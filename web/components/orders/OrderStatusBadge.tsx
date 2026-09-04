import { ORDER_STATUS_LABEL, ORDER_STATUS_STYLE } from '@/lib/orders';
import type { OrderStatus } from '@/types/order';

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  return (
    <span
      className={[
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-medium uppercase tracking-wide',
        ORDER_STATUS_STYLE[status] ?? 'bg-piedra-100 text-piedra-600',
      ].join(' ')}
    >
      {ORDER_STATUS_LABEL[status] ?? status}
    </span>
  );
}
