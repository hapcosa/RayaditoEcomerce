'use client';

import { useState } from 'react';
import { formatCLP } from '@/lib/format';
import type { StatsTopProduct } from '@/types/admin-stats';

/**
 * Ranking de piezas más vendidas, dibujado en SVG a mano (sin librería).
 *
 * Es el contrapunto deliberado al gráfico de Recharts: para cinco barras con
 * etiqueta directa no hace falta un motor de gráficos.
 *
 * La geometría va en porcentajes dentro de un SVG de alto fijo, no en un
 * `viewBox` escalado: así la barra se adapta a cualquier ancho sin deformar el
 * radio de las esquinas, y el texto es HTML normal — con un viewBox escalado
 * las etiquetas se encogen hasta volverse ilegibles en pantalla de teléfono.
 */

/** Alto de la barra, en píxeles. */
const BAR_HEIGHT = 14;

export function TopProductsChart({ products }: { products: StatsTopProduct[] }) {
  const [hovered, setHovered] = useState<number | null>(null);

  if (products.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-piedra-500">
        Todavía no hay piezas vendidas en este periodo.
      </p>
    );
  }

  const max = Math.max(...products.map((p) => p.net_clp));

  return (
    <ul className="space-y-4">
      {products.map((product, i) => {
        // Una barra de 0 no se ve; el mínimo de 1 % la deja insinuada.
        const share = max === 0 ? 0 : Math.max(1, (product.net_clp / max) * 100);
        const isActive = hovered === i;

        return (
          <li
            key={`${product.product_id ?? 'x'}-${i}`}
            onMouseEnter={() => setHovered(i)}
            onMouseLeave={() => setHovered(null)}
            onFocus={() => setHovered(i)}
            onBlur={() => setHovered(null)}
            tabIndex={0}
            className="rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-tierra-400"
          >
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm text-piedra-800">{product.name}</span>
              <span className="whitespace-nowrap text-sm font-medium tabular-nums lining-nums text-piedra-700">
                {formatCLP(product.net_clp)}
              </span>
            </div>
            <svg
              width="100%"
              height={BAR_HEIGHT}
              role="img"
              aria-label={`${product.name}: ${formatCLP(product.net_clp)} en ${product.units} ${
                product.units === 1 ? 'unidad' : 'unidades'
              }`}
              className="mt-1 block"
            >
              {/* Riel de fondo: da la escala sin necesidad de eje. */}
              <rect width="100%" height={BAR_HEIGHT} rx={4} fill="#f2eae0" />
              <rect
                width={`${share}%`}
                height={BAR_HEIGHT}
                rx={4}
                fill={isActive ? '#a8480e' : '#c4550f'}
              />
            </svg>
            {/* El detalle aparece bajo la barra activa en vez de flotar: así
                también sirve al toque en un teléfono. */}
            <p className="mt-1 text-xs text-piedra-500">
              {isActive
                ? `${product.units} ${product.units === 1 ? 'unidad vendida' : 'unidades vendidas'}`
                : ' '}
            </p>
          </li>
        );
      })}
    </ul>
  );
}
