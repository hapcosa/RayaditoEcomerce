/**
 * Visor de imagen a pantalla completa con pinch-to-zoom + arrastre y doble-tap.
 * Se usa dentro de un Modal: los Modal de RN viven en otra jerarquía nativa, por
 * eso el visor trae su propio GestureHandlerRootView (no depende del root layout).
 *
 * Modo recorte (si se pasa `onCrop`): marco FIJO en pantalla con proporción
 * elegible (original / 1:1 / 4:5 / 3:4), giro en pasos de 90° y la foto que se
 * mueve por debajo. El zoom mínimo es el que hace que la foto tape el marco
 * entero y el arrastre está acotado, así nunca queda un borde vacío. Lo que
 * queda dentro del marco es exactamente lo que se recorta (ver utils/crop-image).
 */
import { Image } from 'expo-image';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Image as RNImage,
  Modal,
  Pressable,
  StyleSheet,
  useWindowDimensions,
  View,
} from 'react-native';
import {
  Gesture,
  GestureDetector,
  GestureHandlerRootView,
} from 'react-native-gesture-handler';
import Animated, {
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

import type { CropFrame, ViewerTransform } from '@/utils/crop-image';

import { Brand } from '@/constants/theme';

import { ThemedText } from './themed-text';

/** Cuánto se puede ampliar por sobre el zoom mínimo (el que tapa el marco). */
const MAX_ZOOM_FACTOR = 6;
const DOUBLE_TAP_FACTOR = 2.5;

/** Franjas reservadas arriba (botón cerrar) y abajo (controles). */
const TOP_SAFE = 104;
const BOTTOM_SAFE = 246;
const FRAME_PAD = 16;

/** Destino del recorte: agregar a galería (no destructivo) o volverlo la foto principal. */
export type CropDest = 'gallery' | 'main';

/** `ratio` null = respetar la proporción de la foto tal como viene. */
const ASPECTS: { key: string; label: string; ratio: number | null }[] = [
  { key: 'orig', label: 'Original', ratio: null },
  { key: '1:1', label: '1:1', ratio: 1 },
  { key: '4:5', label: '4:5', ratio: 4 / 5 },
  { key: '3:4', label: '3:4', ratio: 3 / 4 },
];

type Props = {
  visible: boolean;
  uri: string | null;
  onClose: () => void;
  /** Si viene, el visor entra en modo recorte y llama con el encuadre + destino. */
  onCrop?: (t: ViewerTransform, dest: CropDest) => void;
  /**
   * Destinos que se ofrecen. Al ALTA de un producto todavia no hay galeria a la
   * que agregar, asi que esa pantalla pasa solo `['main']`.
   */
  dests?: CropDest[];
  /** Deshabilita los botones y muestra spinner mientras se procesa el recorte. */
  busy?: boolean;
};

export function ImageZoomViewer({
  visible,
  uri,
  onClose,
  onCrop,
  busy,
  dests = ['main', 'gallery'],
}: Props) {
  const { width, height } = useWindowDimensions();
  const cropMode = !!onCrop;

  const scale = useSharedValue(1);
  const savedScale = useSharedValue(1);
  const tx = useSharedValue(0);
  const ty = useSharedValue(0);
  const savedTx = useSharedValue(0);
  const savedTy = useSharedValue(0);

  // Geometría que necesitan los worklets de gesto (no pueden leer estado de React).
  const dwS = useSharedValue(0);
  const dhS = useSharedValue(0);
  const frLeft = useSharedValue(0);
  const frTop = useSharedValue(0);
  const frW = useSharedValue(0);
  const frH = useSharedValue(0);
  const minScale = useSharedValue(1);
  const clampOn = useSharedValue(false);

  // Espejo JS del transform: los worklets lo sincronizan (runOnJS) al terminar y
  // los botones lo leen sin tocar ningún `.value` en el hilo JS (evita el
  // warning de Reanimated en strict mode).
  const tf = useRef({ scale: 1, tx: 0, ty: 0 });
  const syncTf = useCallback((sc: number, x: number, y: number) => {
    tf.current = { scale: sc, tx: x, ty: y };
  }, []);

  const [aspectKey, setAspectKey] = useState('orig');
  const [rot, setRot] = useState(0);

  // Tamaño natural de la imagen, para calcular el encuadre.
  const [imgSize, setImgSize] = useState<{ w: number; h: number } | null>(null);
  useEffect(() => {
    if (!uri || !cropMode) {
      setImgSize(null);
      return;
    }
    let alive = true;
    RNImage.getSize(
      uri,
      (w, h) => alive && setImgSize({ w, h }),
      () => alive && setImgSize(null),
    );
    return () => {
      alive = false;
    };
  }, [uri, cropMode]);

  // Foto nueva ⇒ encuadre de cero.
  useEffect(() => {
    setAspectKey('orig');
    setRot(0);
  }, [uri]);

  /**
   * Rect de la imagen (ya rotada) en `contain` dentro del viewport, marco de
   * recorte y zoom mínimo que lo tapa por completo.
   */
  const layout = useMemo(() => {
    if (!cropMode || !imgSize) return null;
    const swap = rot % 180 !== 0;
    const rw = swap ? imgSize.h : imgSize.w;
    const rh = swap ? imgSize.w : imgSize.h;
    const c = Math.min(width / rw, height / rh);
    const dw = rw * c;
    const dh = rh * c;

    const ratio = ASPECTS.find((a) => a.key === aspectKey)?.ratio ?? rw / rh;
    const availW = width - FRAME_PAD * 2;
    const availH = Math.max(160, height - TOP_SAFE - BOTTOM_SAFE);
    let fw = availW;
    let fh = fw / ratio;
    if (fh > availH) {
      fh = availH;
      fw = fh * ratio;
    }
    const frame: CropFrame = {
      left: (width - fw) / 2,
      top: TOP_SAFE + (availH - fh) / 2,
      width: fw,
      height: fh,
    };
    return {
      dw,
      dh,
      frame,
      minScale: Math.max(fw / dw, fh / dh),
      // El marco no está centrado en el viewport: este es el desplazamiento que
      // deja la foto centrada DENTRO del marco.
      baseTx: frame.left + fw / 2 - width / 2,
      baseTy: frame.top + fh / 2 - height / 2,
      // Tamaño del <Image> sin rotar dentro del contenedor ya rotado.
      imgW: swap ? dh : dw,
      imgH: swap ? dw : dh,
    };
  }, [cropMode, imgSize, rot, aspectKey, width, height]);

  // Al cambiar proporción, giro o foto: reencuadrar al mínimo y centrar.
  useEffect(() => {
    if (!layout) {
      clampOn.value = false;
      minScale.value = 1;
      scale.value = 1;
      savedScale.value = 1;
      tx.value = 0;
      ty.value = 0;
      savedTx.value = 0;
      savedTy.value = 0;
      syncTf(1, 0, 0);
      return;
    }
    dwS.value = layout.dw;
    dhS.value = layout.dh;
    frLeft.value = layout.frame.left;
    frTop.value = layout.frame.top;
    frW.value = layout.frame.width;
    frH.value = layout.frame.height;
    minScale.value = layout.minScale;
    clampOn.value = true;

    scale.value = withTiming(layout.minScale);
    savedScale.value = layout.minScale;
    tx.value = withTiming(layout.baseTx);
    ty.value = withTiming(layout.baseTy);
    savedTx.value = layout.baseTx;
    savedTy.value = layout.baseTy;
    syncTf(layout.minScale, layout.baseTx, layout.baseTy);
  }, [
    layout,
    clampOn,
    dwS,
    dhS,
    frLeft,
    frTop,
    frW,
    frH,
    minScale,
    scale,
    savedScale,
    tx,
    ty,
    savedTx,
    savedTy,
    syncTf,
  ]);

  /** Acota el arrastre para que la foto siga tapando el marco entero. */
  const clampX = (x: number, sc: number) => {
    'worklet';
    if (!clampOn.value) return x;
    const half = (dwS.value * sc) / 2;
    const lo = frLeft.value + frW.value - width / 2 - half;
    const hi = frLeft.value - width / 2 + half;
    return Math.max(lo, Math.min(x, hi));
  };
  const clampY = (y: number, sc: number) => {
    'worklet';
    if (!clampOn.value) return y;
    const half = (dhS.value * sc) / 2;
    const lo = frTop.value + frH.value - height / 2 - half;
    const hi = frTop.value - height / 2 + half;
    return Math.max(lo, Math.min(y, hi));
  };

  const pinch = Gesture.Pinch()
    .onUpdate((e) => {
      const lo = minScale.value;
      const next = Math.max(lo, Math.min(savedScale.value * e.scale, lo * MAX_ZOOM_FACTOR));
      scale.value = next;
      tx.value = clampX(tx.value, next);
      ty.value = clampY(ty.value, next);
    })
    .onEnd(() => {
      savedScale.value = scale.value;
      savedTx.value = tx.value;
      savedTy.value = ty.value;
      runOnJS(syncTf)(scale.value, tx.value, ty.value);
    });

  const pan = Gesture.Pan()
    .onUpdate((e) => {
      tx.value = clampX(savedTx.value + e.translationX, scale.value);
      ty.value = clampY(savedTy.value + e.translationY, scale.value);
    })
    .onEnd(() => {
      savedTx.value = tx.value;
      savedTy.value = ty.value;
      runOnJS(syncTf)(scale.value, tx.value, ty.value);
    });

  const doubleTap = Gesture.Tap()
    .numberOfTaps(2)
    .onEnd(() => {
      const lo = minScale.value;
      const next = scale.value > lo * 1.01 ? lo : lo * DOUBLE_TAP_FACTOR;
      scale.value = withTiming(next);
      savedScale.value = next;
      const nx = clampX(tx.value, next);
      const ny = clampY(ty.value, next);
      tx.value = withTiming(nx);
      ty.value = withTiming(ny);
      savedTx.value = nx;
      savedTy.value = ny;
      runOnJS(syncTf)(next, nx, ny);
    });

  const gesture = Gesture.Exclusive(doubleTap, Gesture.Simultaneous(pinch, pan));

  const animStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: tx.value },
      { translateY: ty.value },
      { scale: scale.value },
    ],
  }));

  /** Vuelve al encuadre inicial (zoom mínimo, foto centrada en el marco). */
  function recenter() {
    const sc = layout ? layout.minScale : 1;
    const x = layout ? layout.baseTx : 0;
    const y = layout ? layout.baseTy : 0;
    scale.value = withTiming(sc);
    savedScale.value = sc;
    tx.value = withTiming(x);
    ty.value = withTiming(y);
    savedTx.value = x;
    savedTy.value = y;
    tf.current = { scale: sc, tx: x, ty: y };
  }

  function handleClose() {
    recenter();
    onClose();
  }

  // Emite el recorte leyendo el transform del espejo JS (tf), sin tocar `.value`.
  function emitCrop(dest: CropDest) {
    const { scale: sc, tx: x, ty: y } = tf.current;
    onCrop?.(
      {
        scale: sc,
        tx: x,
        ty: y,
        viewportW: width,
        viewportH: height,
        rotation: rot,
        frame: layout?.frame,
      },
      dest,
    );
  }

  const frame = layout?.frame ?? null;

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={handleClose}>
      <GestureHandlerRootView style={styles.root}>
        <Pressable style={styles.close} onPress={handleClose} hitSlop={16}>
          <ThemedText style={styles.closeText}>✕</ThemedText>
        </Pressable>
        {uri ? (
          <GestureDetector gesture={gesture}>
            <Animated.View style={[styles.center, animStyle]}>
              {layout ? (
                <View style={{ width: layout.dw, height: layout.dh }}>
                  <Image
                    source={{ uri }}
                    style={{
                      position: 'absolute',
                      left: (layout.dw - layout.imgW) / 2,
                      top: (layout.dh - layout.imgH) / 2,
                      width: layout.imgW,
                      height: layout.imgH,
                      transform: [{ rotate: `${rot}deg` }],
                    }}
                    contentFit="fill"
                  />
                </View>
              ) : (
                <Image source={{ uri }} style={{ width, height }} contentFit="contain" />
              )}
            </Animated.View>
          </GestureDetector>
        ) : null}

        {frame ? (
          <>
            {/* Velo fuera del marco: deja claro qué queda adentro. */}
            <View pointerEvents="none" style={[styles.veil, { height: frame.top }]} />
            <View
              pointerEvents="none"
              style={[styles.veil, { top: frame.top + frame.height, bottom: 0 }]}
            />
            <View
              pointerEvents="none"
              style={[
                styles.veil,
                { top: frame.top, height: frame.height, width: frame.left },
              ]}
            />
            <View
              pointerEvents="none"
              style={[
                styles.veil,
                {
                  top: frame.top,
                  height: frame.height,
                  left: frame.left + frame.width,
                  right: 0,
                },
              ]}
            />
            <View
              pointerEvents="none"
              style={[
                styles.frame,
                {
                  left: frame.left,
                  top: frame.top,
                  width: frame.width,
                  height: frame.height,
                },
              ]}
            />
          </>
        ) : null}

        {onCrop ? (
          <View pointerEvents="box-none" style={styles.bottomBar}>
            {busy ? (
              <ActivityIndicator color="#fff" size="large" style={styles.busySpin} />
            ) : (
              <>
                <View style={styles.toolRow}>
                  {ASPECTS.map((a) => (
                    <Pressable
                      key={a.key}
                      style={[styles.chip, aspectKey === a.key && styles.chipOn]}
                      onPress={() => setAspectKey(a.key)}
                      hitSlop={6}
                    >
                      <ThemedText style={styles.chipText}>{a.label}</ThemedText>
                    </Pressable>
                  ))}
                </View>
                <View style={styles.toolRow}>
                  <Pressable
                    style={styles.chip}
                    onPress={() => setRot((r) => (r + 90) % 360)}
                    hitSlop={6}
                    accessibilityLabel="Girar 90 grados"
                  >
                    <ThemedText style={styles.chipText}>↻ Girar</ThemedText>
                  </Pressable>
                  <Pressable style={styles.chip} onPress={recenter} hitSlop={6}>
                    <ThemedText style={styles.chipText}>Centrar</ThemedText>
                  </Pressable>
                </View>
                {dests.includes('main') && (
                  <Pressable
                    style={styles.cropBtn}
                    onPress={() => emitCrop('main')}
                    disabled={busy}
                  >
                    {/* Sin galería no hay con qué contrastar: el rótulo largo sobra. */}
                    <ThemedText style={styles.cropBtnText}>
                      {dests.length === 1 ? 'Usar este encuadre' : 'Dejar como principal'}
                    </ThemedText>
                  </Pressable>
                )}
                {dests.includes('gallery') && (
                  <Pressable
                    style={styles.cropBtnAlt}
                    onPress={() => emitCrop('gallery')}
                    disabled={busy}
                  >
                    <ThemedText style={styles.cropBtnText}>Guardar en galería</ThemedText>
                  </Pressable>
                )}
              </>
            )}
          </View>
        ) : null}
      </GestureHandlerRootView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: 'rgba(0,0,0,0.94)' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  close: {
    position: 'absolute',
    top: 48,
    right: 20,
    zIndex: 10,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.6)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeText: { color: '#fff', fontSize: 20, lineHeight: 24 },
  veil: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    backgroundColor: 'rgba(0,0,0,0.55)',
    zIndex: 4,
  },
  frame: {
    position: 'absolute',
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.9)',
    zIndex: 5,
  },
  bottomBar: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 32,
    zIndex: 10,
    alignItems: 'center',
    paddingHorizontal: 20,
    gap: 10,
  },
  busySpin: { marginTop: 8 },
  toolRow: { flexDirection: 'row', gap: 8, justifyContent: 'center' },
  chip: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.45)',
  },
  chipOn: {
    borderColor: Brand.logoNaranjo,
    backgroundColor: 'rgba(218,95,21,0.25)',
  },
  chipText: { color: '#fff', fontSize: 14, fontWeight: '600' },
  cropBtn: {
    alignSelf: 'stretch',
    paddingVertical: 15,
    paddingHorizontal: 28,
    borderRadius: 28,
    backgroundColor: Brand.logoNaranjo,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cropBtnAlt: {
    alignSelf: 'stretch',
    paddingVertical: 15,
    paddingHorizontal: 28,
    borderRadius: 28,
    backgroundColor: Brand.agata500,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cropBtnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
