'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { OrderStatusBadge } from '@/components/orders/OrderStatusBadge';
import { fetchOrders, formatOrderDate } from '@/lib/orders';
import { formatCLP } from '@/lib/format';
import { useAuthStore } from '@/lib/store/auth';
import type { OrderSummary } from '@/types/order';

export default function OrdersPage() {
  const router = useRouter();
  const access = useAuthStore((s) => s.access);
  const [mounted, setMounted] = useState(false);
  const [orders, setOrders] = useState<OrderSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const load = useCallback(async (token: string) => {
    try {
      setOrders(await fetchOrders(token));
    } catch {
      setError('No pudimos cargar tus pedidos. Intentá de nuevo en un momento.');
    }
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (!access) {
      router.replace('/auth/login?next=/pedidos');
      return;
    }
    load(access);
  }, [mounted, access, load, router]);

  if (!mounted || !access) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16 text-center text-piedra-500">
        Cargando…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <p className="font-manuscrita text-xl text-tierra-600">tus compras</p>
      <h1 className="mt-1 font-serif text-3xl font-medium text-piedra-900">
        Mis pedidos
      </h1>

      {error && (
        <p className="mt-8 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </p>
      )}

      {!error && orders === null && (
        <p className="mt-8 text-piedra-500">Cargando pedidos…</p>
      )}

      {orders?.length === 0 && (
        <div className="mt-12 flex flex-col items-center gap-4 text-center">
          <span className="font-manuscrita text-5xl text-tierra-300">✦</span>
          <p className="text-piedra-600">Todavía no hiciste ningún pedido.</p>
          <Link
            href="/joyas"
            className="rounded-full bg-tierra-500 px-6 py-2.5 text-sm font-medium uppercase tracking-wide text-piedra-50 hover:bg-tierra-600"
          >
            Explorar joyas
          </Link>
        </div>
      )}

      {orders && orders.length > 0 && (
        <ul className="mt-8 flex flex-col gap-4">
          {orders.map((order) => (
            <li key={order.id}>
              <Link
                href={`/pedidos/${order.transaction_id ?? order.id}`}
                className="flex flex-col gap-3 rounded-xl border border-piedra-200 bg-white p-5 transition-shadow hover:shadow-md"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-serif text-lg text-piedra-900">
                    Pedido #{order.transaction_id ?? order.id}
                  </span>
                  <OrderStatusBadge status={order.status} />
                </div>
                <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm text-piedra-500">
                  <span>{formatOrderDate(order.date_issued)}</span>
                  <span>
                    {order.items_count}{' '}
                    {order.items_count === 1 ? 'pieza' : 'piezas'}
                  </span>
                  <span className="font-semibold text-piedra-900">
                    {formatCLP(order.amount)}
                  </span>
                </div>
                {order.deliveryNumber && (
                  <p className="text-sm text-tierra-700">
                    Seguimiento:{' '}
                    <span className="font-mono">{order.deliveryNumber}</span>
                  </p>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
