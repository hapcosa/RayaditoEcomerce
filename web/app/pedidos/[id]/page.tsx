'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { OrderStatusBadge } from '@/components/orders/OrderStatusBadge';
import { TrackingNumber } from '@/components/orders/TrackingNumber';
import { fetchOrder, formatOrderDate } from '@/lib/orders';
import { formatCLP } from '@/lib/format';
import { useAuthStore } from '@/lib/store/auth';
import type { OrderDetail } from '@/types/order';

export default function OrderDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const reference = params?.id ?? '';
  const access = useAuthStore((s) => s.access);
  const [mounted, setMounted] = useState(false);
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const load = useCallback(
    async (token: string) => {
      try {
        setOrder(await fetchOrder(token, reference));
      } catch {
        setError('No encontramos ese pedido en tu cuenta.');
      }
    },
    [reference],
  );

  useEffect(() => {
    if (!mounted) return;
    if (!access) {
      router.replace(`/auth/login?next=/pedidos/${reference}`);
      return;
    }
    load(access);
  }, [mounted, access, load, reference, router]);

  if (!mounted || !access) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16 text-center text-piedra-500">
        Cargando…
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-16 text-center">
        <p className="text-piedra-600">{error}</p>
        <Link href="/pedidos" className="mt-4 inline-block text-sm text-tierra-600 hover:underline">
          ← Volver a mis pedidos
        </Link>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16 text-center text-piedra-500">
        Cargando pedido…
      </div>
    );
  }

  const subtotal = order.amount - order.shipping_price;

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <Link href="/pedidos" className="text-sm text-tierra-600 hover:underline">
        ← Mis pedidos
      </Link>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-serif text-3xl font-medium text-piedra-900">
          Pedido #{order.transaction_id ?? order.id}
        </h1>
        <OrderStatusBadge status={order.status} />
      </div>
      <p className="mt-1 text-sm text-piedra-500">
        {formatOrderDate(order.date_issued)}
      </p>

      {order.deliveryNumber && (
        <div className="mt-6">
          <TrackingNumber value={order.deliveryNumber} />
          {order.shipping && (
            <p className="mt-2 text-xs text-piedra-500">
              Despachado por {order.shipping.name}. Consultá el número en el
              sitio de la empresa de transporte.
            </p>
          )}
        </div>
      )}

      <section className="mt-10">
        <h2 className="font-serif text-xl text-piedra-900">Piezas</h2>
        <ul className="mt-4 flex flex-col divide-y divide-piedra-100 rounded-xl border border-piedra-200 bg-white">
          {order.order_items.map((item) => (
            <li key={item.id} className="flex items-center gap-4 p-4">
              <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-lg bg-piedra-100">
                {item.product_photo ? (
                  <Image
                    src={item.product_photo}
                    alt={item.name}
                    fill
                    sizes="64px"
                    className="object-cover"
                  />
                ) : (
                  <span className="flex h-full items-center justify-center font-manuscrita text-2xl text-piedra-300">
                    ✦
                  </span>
                )}
              </div>
              <div className="min-w-0 flex-1">
                {item.product_slug ? (
                  <Link
                    href={`/productos/${item.product_slug}`}
                    className="text-sm font-medium text-piedra-900 hover:text-tierra-600"
                  >
                    {item.name}
                  </Link>
                ) : (
                  <span className="text-sm font-medium text-piedra-900">{item.name}</span>
                )}
                <p className="text-xs text-piedra-500">
                  {item.count} × {formatCLP(item.price)}
                </p>
              </div>
              <span className="text-sm font-semibold text-piedra-900">
                {formatCLP(item.price * item.count)}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div className="rounded-xl border border-piedra-200 bg-white p-5">
          <h2 className="font-serif text-lg text-piedra-900">Envío</h2>
          <address className="mt-3 not-italic text-sm leading-relaxed text-piedra-600">
            {order.full_name && <>{order.full_name}<br /></>}
            {order.address_line_1 && <>{order.address_line_1}<br /></>}
            {[order.city, order.region_display].filter(Boolean).join(', ')}
            {order.postal_zip_code && <><br />{order.postal_zip_code}</>}
            {order.telephone_number && <><br />{order.telephone_number}</>}
          </address>
          {order.shipping && (
            <p className="mt-3 text-xs text-piedra-500">
              {order.shipping.name} — {order.shipping.time_to_delivery}
            </p>
          )}
        </div>

        <div className="rounded-xl border border-piedra-200 bg-white p-5">
          <h2 className="font-serif text-lg text-piedra-900">Total</h2>
          <dl className="mt-3 flex flex-col gap-2 text-sm">
            <div className="flex justify-between text-piedra-600">
              <dt>Subtotal</dt>
              <dd>{formatCLP(subtotal)}</dd>
            </div>
            <div className="flex justify-between text-piedra-600">
              <dt>Envío</dt>
              <dd>{formatCLP(order.shipping_price)}</dd>
            </div>
            <div className="flex justify-between border-t border-piedra-100 pt-2 text-base font-semibold text-piedra-900">
              <dt>Total</dt>
              <dd>{formatCLP(order.amount)}</dd>
            </div>
          </dl>
        </div>
      </section>
    </div>
  );
}
