/**
 * Estado de despacho del momento. No depende del rango del resumen a
 * propósito: es la foto operativa de ahora, no un histórico.
 *
 * Toda la tarjeta lleva a la lista de pedidos, que es lo que el dueño va a
 * querer hacer apenas vea un número distinto de cero.
 */
import { Link } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import { hoursSince, type StatsPending } from '@/api/stats';
import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

function Figure({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <View style={styles.figure}>
      <ThemedText type="small" themeColor="textSecondary" numberOfLines={1}>
        {label}
      </ThemedText>
      <ThemedText style={[styles.figureValue, color ? { color } : null]}>{value}</ThemedText>
    </View>
  );
}

export function DispatchSummary({ pending }: { pending: StatsPending }) {
  const theme = useTheme();
  const { awaiting_dispatch, due_soon, overdue, oldest_paid_at } = pending;

  return (
    <Link href="/(app)/orders" asChild>
      <Pressable
        style={StyleSheet.flatten([styles.card, { backgroundColor: theme.backgroundElement }])}
      >
        <View style={styles.header}>
          <ThemedText type="default">Por despachar</ThemedText>
          <ThemedText type="linkPrimary">Ver pedidos</ThemedText>
        </View>

        {awaiting_dispatch === 0 ? (
          <ThemedText type="small" themeColor="textSecondary">
            No queda nada pendiente de despacho.
          </ThemedText>
        ) : (
          <>
            <View style={styles.figures}>
              <Figure label="Pendientes" value={awaiting_dispatch} />
              <Figure
                label="Por vencer"
                value={due_soon}
                color={due_soon > 0 ? theme.accent : undefined}
              />
              <Figure
                label="Vencidas"
                value={overdue}
                color={overdue > 0 ? theme.danger : undefined}
              />
            </View>

            {overdue > 0 && (
              // El estado nunca se comunica solo con color: también va la palabra.
              <ThemedText type="smallBold" style={{ color: theme.danger }}>
                {overdue} {overdue === 1 ? 'venta pasó' : 'ventas pasaron'} el plazo de despacho.
              </ThemedText>
            )}

            {oldest_paid_at && (
              <ThemedText type="small" themeColor="textSecondary">
                La más antigua sin despachar se pagó hace {hoursSince(oldest_paid_at)} h.
              </ThemedText>
            )}
          </>
        )}
      </Pressable>
    </Link>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    padding: Spacing.four,
    gap: Spacing.two,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    gap: Spacing.two,
  },
  figures: {
    flexDirection: 'row',
    gap: Spacing.three,
  },
  figure: { flex: 1, gap: Spacing.half },
  figureValue: {
    fontSize: 24,
    lineHeight: 30,
    fontWeight: '600',
  },
});
