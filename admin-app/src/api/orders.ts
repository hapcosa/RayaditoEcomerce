/**
 * Capa de datos de pedidos contra la API admin (`/api/admin/orders/`).
 * Requiere staff (el header JWT lo agrega apiFetch).
 *
 * Dinero en entero CLP (ver AGENTS.md): `amount`/`price`/`shipping_price` son
 * number enteros. Los estados son los `OrderStatus` del backend (en español).
 */
import { apiJson } from './client';

/** Valores de `Order.OrderStatus` en el backend (es-CL, con espacios). */
export type OrderStatus =
  | 'no procesado'
  | 'procesado'
  | 'enviado'
  | 'cancelado'
  | 'rechazado';

export type OrderItem = {
  id: number;
  product_id: number | null;
  name: string;
  price: number;
  count: number;
  date_added: string;
};

export type Order = {
  id: number;
  status: OrderStatus;
  transaction_id: string | null;
  amount: number | null;
  shipping_price: number;
  full_name: string;
  email: string | null;
  address_line_1: string;
  city: string;
  postal_zip_code: string;
  region: string;
  telephone_number: string;
  deliveryNumber: string | null;
  date_issued: string;
  items: OrderItem[];
  /** Estados a los que este pedido puede transicionar (los expone el backend). */
  allowed_transitions: OrderStatus[];
};

/** DRF pagina la lista; toleramos respuesta paginada o array plano. */
type Paginated<T> = { results: T[] };

function isPaginated<T>(data: T[] | Paginated<T>): data is Paginated<T> {
  return !Array.isArray(data) && Array.isArray((data as Paginated<T>).results);
}

export async function listOrders(status?: OrderStatus): Promise<Order[]> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : '';
  const data = await apiJson<Order[] | Paginated<Order>>(`/api/admin/orders/${qs}`);
  return isPaginated(data) ? data.results : data;
}

export async function getOrder(id: number): Promise<Order> {
  return apiJson<Order>(`/api/admin/orders/${id}/`);
}

/**
 * Cambia el estado de un pedido respetando la máquina de estados del backend.
 * Al pasar a `enviado` el backend exige `deliveryNumber` (número de seguimiento).
 */
export async function changeOrderStatus(
  id: number,
  status: OrderStatus,
  deliveryNumber?: string,
): Promise<Order> {
  const body: Record<string, string> = { status };
  if (deliveryNumber) body.deliveryNumber = deliveryNumber;
  return apiJson<Order>(`/api/admin/orders/${id}/status/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}
