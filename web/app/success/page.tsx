'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import { fetchOrderStatus } from '@/lib/checkout';
import type { OrderStatus } from '@/types/checkout';

const STATUS_LABELS: Record<string, { emoji: string; title: string; desc: string; color: string }> = {
  approved: {
    emoji: '✦',
    title: '¡Pago aprobado!',
    desc: 'Tu pedido está en proceso. Recibirás un correo con los detalles.',
    color: 'text-tierra-600',
  },
  pending: {
    emoji: '⧗',
    title: 'Pago pendiente',
    desc: 'Tu pago está siendo procesado. Te avisaremos cuando se confirme.',
    color: 'text-agata-600',
  },
  rejected: {
    emoji: '✗',
    title: 'Pago rechazado',
    desc: 'El pago no pudo completarse. Puedes intentarlo nuevamente.',
    color: 'text-red-600',
  },
  'no procesado': {
    emoji: '○',
    title: 'Pedido recibido',
    desc: 'Tu pedido fue registrado pero el pago aún no se ha confirmado.',
    color: 'text-piedra-600',
  },
};

function SuccessContent() {
  const searchParams = useSearchParams();

  // MercadoPago envía estos parámetros al volver.
  const externalRef = searchParams.get('external_reference');
  const collectionStatus = searchParams.get('collection_status') ?? searchParams.get('status');

  const [orderStatus, setOrderStatus] = useState<OrderStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(false);

  useEffect(() => {
    if (!externalRef) { setLoading(false); return; }
    fetchOrderStatus(externalRef)
      .then(setOrderStatus)
      .catch(() => setFetchError(true))
      .finally(() => setLoading(false));
  }, [externalRef]);

  // Determinar estado de visualización.
  const displayStatus =
    orderStatus?.payment_status ??
    orderStatus?.order_status ??
    collectionStatus ??
    'pending';

  const info = STATUS_LABELS[displayStatus] ?? STATUS_LABELS.pending;

  return (
    <div className="mx-auto flex max-w-lg flex-col items-center gap-6 px-6 py-20 text-center">
      <span className={`font-manuscrita text-6xl ${info.color}`}>{info.emoji}</span>

      <div>
        <h1 className={`font-serif text-3xl font-medium ${info.color}`}>{info.title}</h1>
        <p className="mt-2 text-piedra-600">{info.desc}</p>
      </div>

      {loading && (
        <p className="text-sm text-piedra-500">Verificando estado del pedido…</p>
      )}

      {!loading && !fetchError && orderStatus && (
        <dl className="w-full rounded-xl border border-piedra-200 bg-white p-5 text-left text-sm">
          <div className="flex justify-between py-1.5">
            <dt className="text-piedra-500">Número de pedido</dt>
            <dd className="font-medium text-piedra-900">#{orderStatus.order_id}</dd>
          </div>
          <div className="flex justify-between py-1.5">
            <dt className="text-piedra-500">Estado</dt>
            <dd className="font-medium capitalize text-piedra-900">{orderStatus.order_status}</dd>
          </div>
          {orderStatus.payment_status && (
            <div className="flex justify-between py-1.5">
              <dt className="text-piedra-500">Pago</dt>
              <dd className="font-medium capitalize text-piedra-900">{orderStatus.payment_status}</dd>
            </div>
          )}
          {orderStatus.transaction_id && (
            <div className="flex justify-between py-1.5">
              <dt className="text-piedra-500">ID transacción</dt>
              <dd className="font-mono text-xs text-piedra-700">{orderStatus.transaction_id}</dd>
            </div>
          )}
        </dl>
      )}

      <div className="flex flex-wrap justify-center gap-3">
        {displayStatus === 'rejected' && (
          <Link href="/checkout"
            className="rounded-full bg-tierra-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-tierra-600">
            Intentar nuevamente
          </Link>
        )}
        <Link href="/"
          className="rounded-full border border-piedra-200 px-6 py-2.5 text-sm font-medium text-piedra-800 hover:border-agata-500">
          Volver al inicio
        </Link>
        <Link href="/joyas"
          className="rounded-full border border-piedra-200 px-6 py-2.5 text-sm font-medium text-piedra-800 hover:border-agata-500">
          Seguir comprando
        </Link>
      </div>
    </div>
  );
}

export default function SuccessPage() {
  return (
    <Suspense fallback={
      <div className="mx-auto max-w-lg px-6 py-20 text-center text-piedra-500">Cargando…</div>
    }>
      <SuccessContent />
    </Suspense>
  );
}
