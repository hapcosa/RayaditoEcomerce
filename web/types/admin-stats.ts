/**
 * Respuesta de `GET /api/admin/stats/` (ver `orders/admin_stats.py`).
 *
 * Todo el dinero llega como entero CLP; el formateo es responsabilidad del
 * cliente (`lib/format.ts`). `Order.amount` incluye el envío, por eso el
 * backend separa bruto / envío / neto en vez de reportar un solo total.
 */

/** Totales de un periodo. `previous` agrega el rango al que corresponden. */
export interface StatsTotals {
  orders_paid: number;
  gross_clp: number;
  shipping_clp: number;
  net_clp: number;
  items_sold: number;
  average_order_clp: number;
}

export interface StatsPeriod {
  days: number;
  from: string;
  to: string;
}

export interface StatsPrevious extends StatsTotals {
  from: string;
  to: string;
}

/** Foto operativa de hoy: no depende del rango consultado. */
export interface StatsPending {
  awaiting_dispatch: number;
  due_soon: number;
  overdue: number;
  oldest_paid_at: string | null;
}

/** Un punto de la serie diaria. Los días sin ventas vienen en cero. */
export interface StatsSeriesPoint {
  date: string;
  orders: number;
  gross_clp: number;
  net_clp: number;
  items: number;
}

export interface StatsTopProduct {
  product_id: number | null;
  name: string;
  units: number;
  net_clp: number;
}

export interface AdminStats {
  generated_at: string;
  period: StatsPeriod;
  totals: StatsTotals;
  previous: StatsPrevious;
  pending: StatsPending;
  series: StatsSeriesPoint[];
  top_products: StatsTopProduct[];
  by_status: Record<string, number>;
  catalog: { available: number; sold: number };
}
