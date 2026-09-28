'use client';

import dynamic from 'next/dynamic';
import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { PendingPanel } from '@/components/panel/PendingPanel';
import { StatCard } from '@/components/panel/StatCard';
import { TopProductsChart } from '@/components/panel/TopProductsChart';
import {
  RANGE_OPTIONS,
  StatsError,
  fetchAdminStats,
  longDate,
  shortDate,
} from '@/lib/admin-stats';
import { apiRefresh } from '@/lib/auth';
import { formatCLP } from '@/lib/format';
import { ORDER_STATUS_LABEL } from '@/lib/orders';
import { useAuthStore } from '@/lib/store/auth';
import type { AdminStats } from '@/types/admin-stats';
import type { OrderStatus } from '@/types/order';

// Recharts toca el DOM al medir el contenedor, así que se carga solo en cliente.
const SalesSeriesChart = dynamic(
  () => import('@/components/panel/SalesSeriesChart').then((m) => m.SalesSeriesChart),
  { ssr: false, loading: () => <div className="h-72 w-full animate-pulse rounded-lg bg-piedra-100" /> },
);

/**
 * Panel de ventas del dueño.
 *
 * El control de acceso vive en el backend: `/api/admin/stats/` exige
 * `IsAdminUser` y responde 403 a una cuenta que no es staff. Esta página solo
 * decide qué mostrar según esa respuesta — no valida permisos por su cuenta,
 * porque cualquier chequeo en el navegador es cosmético.
 */
