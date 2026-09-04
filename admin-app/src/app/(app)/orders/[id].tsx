/**
 * Detalle de un pedido + cambio de estado.
 * Los botones de estado se generan desde `allowed_transitions` que expone el
 * backend (la máquina de estados vive allá, la app solo la refleja).
 */
import { useLocalSearchParams, useNavigation } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  changeOrderStatus,
  getOrder,
  type Order,
  type OrderStatus,
} from '@/api/orders';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import { formatCLP } from '@/utils/money';
import { ORDER_STATUS_COLOR, ORDER_STATUS_LABEL } from '@/utils/order-status';

function Field({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.field}>
      <ThemedText type="small" themeColor="textSecondary">
        {label}
      </ThemedText>
      <ThemedText type="small">{value || '—'}</ThemedText>
    </View>
  );
}

export default function OrderDetailScreen() {
  const theme = useTheme();
  const navigation = useNavigation();
  const { id } = useLocalSearchParams<{ id: string }>();
  const orderId = Number(id);

  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deliveryNumber, setDeliveryNumber] = useState('');
  const [submitting, setSubmitting] = useState<OrderStatus | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setOrder(await getOrder(orderId));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar el pedido.');
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    load();
  }, [load]);

  // Título del header con el número de pedido.
  useEffect(() => {
    navigation.setOptions({ title: order ? `Pedido #${order.id}` : 'Pedido' });
  }, [navigation, order]);

  const handleChange = async (status: OrderStatus) => {
    setActionError(null);
    if (status === 'enviado' && !deliveryNumber.trim()) {
      setActionError('Ingresá el número de seguimiento para marcar como enviado.');
      return;
    }
    setSubmitting(status);
    try {
      const updated = await changeOrderStatus(
        orderId,
        status,
        status === 'enviado' ? deliveryNumber.trim() : undefined,
      );
      setOrder(updated);
      setDeliveryNumber('');
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'No se pudo cambiar el estado.');
    } finally {
      setSubmitting(null);
    }
  };

  if (loading) {
    return (
      <SafeAreaView
        edges={['bottom']}
        style={[styles.safe, styles.center, { backgroundColor: theme.background }]}
      >
        <ActivityIndicator size="large" color={theme.accent} />
      </SafeAreaView>
    );
  }

  if (!order) {
    return (
      <SafeAreaView
        edges={['bottom']}
        style={[styles.safe, styles.center, { backgroundColor: theme.background }]}
      >
        <ThemedText type="small" themeColor="textSecondary">
          {error ?? 'Pedido no encontrado.'}
        </ThemedText>
      </SafeAreaView>
    );
  }

  // `amount` ya viene con el envio incluido (payment/views.py), asi que el
  // total es `amount` y el subtotal de articulos es `amount - shipping_price`.
  const total = order.amount ?? 0;
  const subtotal = total - order.shipping_price;
  const canShip = order.allowed_transitions.includes('enviado');
  // "Enviado" es la accion habitual: va primera, y los estados que cierran el
  // pedido (cancelado/rechazado) quedan abajo para no tocarlos por error.
  const transitions = [...order.allowed_transitions].sort(
    (x, y) => Number(y === 'enviado') - Number(x === 'enviado'),
  );

  return (
    <SafeAreaView
      edges={['bottom']}
      style={[styles.safe, { backgroundColor: theme.background }]}
    >
      {/* `automaticallyAdjustKeyboardInsets`: sin esto el teclado tapa el campo
          de Nº de seguimiento y no hay forma de ver lo que se escribe. */}
      <ScrollView
        contentContainerStyle={styles.content}
        automaticallyAdjustKeyboardInsets
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.statusHead}>
          <View style={[styles.badge, { backgroundColor: ORDER_STATUS_COLOR[order.status] }]}>
            <ThemedText type="small" style={styles.badgeText}>
              {ORDER_STATUS_LABEL[order.status]}
            </ThemedText>
          </View>
          <ThemedText type="small" themeColor="textSecondary">
            {new Date(order.date_issued).toLocaleDateString('es-CL')}
          </ThemedText>
        </View>

        {/* Artículos */}
        <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
          <ThemedText type="smallBold">Artículos</ThemedText>
          {order.items.map((it) => (
            <View key={it.id} style={styles.itemRow}>
              <ThemedText type="small" style={styles.itemName} numberOfLines={2}>
                {it.count}× {it.name}
              </ThemedText>
              <ThemedText type="small">{formatCLP(it.price * it.count)}</ThemedText>
            </View>
          ))}
          <View style={[styles.itemRow, styles.totalRow, { borderTopColor: theme.backgroundSelected }]}>
            <ThemedText type="small" themeColor="textSecondary">
              Subtotal
            </ThemedText>
            <ThemedText type="small" themeColor="textSecondary">
              {formatCLP(subtotal)}
            </ThemedText>
          </View>
          <View style={styles.itemRow}>
            <ThemedText type="small" themeColor="textSecondary">
              Envío
            </ThemedText>
            <ThemedText type="small" themeColor="textSecondary">
              {formatCLP(order.shipping_price)}
            </ThemedText>
          </View>
          <View style={styles.itemRow}>
            <ThemedText type="smallBold">Total</ThemedText>
            <ThemedText type="smallBold">{formatCLP(total)}</ThemedText>
          </View>
        </View>

        {/* Cliente y envío */}
        <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
          <ThemedText type="smallBold">Cliente</ThemedText>
          <Field label="Nombre" value={order.full_name} />
          <Field label="Email" value={order.email ?? ''} />
          <Field label="Teléfono" value={order.telephone_number} />
          <Field
            label="Dirección"
            value={[order.address_line_1, order.city, order.region, order.postal_zip_code]
              .filter(Boolean)
              .join(', ')}
          />
          {order.deliveryNumber ? (
            <Field label="Nº seguimiento" value={order.deliveryNumber} />
          ) : null}
        </View>

        {/* Cambio de estado */}
        <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
          <ThemedText type="smallBold">Cambiar estado</ThemedText>
          {order.allowed_transitions.length === 0 ? (
            <ThemedText type="small" themeColor="textSecondary">
              Este pedido está en un estado final. No admite más cambios.
            </ThemedText>
          ) : (
            <>
              {canShip ? (
                <TextInput
                  value={deliveryNumber}
                  onChangeText={setDeliveryNumber}
                  placeholder="Nº de seguimiento (para enviar)"
                  placeholderTextColor={theme.textSecondary}
                  style={[
                    styles.input,
                    { color: theme.text, borderColor: theme.backgroundSelected },
                  ]}
                  autoCapitalize="characters"
                />
              ) : null}
              <View style={styles.actions}>
                {transitions.map((status) => (
                  <Pressable
                    key={status}
                    onPress={() => handleChange(status)}
                    disabled={submitting !== null}
                    style={[
                      styles.actionBtn,
                      { backgroundColor: ORDER_STATUS_COLOR[status] },
                      submitting !== null && submitting !== status && styles.dim,
                    ]}
                  >
                    {submitting === status ? (
                      <ActivityIndicator color="#ffffff" />
                    ) : (
                      <ThemedText type="smallBold" style={styles.actionText}>
                        {ORDER_STATUS_LABEL[status]}
                      </ThemedText>
                    )}
                  </Pressable>
                ))}
              </View>
            </>
          )}
          {actionError ? (
            <ThemedText type="small" themeColor="textSecondary" style={styles.actionError}>
              {actionError}
            </ThemedText>
          ) : null}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { alignItems: 'center', justifyContent: 'center' },
  content: { padding: 16, gap: 16 },
  statusHead: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  badge: { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 12 },
  badgeText: { color: '#ffffff', fontWeight: '700' },
  card: { borderRadius: 12, padding: 16, gap: 10 },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  itemName: { flexShrink: 1 },
  totalRow: { borderTopWidth: StyleSheet.hairlineWidth, paddingTop: 10, marginTop: 2 },
  field: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
  },
  actions: { gap: 8 },
  actionBtn: {
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  actionText: { color: '#ffffff' },
  dim: { opacity: 0.4 },
  actionError: { marginTop: 2 },
});
