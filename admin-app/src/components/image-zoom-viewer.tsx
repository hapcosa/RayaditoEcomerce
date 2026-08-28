/**
 * Visor de imagen a pantalla completa con pinch-to-zoom + arrastre y doble-tap.
 * Se usa dentro de un Modal: los Modal de RN viven en otra jerarquía nativa, por
 * eso el visor trae su propio GestureHandlerRootView (no depende del root layout).
 *
 * Modo recorte: si se pasa `onCrop`, se dibuja un marco (misma proporción que la
 * foto, fijo en pantalla) y un botón "Guardar recorte". El área encuadrada dentro
 * del marco es lo que se recorta del original (ver utils/crop-image).
 */
import { Image } from 'expo-image';
import { useEffect, useRef, useState } from 'react';
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

import type { ViewerTransform } from '@/utils/crop-image';

import { ThemedText } from './themed-text';

const MAX_SCALE = 6;
const DOUBLE_TAP_SCALE = 2.5;

/** Destino del recorte: agregar a galería (no destructivo) o volverlo la foto principal. */
export type CropDest = 'gallery' | 'main';

type Props = {
  visible: boolean;
  uri: string | null;
  onClose: () => void;
  /** Si viene, el visor entra en modo recorte y llama con el encuadre + destino. */
  onCrop?: (t: ViewerTransform, dest: CropDest) => void;
  /** Deshabilita los botones y muestra spinner mientras se procesa el recorte. */
  busy?: boolean;
};

