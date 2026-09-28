import Link from 'next/link';
import { hoursSince } from '@/lib/admin-stats';
import type { StatsPending } from '@/types/admin-stats';

/**
 * Estado de despacho de hoy. No depende del rango del panel a propósito: es la
 * foto operativa del momento, no un histórico.
 *
 * "Vencidas" se marca en rojo y además con la palabra: el estado nunca se
 * comunica solo con color.
 */
export function PendingPanel({ pending }: { pending: StatsPending }) {
  const { awaiting_dispatch, due_soon, overdue, oldest_paid_at } = pending;

  return (
    <section className="rounded-xl border border-piedra-200 bg-white p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-serif text-xl font-medium text-piedra-900">
          Por despachar ahora
        </h2>
        <Link
          href="/pedidos"
          className="text-sm text-tierra-700 underline decoration-tierra-300 underline-offset-4 hover:text-tierra-800"
        >
          Ver pedidos
        </Link>
      </div>

      <dl className="mt-4 grid grid-cols-3 gap-4">
        <div>
          <dt className="text-xs uppercase tracking-wide text-piedra-500">
            Pendientes
          </dt>
          <dd className="mt-1 text-2xl font-medium tabular-nums lining-nums text-piedra-900">
            {awaiting_dispatch}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-piedra-500">
            Por vencer
          </dt>
          <dd
            className={`mt-1 text-2xl font-medium tabular-nums lining-nums ${
              due_soon > 0 ? 'text-tierra-700' : 'text-piedra-900'
            }`}
          >
            {due_soon}
          </dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide text-piedra-500">
            Vencidas
          </dt>
          <dd
            className={`mt-1 text-2xl font-medium tabular-nums lining-nums ${
              overdue > 0 ? 'text-red-600' : 'text-piedra-900'
            }`}
          >
            {overdue}
          </dd>
        </div>
      </dl>

      {overdue > 0 && (
        <p className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          <strong className="font-medium">Atención:</strong> {overdue}{' '}
          {overdue === 1 ? 'venta pasó' : 'ventas pasaron'} el plazo de despacho.
        </p>
      )}

      {oldest_paid_at && awaiting_dispatch > 0 && (
        <p className="mt-3 text-xs text-piedra-500">
          La más antigua sin despachar se pagó hace {hoursSince(oldest_paid_at)} h.
        </p>
      )}

      {awaiting_dispatch === 0 && (
        <p className="mt-4 text-sm text-piedra-500">
          No queda nada pendiente de despacho.
        </p>
      )}
    </section>
  );
}
