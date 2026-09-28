'use client';

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { formatCLP } from '@/lib/format';
import { longDate, shortDate } from '@/lib/admin-stats';
import type { StatsSeriesPoint } from '@/types/admin-stats';

/** Naranjo de marca (tierra-500). Recharts necesita el color resuelto, no la var. */
const SERIE = '#c4550f';

/** Miles abreviados para el eje: 125000 → "125k". */
function axisCLP(value: number): string {
  if (value === 0) return '0';
  if (value >= 1_000_000) return `${Math.round(value / 100_000) / 10}M`;
  if (value >= 1_000) return `${Math.round(value / 1_000)}k`;
  return String(value);
}

interface TooltipPayload {
  active?: boolean;
  payload?: { payload: StatsSeriesPoint }[];
}

/** Tooltip propio: el del default no sabe de CLP ni de envío. */
function SeriesTooltip({ active, payload }: TooltipPayload) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  const shipping = point.gross_clp - point.net_clp;

  return (
    <div className="rounded-lg border border-piedra-200 bg-white px-3 py-2 text-xs shadow-sm">
      <p className="font-medium text-piedra-900">{longDate(point.date)}</p>
      <p className="mt-1 text-piedra-700">
        Neto <span className="font-medium">{formatCLP(point.net_clp)}</span>
      </p>
      <p className="text-piedra-500">Envío {formatCLP(shipping)}</p>
      <p className="mt-1 text-piedra-500">
        {point.orders} {point.orders === 1 ? 'venta' : 'ventas'} · {point.items}{' '}
        {point.items === 1 ? 'pieza' : 'piezas'}
      </p>
    </div>
  );
}

/**
 * Venta neta por día, con Recharts.
 *
 * Es una sola serie a propósito: el envío no es una identidad que competir con
 * el neto, es un descuento del bruto, así que vive en el tooltip en vez de
 * apilarse encima. Una serie no lleva leyenda — el título ya la nombra.
 */
export function SalesSeriesChart({ series }: { series: StatsSeriesPoint[] }) {
  return (
    <div className="h-72 w-full min-w-0">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={series}
          margin={{ top: 8, right: 8, bottom: 0, left: 8 }}
        >
          <CartesianGrid
            stroke='#e8e8e5'
            strokeDasharray="2 4"
            vertical={false}
          />
          <XAxis
            dataKey='date'
            tickFormatter={shortDate}
            // Recharts decide cuántas fechas caben según el ancho real: con 30
            // días en un teléfono, fijar el intervalo a mano las encima.
            interval='preserveStartEnd'
            minTickGap={28}
            tick={{ fill: '#737370', fontSize: 11 }}
            stroke='#c9c9c5'
            tickLine={false}
          />
          <YAxis
            tickFormatter={axisCLP}
            tick={{ fill: '#737370', fontSize: 11 }}
            stroke='#c9c9c5'
            tickLine={false}
            width={44}
          />
          <Tooltip content={<SeriesTooltip />} cursor={{ fill: '#f5f5f3' }} />
          <Bar
            dataKey='net_clp'
            name='Venta neta'
            fill={SERIE}
            radius={[4, 4, 0, 0]}
            maxBarSize={28}
            // Sin animación de entrada: con React 19 en StrictMode la animación
            // de Recharts se queda colgada y las barras nunca llegan a pintarse.
            // Un panel de números tampoco gana nada con la entrada animada.
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
