/**
 * Visor de imagen a pantalla completa con pinch-to-zoom + arrastre y doble-tap.
 * Se usa dentro de un Modal: los Modal de RN viven en otra jerarquía nativa, por
 * eso el visor trae su propio GestureHandlerRootView (no depende del root layout).
 */
import { Image } from 'expo-image';
import { Modal, Pressable, StyleSheet, useWindowDimensions } from 'react-native';
import {
  Gesture,
  GestureDetector,
  GestureHandlerRootView,
} from 'react-native-gesture-handler';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

import { ThemedText } from './themed-text';

const MAX_SCALE = 6;
const DOUBLE_TAP_SCALE = 2.5;

type Props = {
  visible: boolean;
  uri: string | null;
  onClose: () => void;
};

export function ImageZoomViewer({ visible, uri, onClose }: Props) {
  const { width, height } = useWindowDimensions();

  const scale = useSharedValue(1);
  const savedScale = useSharedValue(1);
  const tx = useSharedValue(0);
  const ty = useSharedValue(0);
  const savedTx = useSharedValue(0);
  const savedTy = useSharedValue(0);

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
      savedScale.value = scale.value;
      if (scale.value <= 1) reset();
    });

  const pan = Gesture.Pan()
    .onUpdate((e) => {
      tx.value = savedTx.value + e.translationX;
      ty.value = savedTy.value + e.translationY;
    })
    .onEnd(() => {
      savedTx.value = tx.value;
      savedTy.value = ty.value;
    });

  const doubleTap = Gesture.Tap()
    .numberOfTaps(2)
    .onEnd(() => {
      if (scale.value > 1) {
        reset();
      } else {
        scale.value = withTiming(DOUBLE_TAP_SCALE);
        savedScale.value = DOUBLE_TAP_SCALE;
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
});
