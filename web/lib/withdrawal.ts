import { API_BASE_URL } from './api';

export interface WithdrawalInput {
  order_number: string;
  email: string;
  reason?: string;
}

export interface WithdrawalResult {
  code: string;
  created_at: string;
  already_requested: boolean;
  message: string;
}

/**
 * Solicitud de retracto de una compra.
 * Endpoint público (AllowAny, con throttle): POST /api/orders/withdrawal.
 * Pide el número de pedido y el correo de la compra; sirve también para
 * compras como invitado.
 */
export async function requestWithdrawal(input: WithdrawalInput): Promise<WithdrawalResult> {
  const res = await fetch(`${API_BASE_URL}/orders/withdrawal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
    cache: 'no-store',
  });
  let data: Record<string, unknown> = {};
  try {
    data = await res.json();
  } catch {
    /* respuesta sin cuerpo JSON */
  }
  if (!res.ok) {
    if (res.status === 429) {
      throw new Error('Demasiados intentos seguidos. Espera un minuto y vuelve a intentarlo.');
    }
    const message = typeof data.message === 'string' ? data.message : null;
    throw new Error(message ?? 'No pudimos registrar tu solicitud. Intenta de nuevo.');
  }
  return data as unknown as WithdrawalResult;
}
