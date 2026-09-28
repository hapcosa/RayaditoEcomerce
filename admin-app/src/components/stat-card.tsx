/**
 * Tarjeta numérica del home con su variación contra el periodo anterior.
 *
 * El signo se dice con texto ("▲ +12 %" / "▼ −8 %") además del color: el color
 * por sí solo no comunica nada a quien no lo distingue.
 */
import { StyleSheet, View } from 'react-native';

import { deltaPercent } from '@/api/stats';
import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

type StatCardProps = {
  /** Qué mide la tarjeta. */
  label: string;
  /** Valor ya formateado (CLP o unidades). */
  value: string;
  /** Valores crudos del periodo actual y del anterior, para la variación. */
  current: number;
  previous: number;
  /** Cómo nombrar el periodo anterior en el texto de referencia. */
  previousLabel: string;
};

export function StatCard({ label, value, current, previous, previousLabel }: StatCardProps) {
  const theme = useTheme();
  const delta = deltaPercent(current, previous);

  // La línea de la variación no lleva `numberOfLines`: a 390 px ocupa dos
  // renglones, y truncarla se comería el "vs. …" que le da sentido al número.

  return (
    <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
      <ThemedText type="small" themeColor="textSecondary" numberOfLines={1}>
        {label}
      </ThemedText>
      <ThemedText style={styles.value} numberOfLines={1} adjustsFontSizeToFit>
        {value}
      </ThemedText>
      {delta === null ? (
        <ThemedText type="small" themeColor="textSecondary">
          sin datos en {previousLabel}
        </ThemedText>
      ) : (
        <ThemedText type="small" themeColor="textSecondary">
          <ThemedText
            type="smallBold"
            style={{ color: delta > 0 ? theme.accent : theme.textSecondary }}
          >
            {delta > 0 ? '▲ +' : delta < 0 ? '▼ −' : ''}
            {Math.abs(delta)} %
          </ThemedText>{' '}
          vs. {previousLabel}
        </ThemedText>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexGrow: 1,
    flexBasis: '45%',
    borderRadius: 12,
    padding: Spacing.three,
    gap: Spacing.one,
  },
  value: {
    fontSize: 24,
    lineHeight: 30,
    fontWeight: '600',
  },
});
