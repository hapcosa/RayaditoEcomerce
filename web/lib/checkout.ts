import type { SavedProfile, CheckoutForm, PaymentPreference, OrderStatus } from '@/types/checkout';

const API =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api';

function authHeaders(access: string) {
  return { 'Content-Type': 'application/json', Authorization: `JWT ${access}` };
}

// ---------- Perfil de usuario -----------------------------------------------

export async function fetchProfile(access: string): Promise<SavedProfile | null> {
  const res = await fetch(`${API}/profile/user`, {
    headers: authHeaders(access),
    cache: 'no-store',
  });
  if (!res.ok) return null;
  const data = await res.json() as { profile?: SavedProfile };
  return data.profile ?? null;
}

export async function createProfile(
  access: string,
  data: Omit<SavedProfile, 'id'>,
): Promise<SavedProfile> {
  const res = await fetch(`${API}/profile/create`, {
    method: 'PUT',
    headers: authHeaders(access),
    body: JSON.stringify(data),
    cache: 'no-store',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as Record<string, unknown>;
    const msg = (Object.values(err).flat() as string[]).join(' ') || 'Error al guardar dirección';
    throw new Error(msg);
  }
  const result = await res.json() as { profile?: SavedProfile };
  return result.profile!;
}

// ---------- Pago ------------------------------------------------------------

/** Checkout autenticado: usa el carrito + perfil del backend. */
export async function processAuthPayment(
  access: string,
  profileId: number,
  shippingId: number,
): Promise<{ preference: PaymentPreference; orderId: number }> {
  const res = await fetch(`${API}/payment/make-payment`, {
    method: 'POST',
    headers: authHeaders(access),
    body: JSON.stringify({ profile_id: profileId, shipping_id: shippingId }),
    cache: 'no-store',
  });
  const data = await res.json() as { response?: PaymentPreference; order_id?: number; error?: string };
  if (!res.ok) throw new Error(data.error ?? 'Error al procesar el pago');
  return { preference: data.response!, orderId: data.order_id! };
}

/** Checkout de invitado: envía items y datos del comprador. */
export async function processGuestPayment(
  form: CheckoutForm,
  items: { product: { id: number }; count: number }[],
): Promise<{ preference: PaymentPreference; orderId: number }> {
  const res = await fetch(`${API}/payment/make-payment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...form, items }),
    cache: 'no-store',
  });
  const data = await res.json() as { response?: PaymentPreference; order_id?: number; error?: string };
  if (!res.ok) throw new Error(data.error ?? 'Error al procesar el pago');
  return { preference: data.response!, orderId: data.order_id! };
}

// ---------- Estado de orden -------------------------------------------------

export async function fetchOrderStatus(orderId: string | number): Promise<OrderStatus> {
  const res = await fetch(`${API}/payment/status-payment?order_id=${orderId}`, {
    cache: 'no-store',
  });
  if (!res.ok) throw new Error('No se pudo obtener el estado del pago');
  return res.json() as Promise<OrderStatus>;
}