export function ImageZoomViewer({ visible, uri, onClose, onCrop, busy }: Props) {
  const { width, height } = useWindowDimensions();

  const scale = useSharedValue(1);
  const savedScale = useSharedValue(1);
  const tx = useSharedValue(0);
  const ty = useSharedValue(0);
  const savedTx = useSharedValue(0);
  const savedTy = useSharedValue(0);

  // Espejo JS del transform: los worklets de gesto lo sincronizan (runOnJS) al
  // terminar, y los botones lo leen sin tocar ningún `.value` en el hilo JS
  // (evita el warning de Reanimated en strict mode).
  const tf = useRef({ scale: 1, tx: 0, ty: 0 });
  function syncTf(sc: number, x: number, y: number) {
    tf.current = { scale: sc, tx: x, ty: y };
  }

  // Tamaño natural de la imagen, para dibujar el marco de recorte en `contain`.
  const [imgSize, setImgSize] = useState<{ w: number; h: number } | null>(null);
  useEffect(() => {
    if (!uri || !onCrop) {
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
  }, [uri, onCrop]);

  const reset = () => {
    'worklet';
    scale.value = withTiming(1);
    savedScale.value = 1;
    tx.value = withTiming(0);
    ty.value = withTiming(0);
    savedTx.value = 0;
    savedTy.value = 0;
  };

  const pinch = Gesture.Pinch()
    .onUpdate((e) => {
      scale.value = Math.max(1, Math.min(savedScale.value * e.scale, MAX_SCALE));
    })
    .onEnd(() => {
      if (scale.value <= 1) {
        reset();
        runOnJS(syncTf)(1, 0, 0);
      } else {
        savedScale.value = scale.value;
        runOnJS(syncTf)(scale.value, tx.value, ty.value);
      }
    });

  const pan = Gesture.Pan()
    .onUpdate((e) => {
      tx.value = savedTx.value + e.translationX;
      ty.value = savedTy.value + e.translationY;
    })
    .onEnd(() => {
      savedTx.value = tx.value;
      savedTy.value = ty.value;
      runOnJS(syncTf)(scale.value, tx.value, ty.value);
    });

  const doubleTap = Gesture.Tap()
    .numberOfTaps(2)
    .onEnd(() => {
      if (scale.value > 1) {
        reset();
        runOnJS(syncTf)(1, 0, 0);
      } else {
        scale.value = withTiming(DOUBLE_TAP_SCALE);
        savedScale.value = DOUBLE_TAP_SCALE;
        runOnJS(syncTf)(DOUBLE_TAP_SCALE, tx.value, ty.value);
      }
    });

  const gesture = Gesture.Exclusive(doubleTap, Gesture.Simultaneous(pinch, pan));

  const animStyle = useAnimatedStyle(() => ({
    transform: [
      { translateX: tx.value },
      { translateY: ty.value },
      { scale: scale.value },
    ],
  }));

  function handleClose() {
    reset();
    onClose();
  }

  // Emite el recorte leyendo el transform del espejo JS (tf), sin tocar `.value`.
  function emitCrop(dest: CropDest) {
    const { scale: sc, tx: x, ty: y } = tf.current;
    onCrop?.({ scale: sc, tx: x, ty: y, viewportW: width, viewportH: height }, dest);
  }

  // Marco de recorte = rectángulo `contain` de la imagen dentro del viewport.
  let frame: { left: number; top: number; w: number; h: number } | null = null;
  if (onCrop && imgSize) {
    const c = Math.min(width / imgSize.w, height / imgSize.h);
    const dw = imgSize.w * c;
    const dh = imgSize.h * c;
    frame = { left: (width - dw) / 2, top: (height - dh) / 2, w: dw, h: dh };
  }

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={handleClose}>
      <GestureHandlerRootView style={styles.root}>
        <Pressable style={styles.close} onPress={handleClose} hitSlop={16}>
          <ThemedText style={styles.closeText}>✕</ThemedText>
        </Pressable>
        {uri ? (
          <GestureDetector gesture={gesture}>
            <Animated.View style={[styles.center, animStyle]}>
              <Image
                source={{ uri }}
                style={{ width, height }}
                contentFit="contain"
              />
            </Animated.View>
          </GestureDetector>
        ) : null}

        {frame ? (
          <View
            pointerEvents="none"
            style={[
              styles.frame,
              { left: frame.left, top: frame.top, width: frame.w, height: frame.h },
            ]}
          />
        ) : null}

        {onCrop ? (
          <View pointerEvents="box-none" style={styles.bottomBar}>
            <ThemedText style={styles.hint}>
              Ajustá con zoom y arrastre; se recorta lo que quede dentro del marco.
            </ThemedText>
            {busy ? (
              <ActivityIndicator color="#fff" size="large" style={styles.busySpin} />
            ) : (
              <>
                <Pressable
                  style={styles.centerBtn}
                  onPress={() => {
                    reset();
                    tf.current = { scale: 1, tx: 0, ty: 0 };
                  }}
                  hitSlop={8}
                >
                  <ThemedText style={styles.centerBtnText}>Centrar</ThemedText>
                </Pressable>
                <Pressable
                  style={styles.cropBtn}
                  onPress={() => emitCrop('main')}
                  disabled={busy}
                >
                  <ThemedText style={styles.cropBtnText}>Dejar como principal</ThemedText>
                </Pressable>
                <Pressable
                  style={styles.cropBtnAlt}
                  onPress={() => emitCrop('gallery')}
                  disabled={busy}
                >
                  <ThemedText style={styles.cropBtnText}>Guardar en galería</ThemedText>
                </Pressable>
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
    bottom: 40,
    zIndex: 10,
    alignItems: 'center',
    paddingHorizontal: 24,
    gap: 12,
  },
  hint: {
    color: 'rgba(255,255,255,0.85)',
    fontSize: 13,
    textAlign: 'center',
  },
  busySpin: { marginTop: 8 },
  centerBtn: {
    alignSelf: 'center',
    paddingVertical: 10,
    paddingHorizontal: 24,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.6)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerBtnText: { color: '#fff', fontSize: 15, fontWeight: '600' },
  cropBtn: {
    alignSelf: 'stretch',
    paddingVertical: 15,
    paddingHorizontal: 28,
    borderRadius: 28,
    backgroundColor: '#c8763f',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cropBtnAlt: {
    alignSelf: 'stretch',
    paddingVertical: 15,
    paddingHorizontal: 28,
    borderRadius: 28,
    backgroundColor: '#4d6b7a',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cropBtnText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
