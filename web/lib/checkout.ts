import type { CheckoutForm, PaymentPreference, OrderStatus } from '@/types/checkout';
import type { InvoiceFields } from '@/lib/billing';

const API =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api';

function authHeaders(access: string) {
  return { 'Content-Type': 'application/json', Authorization: `JWT ${access}` };
}

// ---------- Carrito del servidor --------------------------------------------

/**
 * Deja el carrito del servidor igual al del navegador.
 *
 * La tienda guarda el carrito en `localStorage` para que funcione sin sesión,
 * pero el pago autenticado arma la orden desde el carrito del backend. Sin este
 * paso el servidor no ve nada y responde "No tienes productos en tu carrito".
 */
export async function pushCart(
  access: string,
  items: { product_id: number; count: number }[],
): Promise<void> {
  const res = await fetch(`${API}/cart/replace`, {
    method: 'POST',
    headers: authHeaders(access),
    body: JSON.stringify({ cart_items: items }),
    cache: 'no-store',
  });
  if (!res.ok) {
    const data = (await res.json().catch(() => ({}))) as { error?: string };
    throw new Error(data.error ?? 'No se pudo preparar tu carrito');
  }
}

// ---------- Pago ------------------------------------------------------------

type PaymentResponse = {
  response?: PaymentPreference;
  order_id?: number;
  error?: string;
  /** Errores por campo de los datos de factura (400). */
  invoice?: Record<string, string>;
};

function paymentError(data: PaymentResponse): Error {
  const detalle = data.invoice ? Object.values(data.invoice).join(' ') : '';
  return new Error(
    [data.error ?? 'Error al procesar el pago', detalle].filter(Boolean).join(' '),
  );
}

/** Checkout autenticado: usa el carrito + perfil del backend. */
export async function processAuthPayment(
  access: string,
  profileId: number,
  shippingId: number,
  invoice?: InvoiceFields | null,
): Promise<{ preference: PaymentPreference; orderId: number }> {
  const res = await fetch(`${API}/payment/make-payment`, {
    method: 'POST',
    headers: authHeaders(access),
    body: JSON.stringify({ profile_id: profileId, shipping_id: shippingId, invoice: invoice ?? null }),
    cache: 'no-store',
  });
  const data = await res.json() as PaymentResponse;
  if (!res.ok) throw paymentError(data);
  return { preference: data.response!, orderId: data.order_id! };
}

/** Checkout de invitado: envía items y datos del comprador. */
export async function processGuestPayment(
  form: CheckoutForm,
  items: { product: { id: number }; count: number }[],
  invoice?: InvoiceFields | null,
): Promise<{ preference: PaymentPreference; orderId: number }> {
  const res = await fetch(`${API}/payment/make-payment`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...form, items, invoice: invoice ?? null }),
    cache: 'no-store',
  });
  const data = await res.json() as PaymentResponse;
  if (!res.ok) throw paymentError(data);
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
