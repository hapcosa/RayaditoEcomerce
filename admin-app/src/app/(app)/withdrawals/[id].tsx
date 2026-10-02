/**
 * Detalle de una solicitud de retracto + cambio de estado.
 *
 * La tienda no registra cuándo llegó el paquete, así que la app muestra los
 * días desde el pago y desde el despacho para que la dueña evalúe el plazo
 * legal (10 días desde la recepción; 90 si no hubo confirmación escrita).
 */
import { Link, useLocalSearchParams, useNavigation } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  changeWithdrawalStatus,
  getWithdrawal,
  type Withdrawal,
  type WithdrawalStatus,
} from '@/api/withdrawals';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import { formatCLP } from '@/utils/money';
import {
  WITHDRAWAL_STATUS_COLOR,
  WITHDRAWAL_STATUS_LABEL,
  daysSince,
} from '@/utils/withdrawal-status';

/** Texto del botón: la acción, no el estado al que se llega. */
const ACTION_LABEL: Record<WithdrawalStatus, string> = {
  received: 'Recibida',
  accepted: 'Aceptar',
  refunded: 'Marcar como reembolsada',
  rejected: 'Rechazar',
};

function Field({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.field}>
      <ThemedText type="small" themeColor="textSecondary">
        {label}
      </ThemedText>
      <ThemedText type="small" style={styles.fieldValue}>
        {value || '—'}
      </ThemedText>
    </View>
  );
}

function dateWithDays(iso: string | null): string {
  if (!iso) return '';
  const days = daysSince(iso);
  return `${new Date(iso).toLocaleDateString('es-CL')} (hace ${days} ${days === 1 ? 'día' : 'días'})`;
}

