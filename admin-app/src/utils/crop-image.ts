/**
 * Recorta una imagen a partir del encuadre del visor (rotación + pinch-zoom +
 * pan) tomando los píxeles del ORIGINAL a resolución nativa: nunca amplía, solo
 * recorta una sub-región, así no se pierde nitidez (salvo el reencode JPEG a
 * calidad máxima).
 *
 * El visor dibuja la imagen ya rotada, ajustada con `contain` al viewport W×H, y
 * le aplica el transform `[translateX tx, translateY ty, scale s]` con origen en
 * el centro. Para un punto P (coords del elemento W×H, pre-transform):
 *   pantalla = C + s·(P − C) + (tx, ty),  con C = (W/2, H/2)
 * Invirtiendo, las esquinas del marco de recorte (en pantalla) mapean a:
 *   P = C + (pantalla − C − (tx, ty)) / s
 * Luego se pasa de coords del elemento (con letterbox del contain) a px de la
 * imagen rotada. Por eso acá se rota primero y se recorta después: así el
 * recorte usa el mismo sistema de coordenadas que vio el usuario.
 */
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';
import { Image } from 'react-native';

import type { LocalImage } from '@/api/products';

/** Marco de recorte, en coordenadas de pantalla del visor. */
export type CropFrame = { left: number; top: number; width: number; height: number };

export type ViewerTransform = {
  scale: number;
  tx: number;
  ty: number;
  viewportW: number;
  viewportH: number;
  /** Giro en pasos de 90° en sentido horario. Por defecto 0. */
  rotation?: number;
  /** Si falta, se recorta el rectángulo `contain` completo (proporción original). */
  frame?: CropFrame;
};

function getSize(uri: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    Image.getSize(uri, (width, height) => resolve({ width, height }), reject);
  });
}

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(v, hi));

/** Normaliza el giro a uno de {0, 90, 180, 270}. */
export function normalizeRotation(deg: number): number {
  return ((Math.round(deg / 90) * 90) % 360 + 360) % 360;
}

/**
 * Genera un recorte (LocalImage lista para subir) del área encuadrada.
 * Devuelve `null` si el rectángulo resultante es degenerado.
 */
export async function cropFromViewer(
  uri: string,
  t: ViewerTransform,
): Promise<LocalImage | null> {
  const { width: iw, height: ih } = await getSize(uri);
  const { scale: s, tx, ty, viewportW: W, viewportH: H } = t;
  const rot = normalizeRotation(t.rotation ?? 0);

  // Dimensiones de la imagen YA rotada: en 90/270 se intercambian los lados.
  const rw = rot % 180 === 0 ? iw : ih;
  const rh = rot % 180 === 0 ? ih : iw;

  const cx = W / 2;
  const cy = H / 2;

  // contain: escala y offsets del letterbox dentro del viewport.
  const c = Math.min(W / rw, H / rh);
  const dw = rw * c;
  const dh = rh * c;
  const offX = (W - dw) / 2;
  const offY = (H - dh) / 2;

  // Sin marco explícito, el recorte es el rect `contain` entero (compatibilidad
  // con el comportamiento viejo: misma proporción que la foto).
  const fr: CropFrame = t.frame ?? { left: offX, top: offY, width: dw, height: dh };

  const pTlX = cx + (fr.left - cx - tx) / s;
  const pTlY = cy + (fr.top - cy - ty) / s;
  const pBrX = cx + (fr.left + fr.width - cx - tx) / s;
  const pBrY = cy + (fr.top + fr.height - cy - ty) / s;

  // Elemento → px de la imagen rotada, recortado a sus límites.
  const oxTl = clamp((pTlX - offX) / c, 0, rw);
  const oyTl = clamp((pTlY - offY) / c, 0, rh);
  const oxBr = clamp((pBrX - offX) / c, 0, rw);
  const oyBr = clamp((pBrY - offY) / c, 0, rh);

  const originX = Math.round(oxTl);
  const originY = Math.round(oyTl);
  const width = Math.round(oxBr - oxTl);
  const height = Math.round(oyBr - oyTl);

  if (width < 2 || height < 2) return null;

  const context = ImageManipulator.manipulate(uri);
  if (rot !== 0) context.rotate(rot);
  context.crop({ originX, originY, width, height });
  const ref = await context.renderAsync();
  // compress: 1 = calidad máxima (JPEG visualmente sin pérdida).
  const result = await ref.saveAsync({ compress: 1, format: SaveFormat.JPEG });

  return {
    uri: result.uri,
    name: `recorte-${Date.now()}.jpg`,
    mimeType: 'image/jpeg',
  };
}
