/** Etiquetas es-CL y colores para los estados de pedido (OrderStatus del backend). */
import type { OrderStatus } from '@/api/orders';

export const ORDER_STATUS_LABEL: Record<OrderStatus, string> = {
  'no procesado': 'No procesado',
  procesado: 'Procesado',
  enviado: 'Enviado',
  cancelado: 'Cancelado',
  rechazado: 'Rechazado',
};

/** Color de acento por estado (fondo del chip/badge). Tonos tierra/piedra. */
export const ORDER_STATUS_COLOR: Record<OrderStatus, string> = {
  'no procesado': '#B08968', // arena
  procesado: '#7D8471', // salvia
  enviado: '#5B7B7A', // ágata
  cancelado: '#8A8A8A', // gris piedra
  rechazado: '#A15C4A', // óxido
};