export default function WithdrawalDetailScreen() {
  const theme = useTheme();
  const navigation = useNavigation();
  const { id } = useLocalSearchParams<{ id: string }>();
  const withdrawalId = Number(id);

  const [item, setItem] = useState<Withdrawal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState<WithdrawalStatus | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setItem(await getWithdrawal(withdrawalId));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar la solicitud.');
    } finally {
      setLoading(false);
    }
  }, [withdrawalId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    navigation.setOptions({ title: item ? item.code : 'Retracto' });
  }, [navigation, item]);

  const submit = async (status: WithdrawalStatus) => {
    setSubmitting(status);
    try {
      setItem(await changeWithdrawalStatus(withdrawalId, status, note.trim() || undefined));
      setNote('');
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'No se pudo cambiar el estado.');
    } finally {
      setSubmitting(null);
    }
  };

  const handleChange = (status: WithdrawalStatus) => {
    setActionError(null);
    if (status === 'rejected' && !note.trim() && !item?.staff_note) {
      setActionError('Para rechazar, escribe el motivo en la nota (queda como respaldo).');
      return;
    }
    // Rechazar y reembolsar cierran la solicitud: se confirma antes.
    if (status === 'rejected' || status === 'refunded') {
      Alert.alert(
        status === 'rejected' ? '¿Rechazar la solicitud?' : '¿Ya hiciste el reembolso?',
        status === 'rejected'
          ? 'La solicitud queda cerrada. Avísale al cliente el motivo.'
          : 'Márcala solo después de devolver el dinero en MercadoPago.',
        [
          { text: 'Cancelar', style: 'cancel' },
          { text: ACTION_LABEL[status], onPress: () => submit(status) },
        ],
      );
      return;
    }
    submit(status);
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

  if (!item) {
    return (
      <SafeAreaView
        edges={['bottom']}
        style={[styles.safe, styles.center, { backgroundColor: theme.background }]}
      >
        <ThemedText type="small" themeColor="textSecondary">
          {error ?? 'Solicitud no encontrada.'}
        </ThemedText>
      </SafeAreaView>
    );
  }

  const { order } = item;
  // `amount` ya incluye el envío; el valor de los productos es el resto.
  const productos = (order.amount ?? 0) - order.shipping_price;

  return (
    <SafeAreaView edges={['bottom']} style={[styles.safe, { backgroundColor: theme.background }]}>
      <ScrollView
        contentContainerStyle={styles.content}
        automaticallyAdjustKeyboardInsets
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.statusHead}>
          <View style={[styles.badge, { backgroundColor: WITHDRAWAL_STATUS_COLOR[item.status] }]}>
            <ThemedText type="small" style={styles.badgeText}>
              {WITHDRAWAL_STATUS_LABEL[item.status]}
            </ThemedText>
          </View>
          <ThemedText type="small" themeColor="textSecondary">
            {new Date(item.created_at).toLocaleDateString('es-CL')}
          </ThemedText>
        </View>

        <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
          <ThemedText type="smallBold">Solicitud</ThemedText>
          <Field label="Correo" value={item.email} />
          <ThemedText type="small" themeColor="textSecondary">
            Motivo del cliente
          </ThemedText>
          <ThemedText type="small">{item.reason || 'No indicó motivo (no es obligatorio).'}</ThemedText>
          {item.staff_note ? <Field label="Nota interna" value={item.staff_note} /> : null}
          {item.resolved_at ? (
            <Field
              label="Cerrada"
              value={new Date(item.resolved_at).toLocaleDateString('es-CL')}
            />
          ) : null}
        </View>

        <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
          <ThemedText type="smallBold">Pedido y plazo</ThemedText>
          <Field label="Cliente" value={order.full_name ?? ''} />
          <Field label="Teléfono" value={order.telephone_number} />
          <Field label="Productos" value={formatCLP(productos)} />
          <Field label="Pagado" value={dateWithDays(order.paid_at)} />
          <Field
            label="Despachado"
            value={order.shipped_at ? dateWithDays(order.shipped_at) : 'Todavía no'}
          />
          {order.deliveryNumber ? (
            <Field label="Nº seguimiento" value={order.deliveryNumber} />
          ) : null}
          <ThemedText type="small" themeColor="textSecondary">
            El plazo legal es de 10 días desde que el cliente recibe el producto (90 si no
            recibió la confirmación escrita de la compra).
          </ThemedText>
          <Link href={`/(app)/orders/${order.id}`} asChild>
            <Pressable style={[styles.linkBtn, { borderColor: theme.backgroundSelected }]}>
              <ThemedText type="small">Ver pedido #{order.id}</ThemedText>
            </Pressable>
          </Link>
        </View>

        <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
          <ThemedText type="smallBold">Cambiar estado</ThemedText>
          {item.allowed_transitions.length === 0 ? (
            <ThemedText type="small" themeColor="textSecondary">
              La solicitud está cerrada. No admite más cambios.
            </ThemedText>
          ) : (
            <>
              <TextInput
                value={note}
                onChangeText={setNote}
                placeholder="Nota interna (obligatoria para rechazar)"
                placeholderTextColor={theme.textSecondary}
                style={[styles.input, { color: theme.text, borderColor: theme.backgroundSelected }]}
                multiline
              />
              <View style={styles.actions}>
                {item.allowed_transitions.map((status) => (
                  <Pressable
                    key={status}
                    onPress={() => handleChange(status)}
                    disabled={submitting !== null}
                    style={[
                      styles.actionBtn,
                      { backgroundColor: WITHDRAWAL_STATUS_COLOR[status] },
                      submitting !== null && submitting !== status && styles.dim,
                    ]}
                  >
                    {submitting === status ? (
                      <ActivityIndicator color="#ffffff" />
                    ) : (
                      <ThemedText type="smallBold" style={styles.actionText}>
                        {ACTION_LABEL[status]}
                      </ThemedText>
                    )}
                  </Pressable>
                ))}
              </View>
            </>
          )}
          {actionError ? (
            <ThemedText type="small" themeColor="textSecondary">
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
  field: { flexDirection: 'row', justifyContent: 'space-between', gap: 12 },
  fieldValue: { flexShrink: 1, textAlign: 'right' },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    minHeight: 60,
    textAlignVertical: 'top',
  },
  linkBtn: {
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  actions: { gap: 8 },
  actionBtn: { paddingVertical: 12, borderRadius: 10, alignItems: 'center' },
  actionText: { color: '#ffffff' },
  dim: { opacity: 0.4 },
});
