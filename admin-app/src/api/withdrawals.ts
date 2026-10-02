/**
 * Solicitudes de retracto contra la API admin (`/api/admin/withdrawals/`).
 * Requiere staff (el header JWT lo agrega apiFetch).
 *
 * La máquina de estados vive en el backend: la app solo ofrece los botones de
 * `allowed_transitions`. El reembolso se hace en MercadoPago; marcarlo acá
 * solo deja constancia.
 */
import { apiJson } from './client';

export type WithdrawalStatus = 'received' | 'accepted' | 'refunded' | 'rejected';

export type WithdrawalOrder = {
  id: number;
  transaction_id: string | null;
  status: string;
  full_name: string | null;
  telephone_number: string;
  amount: number | null;
  shipping_price: number;
  paid_at: string | null;
  shipped_at: string | null;
  deliveryNumber: string | null;
};

export type Withdrawal = {
  id: number;
  code: string;
  status: WithdrawalStatus;
  status_display: string;
  email: string;
  reason: string;
  staff_note: string;
  created_at: string;
  resolved_at: string | null;
  order: WithdrawalOrder;
  allowed_transitions: WithdrawalStatus[];
};

/** `open` = recibidas + aceptadas (las que todavía piden algo). */
export type WithdrawalFilter = WithdrawalStatus | 'open';

type Paginated<T> = { results: T[] };

function isPaginated<T>(data: T[] | Paginated<T>): data is Paginated<T> {
  return !Array.isArray(data) && Array.isArray((data as Paginated<T>).results);
}

export async function listWithdrawals(filter?: WithdrawalFilter): Promise<Withdrawal[]> {
  const qs = filter ? `?status=${encodeURIComponent(filter)}` : '';
  const data = await apiJson<Withdrawal[] | Paginated<Withdrawal>>(
    `/api/admin/withdrawals/${qs}`,
  );
  return isPaginated(data) ? data.results : data;
}

export async function getWithdrawal(id: number): Promise<Withdrawal> {
  return apiJson<Withdrawal>(`/api/admin/withdrawals/${id}/`);
}

/** Rechazar exige `staffNote` (el backend responde 400 sin motivo). */
export async function changeWithdrawalStatus(
  id: number,
  status: WithdrawalStatus,
  staffNote?: string,
): Promise<Withdrawal> {
  const body: Record<string, string> = { status };
  if (staffNote) body.staff_note = staffNote;
  return apiJson<Withdrawal>(`/api/admin/withdrawals/${id}/status/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}
