/**
 * Los cuatro números de venta del periodo, cada uno contra el periodo anterior.
 *
 * Se reporta el **neto** y no el bruto: `Order.amount` incluye el envío (ver
 * `payment/views.py`), así que el bruto infla la venta con lo que se lleva
 * Starken.
 */
import { StyleSheet, View } from 'react-native';

import type { StatsPrevious, StatsTotals } from '@/api/stats';
import { StatCard } from '@/components/stat-card';
import { ThemedText } from '@/components/themed-text';
import { Spacing } from '@/constants/theme';
import { formatCLP } from '@/utils/money';

type SalesSummaryProps = {
  days: number;
  totals: StatsTotals;
  previous: StatsPrevious;
};

export function SalesSummary({ days, totals, previous }: SalesSummaryProps) {
  const previousLabel = `${days} días previos`;

  return (
    <View style={styles.block}>
      <ThemedText type="small" themeColor="textSecondary">
        Últimos {days} días
      </ThemedText>
      <View style={styles.grid}>
        <StatCard
          label="Vendido (neto)"
          value={formatCLP(totals.net_clp)}
          current={totals.net_clp}
          previous={previous.net_clp}
          previousLabel={previousLabel}
        />
        <StatCard
          label="Pedidos pagados"
          value={String(totals.orders_paid)}
          current={totals.orders_paid}
          previous={previous.orders_paid}
          previousLabel={previousLabel}
        />
        <StatCard
          label="Piezas vendidas"
          value={String(totals.items_sold)}
          current={totals.items_sold}
          previous={previous.items_sold}
          previousLabel={previousLabel}
        />
        <StatCard
          label="Ticket promedio"
          value={formatCLP(totals.average_order_clp)}
          current={totals.average_order_clp}
          previous={previous.average_order_clp}
          previousLabel={previousLabel}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: Spacing.two },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.two,
  },
});
