import type { ShippingOption } from './cart';

/** Estados de `Order.OrderStatus` en el backend (orders/models.py). */
export type OrderStatus =
  | 'no procesado'
  | 'procesado'
  | 'enviado'
  | 'cancelado'
  | 'rechazado';

export interface OrderItem {
  id: number;
  /** Nombre congelado al momento de la compra, no el del catálogo hoy. */
  name: string;
  /** Precio unitario en CLP entero. */
  price: number;
  count: number;
  product_id: number | null;
  product_slug: string | null;
  product_photo: string | null;
}

/** Fila del listado "Mis pedidos" (GET /api/orders/get-orders). */
export interface OrderSummary {
  id: number;
  status: OrderStatus;
  status_display: string;
  transaction_id: string | null;
  /** Total en CLP entero. */
  amount: number;
  shipping_price: number;
  date_issued: string;
  address_line_1: string | null;
  city: string | null;
  /** Número de seguimiento de la empresa de despacho; null hasta despachar. */
  deliveryNumber: string | null;
  items_count: number;
  shipping: ShippingOption | null;
}

/** Detalle (GET /api/orders/get-order/<transactionId>). */
export interface OrderDetail extends Omit<OrderSummary, 'items_count'> {
  full_name: string | null;
  email: string | null;
  postal_zip_code: string;
  region: string;
  region_display: string;
  telephone_number: string;
  order_items: OrderItem[];
}
