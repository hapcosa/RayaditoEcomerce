import type { OrderDetail, OrderStatus, OrderSummary } from '@/types/order';
import { API_BASE_URL } from './api';

function authHeaders(access: string) {
  return { 'Content-Type': 'application/json', Authorization: `JWT ${access}` };
}

/** GET /api/orders/get-orders — pedidos del usuario, en cualquier estado. */
export async function fetchOrders(access: string): Promise<OrderSummary[]> {
  const res = await fetch(`${API_BASE_URL}/orders/get-orders`, {
    headers: authHeaders(access),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`orders ${res.status}`);
  const data = (await res.json()) as { orders: OrderSummary[] };
  return data.orders;
}

/** GET /api/orders/get-order/<id> — acepta transaction_id o el id numérico. */
export async function fetchOrder(
  access: string,
  reference: string,
): Promise<OrderDetail> {
  const res = await fetch(
    `${API_BASE_URL}/orders/get-order/${encodeURIComponent(reference)}`,
    { headers: authHeaders(access), cache: 'no-store' },
  );
  if (!res.ok) throw new Error(`order ${res.status}`);
  const data = (await res.json()) as { order: OrderDetail };
  return data.order;
}

/** Etiqueta en es-CL para el cliente. El backend usa "enviado" para despachado. */
export const ORDER_STATUS_LABEL: Record<OrderStatus, string> = {
  'no procesado': 'Pendiente',
  procesado: 'En preparación',
  enviado: 'Enviado',
  cancelado: 'Cancelado',
  rechazado: 'Rechazado',
};

/** Clases Tailwind del badge de estado, sobre la paleta piedra/tierra/ágata. */
export const ORDER_STATUS_STYLE: Record<OrderStatus, string> = {
  'no procesado': 'bg-piedra-100 text-piedra-600',
  procesado: 'bg-agata-100 text-agata-700',
  enviado: 'bg-tierra-100 text-tierra-700',
  cancelado: 'bg-piedra-100 text-piedra-500',
  rechazado: 'bg-red-50 text-red-600',
};

/** Fecha larga en es-CL: "12 de marzo de 2026". */
export function formatOrderDate(iso: string): string {
  return new Date(iso).toLocaleDateString('es-CL', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  });
}
