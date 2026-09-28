import { API_BASE_URL } from './api';
import type { AdminStats } from '@/types/admin-stats';

/** Rangos que ofrece el selector del panel. */
export const RANGE_OPTIONS = [
  { days: 7, label: '7 días' },
  { days: 30, label: '30 días' },
  { days: 90, label: '90 días' },
  { days: 365, label: '1 año' },
] as const;

/**
 * Error de la API de stats. `status` permite distinguir los dos casos que el
 * panel trata distinto: 401 (token vencido, se intenta refresh) y 403 (la
 * cuenta existe pero no es staff, no hay nada que reintentar).
 */
export class StatsError extends Error {
  status: number;

  constructor(status: number) {
    super(`admin stats ${status}`);
    this.name = 'StatsError';
    this.status = status;
  }
}

/** GET /api/admin/stats/?days=N — requiere un token de cuenta staff. */
export async function fetchAdminStats(
  access: string,
  days: number,
): Promise<AdminStats> {
  const res = await fetch(`${API_BASE_URL}/admin/stats/?days=${days}`, {
    headers: { 'Content-Type': 'application/json', Authorization: `JWT ${access}` },
    cache: 'no-store',
  });
  if (!res.ok) throw new StatsError(res.status);
  return res.json() as Promise<AdminStats>;
}

/**
 * Variación porcentual contra el periodo anterior.
 *
 * Devuelve `null` cuando el periodo anterior fue cero: "subió infinito" no es
 * un dato útil, así que la tarjeta muestra un guion en vez de un número.
 */
export function deltaPercent(current: number, previous: number): number | null {
  if (previous === 0) return null;
  return Math.round(((current - previous) / previous) * 100);
}

/** Fecha corta para el eje temporal: "12 mar". */
export function shortDate(iso: string): string {
  // El backend manda `YYYY-MM-DD`; se parsea a mano para que no lo corra la
  // zona horaria (new Date('2026-03-12') es medianoche UTC).
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('es-CL', {
    day: 'numeric',
    month: 'short',
  });
}

/** Fecha con día y mes largos: "12 de marzo". */
export function longDate(iso: string): string {
  const [year, month, day] = iso.split('-').map(Number);
  return new Date(year, month - 1, day).toLocaleDateString('es-CL', {
    day: 'numeric',
    month: 'long',
  });
}

/** Antigüedad en horas de un ISO datetime, redondeada hacia abajo. */
export function hoursSince(iso: string): number {
  return Math.floor((Date.now() - new Date(iso).getTime()) / 3_600_000);
}
