/**
 * Recorta una imagen a partir del encuadre del visor (pinch-zoom + pan) tomando
 * los píxeles del ORIGINAL a resolución nativa: nunca amplía, solo recorta una
 * sub-región, así no se pierde nitidez (salvo el reencode JPEG a calidad máxima).
 *
 * El visor aplica el transform `[translateX tx, translateY ty, scale s]` con
 * origen en el centro y la imagen con `contentFit="contain"` dentro de un marco
 * W×H (viewport). Para un punto P (coords del elemento W×H, pre-transform):
 *   pantalla = C + s·(P − C) + (tx, ty),  con C = (W/2, H/2)
 * Invirtiendo, la región visible (esquinas (0,0) y (W,H) en pantalla) mapea a:
 *   P = C + (pantalla − C − (tx, ty)) / s
 * Luego se pasa de coords del elemento (con letterbox del contain) a px del
 * original y se recorta con expo-image-manipulator.
 */
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';
import { Image } from 'react-native';

import type { LocalImage } from '@/api/products';

export type ViewerTransform = {
  scale: number;
  tx: number;
  ty: number;
  viewportW: number;
  viewportH: number;
};

function getSize(uri: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    Image.getSize(uri, (width, height) => resolve({ width, height }), reject);
  });
}

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(v, hi));

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

  const cx = W / 2;
  const cy = H / 2;

  // contain: escala y offsets del letterbox dentro del viewport.
  const c = Math.min(W / iw, H / ih);
  const dw = iw * c;
  const dh = ih * c;
  const offX = (W - dw) / 2;
  const offY = (H - dh) / 2;

  // Marco de recorte = rectángulo de la imagen en `contain` (misma proporción
  // que la foto), fijo en pantalla. Sus esquinas → coords del elemento.
  const frLeft = offX;
  const frTop = offY;
  const frRight = offX + dw;
  const frBottom = offY + dh;
  const pTlX = cx + (frLeft - cx - tx) / s;
  const pTlY = cy + (frTop - cy - ty) / s;
  const pBrX = cx + (frRight - cx - tx) / s;
  const pBrY = cy + (frBottom - cy - ty) / s;

  // Elemento → px del original, recortado a los límites de la imagen.
  const oxTl = clamp((pTlX - offX) / c, 0, iw);
  const oyTl = clamp((pTlY - offY) / c, 0, ih);
  const oxBr = clamp((pBrX - offX) / c, 0, iw);
  const oyBr = clamp((pBrY - offY) / c, 0, ih);

  const originX = Math.round(oxTl);
  const originY = Math.round(oyTl);
  const width = Math.round(oxBr - oxTl);
  const height = Math.round(oyBr - oyTl);

  if (width < 2 || height < 2) return null;

  const context = ImageManipulator.manipulate(uri);
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
