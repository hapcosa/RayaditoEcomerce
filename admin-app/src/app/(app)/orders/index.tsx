/** Lista de pedidos (GET /api/admin/orders/) con filtro por estado. */
import { Link, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { listOrders, type Order, type OrderStatus } from '@/api/orders';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import { formatCLP } from '@/utils/money';
import { ORDER_STATUS_COLOR, ORDER_STATUS_LABEL } from '@/utils/order-status';

/** Estados ofrecidos como chips de filtro (más "Todos"). */
const FILTERS: OrderStatus[] = [
  'no procesado',
  'procesado',
  'enviado',
  'cancelado',
  'rechazado',
];

function StatusBadge({ status }: { status: OrderStatus }) {
  return (
    <View style={[styles.badge, { backgroundColor: ORDER_STATUS_COLOR[status] }]}>
      <ThemedText type="small" style={styles.badgeText}>
        {ORDER_STATUS_LABEL[status]}
      </ThemedText>
    </View>
  );
}

function OrderRow({ order }: { order: Order }) {
  const theme = useTheme();
  // `amount` ya incluye el envio (payment/views.py); no volver a sumarlo.
  const total = order.amount ?? 0;
  const count = order.items.reduce((n, it) => n + it.count, 0);
  return (
    <Link href={`/(app)/orders/${order.id}`} asChild>
      <Pressable
        style={StyleSheet.flatten([styles.row, { backgroundColor: theme.backgroundElement }])}
      >
        <View style={styles.rowTop}>
          <ThemedText type="smallBold" numberOfLines={1} style={styles.rowName}>
            #{order.id} · {order.full_name}
          </ThemedText>
          <StatusBadge status={order.status} />
        </View>
        <ThemedText type="small">{formatCLP(total)}</ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          {count} {count === 1 ? 'artículo' : 'artículos'} · {order.city || 'Sin ciudad'}
        </ThemedText>
      </Pressable>
    </Link>
  );
}

export default function OrdersListScreen() {
  const theme = useTheme();
  const [orders, setOrders] = useState<Order[]>([]);
  const [filter, setFilter] = useState<OrderStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (status: OrderStatus | null, isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      setError(null);
      try {
        setOrders(await listOrders(status ?? undefined));
      } catch (e) {
        setError(e instanceof Error ? e.message : 'No se pudieron cargar los pedidos.');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [],
  );

  // Recarga al enfocar (p. ej. tras cambiar el estado de un pedido y volver).
  useFocusEffect(
    useCallback(() => {
      load(filter);
    }, [load, filter]),
  );

  const onFilter = (status: OrderStatus | null) => {
    setFilter(status);
    setLoading(true);
    load(status);
  };

  return (
    <SafeAreaView
      edges={['bottom']}
      style={[styles.safe, { backgroundColor: theme.background }]}
    >
      <View style={styles.filters}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filtersRow}
        >
          <FilterChip label="Todos" active={filter === null} onPress={() => onFilter(null)} />
          {FILTERS.map((s) => (
            <FilterChip
              key={s}
              label={ORDER_STATUS_LABEL[s]}
              active={filter === s}
              onPress={() => onFilter(s)}
            />
          ))}
        </ScrollView>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.accent} />
        </View>
      ) : (
        <FlatList
          data={orders}
          keyExtractor={(o) => String(o.id)}
          renderItem={({ item }) => <OrderRow order={item} />}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => load(filter, true)} />
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <ThemedText type="small" themeColor="textSecondary">
                {error ?? 'No hay pedidos en este filtro.'}
              </ThemedText>
            </View>
          }
          ListHeaderComponent={
            error && orders.length > 0 ? (
              <ThemedText type="small" themeColor="textSecondary" style={styles.err}>
                {error}
              </ThemedText>
            ) : null
          }
        />
      )}
    </SafeAreaView>
  );
}

function FilterChip({
  label,
  active,
  onPress,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
}) {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.chip,
        { backgroundColor: active ? theme.accent : theme.backgroundElement },
      ]}
    >
      <ThemedText
        type="small"
        style={{ color: active ? theme.onAccent : theme.textSecondary }}
      >
        {label}
      </ThemedText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  filters: { paddingVertical: 8 },
  filtersRow: { paddingHorizontal: 16, gap: 8 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  list: { padding: 16, gap: 12, flexGrow: 1 },
  err: { marginBottom: 8 },
  row: {
    padding: 14,
    borderRadius: 12,
    gap: 4,
  },
  rowTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  rowName: { flexShrink: 1 },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: { color: '#ffffff', fontWeight: '700' },
});
