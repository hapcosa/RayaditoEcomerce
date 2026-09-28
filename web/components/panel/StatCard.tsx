import { deltaPercent } from '@/lib/admin-stats';

interface StatCardProps {
  /** Qué mide la tarjeta. */
  label: string;
  /** Valor ya formateado (CLP o unidades). */
  value: string;
  /** Valor crudo del periodo actual y del anterior, para la variación. */
  current: number;
  previous: number;
  /** Rango del periodo anterior, para el texto de referencia. */
  previousLabel: string;
}

/**
 * Tarjeta numérica con su variación contra el periodo anterior.
 *
 * El signo se dice con texto ("+12 %" / "−8 %") además del color: el color por
 * sí solo no comunica nada a quien no lo distingue.
 */
export function StatCard({
  label,
  value,
  current,
  previous,
  previousLabel,
}: StatCardProps) {
  const delta = deltaPercent(current, previous);

  return (
    <div className="rounded-xl border border-piedra-200 bg-white p-5">
      <p className="text-xs uppercase tracking-wide text-piedra-500">{label}</p>
      {/* `lining-nums` + `tabular-nums`: la serif del sitio usa cifras de estilo
          antiguo, donde el 1 se confunde con una I. En un número que se lee de
          un vistazo eso no sirve. */}
      <p className="mt-2 font-serif text-3xl font-medium tabular-nums lining-nums text-piedra-900">
        {value}
      </p>
      <p className="mt-2 text-xs text-piedra-500">
        {delta === null ? (
          <span>sin datos en {previousLabel}</span>
        ) : (
          <>
            <span
              className={
                delta > 0
                  ? 'font-medium text-tierra-700'
                  : delta < 0
                    ? 'font-medium text-piedra-700'
                    : 'font-medium text-piedra-500'
              }
            >
              {delta > 0 ? '▲ +' : delta < 0 ? '▼ −' : ''}
              {Math.abs(delta)} %
            </span>{' '}
            vs. {previousLabel}
          </>
        )}
      </p>
    </div>
  );
}
