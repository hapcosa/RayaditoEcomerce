/**
 * Velo con spinner que tapa la pantalla mientras sube una foto o se guarda.
 *
 * Con señal inestable una subida puede tardar bastante: sin esto la pantalla
 * parecía congelada y daban ganas de volver a tocar el botón.
 */
import { ActivityIndicator, Modal, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type BusyOverlayProps = {
  visible: boolean;
  /** Qué se está haciendo, ej. "Subiendo foto…". */
  label: string;
};

export function BusyOverlay({ visible, label }: BusyOverlayProps) {
  const theme = useTheme();

  return (
    // `onRequestClose` vacío: el botón atrás de Android no debe cerrar el velo
    // a mitad de una subida.
    <Modal visible={visible} transparent animationType="fade" onRequestClose={() => {}}>
      <View style={styles.backdrop}>
        <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
          <ActivityIndicator size="large" color={theme.accent} />
          <ThemedText type="small">{label}</ThemedText>
          <ThemedText type="small" themeColor="textSecondary" style={styles.hint}>
            Si la señal está lenta puede tardar. No cierres la app.
          </ThemedText>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.45)',
    padding: Spacing.four,
  },
  card: {
    alignItems: 'center',
    gap: Spacing.two,
    paddingVertical: Spacing.four,
    paddingHorizontal: Spacing.four,
    borderRadius: 16,
    maxWidth: 320,
  },
  hint: { textAlign: 'center' },
});
