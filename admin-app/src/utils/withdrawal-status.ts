/** Etiquetas es-CL y colores para los estados de una solicitud de retracto. */
import type { WithdrawalStatus } from '@/api/withdrawals';

export const WITHDRAWAL_STATUS_LABEL: Record<WithdrawalStatus, string> = {
  received: 'Recibida',
  accepted: 'Aceptada',
  refunded: 'Reembolsada',
  rejected: 'Rechazada',
};

/** Mismos tonos tierra/piedra que los estados de pedido. */
export const WITHDRAWAL_STATUS_COLOR: Record<WithdrawalStatus, string> = {
  received: '#B08968', // arena: pendiente de revisar
  accepted: '#7D8471', // salvia
  refunded: '#5B7B7A', // ágata
  rejected: '#A15C4A', // óxido
};

/** Días enteros desde una fecha ISO hasta hoy, o null si no hay fecha. */
export function daysSince(iso: string | null): number | null {
  if (!iso) return null;
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
}
