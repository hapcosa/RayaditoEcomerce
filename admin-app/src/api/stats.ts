/**
 * Resumen de ventas para el home (`GET /api/admin/stats/`). Requiere staff.
 *
 * Es el mismo endpoint que alimenta el panel web (`web/lib/admin-stats.ts`);
 * la app solo toma `totals`, `previous` y `pending`, y deja `series` y
 * `top_products` para los gráficos del panel.
 *
 * Dinero en entero CLP (ver AGENTS.md): el formateo es de `utils/money.ts`.
 */
import { apiJson } from './client';

/** Totales de un periodo. */
export type StatsTotals = {
  orders_paid: number;
  gross_clp: number;
  shipping_clp: number;
  net_clp: number;
  items_sold: number;
  average_order_clp: number;
};

export type StatsPrevious = StatsTotals & { from: string; to: string };

/** Foto operativa del momento: no depende del rango consultado. */
export type StatsPending = {
  awaiting_dispatch: number;
  due_soon: number;
  overdue: number;
  oldest_paid_at: string | null;
};

/**
 * La app solo declara lo que usa. `series`, `top_products`, `by_status` y
 * `catalog` vienen en la respuesta pero no se tipan aquí a propósito: tipar de
 * más obliga a tocar este archivo cada vez que el panel web agrega un campo.
 */
export type AdminStats = {
  generated_at: string;
  period: { days: number; from: string; to: string };
  totals: StatsTotals;
  previous: StatsPrevious;
  pending: StatsPending;
};

/** Rango del resumen del home. Fijo por ahora; el selector es trabajo aparte. */
export const SUMMARY_DAYS = 30;

export async function getAdminStats(days: number = SUMMARY_DAYS): Promise<AdminStats> {
  return apiJson<AdminStats>(`/api/admin/stats/?days=${days}`);
}

/**
 * Variación porcentual contra el periodo anterior.
 *
 * Devuelve `null` si el periodo anterior fue cero: "subió infinito" no es un
 * dato útil, la tarjeta prefiere decir que no hay con qué comparar.
 */
export function deltaPercent(current: number, previous: number): number | null {
  if (previous === 0) return null;
  return Math.round(((current - previous) / previous) * 100);
}

/** Antigüedad en horas de un ISO datetime, redondeada hacia abajo. */
export function hoursSince(iso: string): number {
  return Math.floor((Date.now() - new Date(iso).getTime()) / 3_600_000);
}