export default function PanelPage() {
  const router = useRouter();
  const { access, refresh, setAccess, logout } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [days, setDays] = useState<number>(30);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const load = useCallback(
    async (token: string, range: number) => {
      setError(null);
      try {
        setStats(await fetchAdminStats(token, range));
      } catch (e) {
        if (e instanceof StatsError && e.status === 403) {
          setForbidden(true);
          return;
        }
        // 401: el access venció. Se reintenta una vez con el refresh y, si
        // tampoco sirve, la sesión se cierra y vuelve al login.
        if (e instanceof StatsError && e.status === 401 && refresh) {
          try {
            const { access: fresh } = await apiRefresh(refresh);
            setAccess(fresh);
            setStats(await fetchAdminStats(fresh, range));
            return;
          } catch {
            logout();
            router.replace('/auth/login?next=/panel');
            return;
          }
        }
        setError('No pudimos cargar las métricas. Intenta de nuevo en un momento.');
      }
    },
    [refresh, setAccess, logout, router],
  );

  useEffect(() => {
    if (!mounted) return;
    if (!access) {
      router.replace('/auth/login?next=/panel');
      return;
    }
    load(access, days);
  }, [mounted, access, days, load, router]);

  if (!mounted || !access) {
    return (
      <div className="mx-auto max-w-contenido px-4 py-16 text-center text-piedra-500 sm:px-6 lg:px-10">
        Cargando…
      </div>
    );
  }

  if (forbidden) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-16">
        <h1 className="font-serif text-2xl font-medium text-piedra-900">
          Panel de ventas
        </h1>
        <p className="mt-3 text-sm text-piedra-600">
          Tu cuenta no tiene permisos para ver estas métricas. Pídele al
          administrador que la habilite como staff.
        </p>
      </div>
    );
  }

  const previousLabel = stats
    ? `${longDate(stats.previous.from)} – ${longDate(stats.previous.to)}`
    : '';

  return (
    <div className="mx-auto max-w-contenido px-4 py-10 sm:px-6 lg:px-10">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-manuscrita text-xl text-tierra-600">tus ventas</p>
          <h1 className="mt-1 font-serif text-3xl font-medium text-piedra-900">
            Panel
          </h1>
          {stats && (
            <p className="mt-1 text-sm text-piedra-500">
              {longDate(stats.period.from)} – {longDate(stats.period.to)}
            </p>
          )}
        </div>

        {/* Los filtros van en una sola fila arriba de todo lo que afectan. */}
        <div className="flex flex-wrap gap-2" role="group" aria-label="Rango de fechas">
          {RANGE_OPTIONS.map((option) => (
            <button
              key={option.days}
              type="button"
              onClick={() => setDays(option.days)}
              aria-pressed={days === option.days}
              className={`rounded-full border px-4 py-1.5 text-sm transition ${
                days === option.days
                  ? 'border-tierra-500 bg-tierra-500 text-white'
                  : 'border-piedra-300 bg-white text-piedra-700 hover:border-tierra-300'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </header>

      {error && (
        <p className="mt-8 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </p>
      )}

      {!stats && !error && (
        <p className="mt-10 text-sm text-piedra-500">Cargando métricas…</p>
      )}

      {stats && (
        <div className="mt-8 space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Venta neta"
              value={formatCLP(stats.totals.net_clp)}
              current={stats.totals.net_clp}
              previous={stats.previous.net_clp}
              previousLabel="el periodo anterior"
            />
            <StatCard
              label="Ventas pagadas"
              value={String(stats.totals.orders_paid)}
              current={stats.totals.orders_paid}
              previous={stats.previous.orders_paid}
              previousLabel="el periodo anterior"
            />
            <StatCard
              label="Ticket promedio"
              value={formatCLP(stats.totals.average_order_clp)}
              current={stats.totals.average_order_clp}
              previous={stats.previous.average_order_clp}
              previousLabel="el periodo anterior"
            />
            <StatCard
              label="Piezas vendidas"
              value={String(stats.totals.items_sold)}
              current={stats.totals.items_sold}
              previous={stats.previous.items_sold}
              previousLabel="el periodo anterior"
            />
          </div>

          <p className="text-xs text-piedra-500">
            Periodo anterior comparado: {previousLabel}. La venta neta descuenta
            el envío del total cobrado ({formatCLP(stats.totals.gross_clp)} bruto,{' '}
            {formatCLP(stats.totals.shipping_clp)} de envío).
          </p>

          <PendingPanel pending={stats.pending} />

          <section className="rounded-xl border border-piedra-200 bg-white p-5">
            <h2 className="font-serif text-xl font-medium text-piedra-900">
              Venta neta por día
            </h2>
            <p className="mt-1 text-sm text-piedra-500">
              Cada barra es un día del periodo; los días sin ventas quedan en cero.
            </p>
            <div className="mt-4">
              <SalesSeriesChart series={stats.series} />
            </div>

            {/* Vista de tabla: el mismo dato sin depender de ver el gráfico. */}
            <details className="mt-4">
              <summary className="cursor-pointer text-sm text-tierra-700">
                Ver los datos en tabla
              </summary>
              <div className="mt-3 max-h-64 overflow-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-xs uppercase tracking-wide text-piedra-500">
                    <tr>
                      <th className="py-1 pr-4 font-normal">Día</th>
                      <th className="py-1 pr-4 font-normal">Ventas</th>
                      <th className="py-1 pr-4 font-normal">Piezas</th>
                      <th className="py-1 font-normal">Neto</th>
                    </tr>
                  </thead>
                  <tbody className="text-piedra-700">
                    {stats.series
                      .filter((point) => point.orders > 0)
                      .map((point) => (
                        <tr key={point.date} className="border-t border-piedra-100">
                          <td className="py-1 pr-4">{shortDate(point.date)}</td>
                          <td className="py-1 pr-4">{point.orders}</td>
                          <td className="py-1 pr-4">{point.items}</td>
                          <td className="py-1">{formatCLP(point.net_clp)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
                {stats.series.every((point) => point.orders === 0) && (
                  <p className="py-2 text-sm text-piedra-500">
                    No hubo ventas pagadas en este periodo.
                  </p>
                )}
              </div>
            </details>
          </section>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <section className="rounded-xl border border-piedra-200 bg-white p-5 lg:col-span-2">
              <h2 className="font-serif text-xl font-medium text-piedra-900">
                Piezas más vendidas
              </h2>
              <p className="mt-1 text-sm text-piedra-500">
                Por venta neta del periodo, al precio que tenían al vender.
              </p>
              <div className="mt-4">
                <TopProductsChart products={stats.top_products} />
              </div>
            </section>

            <section className="rounded-xl border border-piedra-200 bg-white p-5">
              <h2 className="font-serif text-xl font-medium text-piedra-900">
                Catálogo y pedidos
              </h2>
              <p className="mt-1 text-sm text-piedra-500">
                Conteo de hoy, sin importar el rango elegido.
              </p>
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between border-b border-piedra-100 pb-2">
                  <dt className="text-piedra-600">Piezas disponibles</dt>
                  <dd className="font-medium text-piedra-900">
                    {stats.catalog.available}
                  </dd>
                </div>
                <div className="flex justify-between border-b border-piedra-100 pb-2">
                  <dt className="text-piedra-600">Piezas vendidas</dt>
                  <dd className="font-medium text-piedra-900">{stats.catalog.sold}</dd>
                </div>
                {Object.entries(stats.by_status).map(([status, total]) => (
                  <div key={status} className="flex justify-between">
                    <dt className="text-piedra-600">
                      {ORDER_STATUS_LABEL[status as OrderStatus] ?? status}
                    </dt>
                    <dd className="font-medium text-piedra-900">{total}</dd>
                  </div>
                ))}
              </dl>
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
