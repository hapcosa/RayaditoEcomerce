/** Lista de solicitudes de retracto (GET /api/admin/withdrawals/). */
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

import { listWithdrawals, type Withdrawal, type WithdrawalFilter } from '@/api/withdrawals';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import {
  WITHDRAWAL_STATUS_COLOR,
  WITHDRAWAL_STATUS_LABEL,
} from '@/utils/withdrawal-status';

/** Por defecto se abren las pendientes: son las que piden una acción. */
const FILTERS: { value: WithdrawalFilter | null; label: string }[] = [
  { value: 'open', label: 'Pendientes' },
  { value: null, label: 'Todas' },
  { value: 'refunded', label: WITHDRAWAL_STATUS_LABEL.refunded },
  { value: 'rejected', label: WITHDRAWAL_STATUS_LABEL.rejected },
];

function WithdrawalRow({ item }: { item: Withdrawal }) {
  const theme = useTheme();
  return (
    <Link href={`/(app)/withdrawals/${item.id}`} asChild>
      <Pressable
        style={StyleSheet.flatten([styles.row, { backgroundColor: theme.backgroundElement }])}
      >
        <View style={styles.rowTop}>
          <ThemedText type="smallBold" numberOfLines={1} style={styles.rowName}>
            {item.code} · {item.order.full_name || item.email}
          </ThemedText>
          <View style={[styles.badge, { backgroundColor: WITHDRAWAL_STATUS_COLOR[item.status] }]}>
            <ThemedText type="small" style={styles.badgeText}>
              {WITHDRAWAL_STATUS_LABEL[item.status]}
            </ThemedText>
          </View>
        </View>
        <ThemedText type="small" themeColor="textSecondary">
          Pedido #{item.order.id} · pedida el{' '}
          {new Date(item.created_at).toLocaleDateString('es-CL')}
        </ThemedText>
      </Pressable>
    </Link>
  );
}

export default function WithdrawalsListScreen() {
  const theme = useTheme();
  const [items, setItems] = useState<Withdrawal[]>([]);
  const [filter, setFilter] = useState<WithdrawalFilter | null>('open');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (f: WithdrawalFilter | null, isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    setError(null);
    try {
      setItems(await listWithdrawals(f ?? undefined));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudieron cargar las solicitudes.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Recarga al volver del detalle, donde pudo cambiar el estado.
  useFocusEffect(
    useCallback(() => {
      load(filter);
    }, [load, filter]),
  );

  const onFilter = (f: WithdrawalFilter | null) => {
    setFilter(f);
    setLoading(true);
    load(f);
  };

  return (
    <SafeAreaView edges={['bottom']} style={[styles.safe, { backgroundColor: theme.background }]}>
      <View style={styles.filters}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filtersRow}
        >
          {FILTERS.map((f) => {
            const active = filter === f.value;
            return (
              <Pressable
                key={f.label}
                onPress={() => onFilter(f.value)}
                style={[
                  styles.chip,
                  { backgroundColor: active ? theme.accent : theme.backgroundElement },
                ]}
              >
                <ThemedText
                  type="small"
                  style={{ color: active ? theme.onAccent : theme.textSecondary }}
                >
                  {f.label}
                </ThemedText>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.accent} />
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(w) => String(w.id)}
          renderItem={({ item }) => <WithdrawalRow item={item} />}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => load(filter, true)} />
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <ThemedText type="small" themeColor="textSecondary">
                {error ?? 'No hay solicitudes en este filtro.'}
              </ThemedText>
            </View>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  filters: { paddingVertical: 8 },
  filtersRow: { paddingHorizontal: 16, gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20 },
  list: { padding: 16, gap: 12, flexGrow: 1 },
  row: { padding: 14, borderRadius: 12, gap: 4 },
  rowTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  rowName: { flexShrink: 1 },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  badgeText: { color: '#ffffff', fontWeight: '700' },
});
