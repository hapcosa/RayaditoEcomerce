/**
 * Cliente HTTP de la API DRF.
 *
 * OJO: djoser + simplejwt usan el header `Authorization: JWT <access>`
 * (NO `Bearer`). Ver core/settings.py -> SIMPLE_JWT.AUTH_HEADER_TYPES.
 *
 * `apiFetch` agrega el access token y, ante un 401, intenta refrescar una vez
 * con el refresh token antes de reintentar. No fuerza Content-Type para poder
 * enviar FormData (multipart) en subida de imágenes.
 */
import { API_URL } from './config';
import { clearTokens, getAccess, getRefresh, saveAccess } from './tokens';

async function refreshAccess(): Promise<string | null> {
  const refresh = await getRefresh();
  if (!refresh) return null;
  const res = await fetch(`${API_URL}/auth/jwt/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { access?: string };
  if (!data.access) return null;
  await saveAccess(data.access);
  return data.access;
}

export async function apiFetch(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<Response> {
  const access = await getAccess();
  const headers = new Headers(options.headers);
  if (access) headers.set('Authorization', `JWT ${access}`);

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401 && retry) {
    const newAccess = await refreshAccess();
    if (newAccess) return apiFetch(path, options, false);
    await clearTokens();
  }
  return res;
}

export async function apiJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await apiFetch(path, options);
  if (!res.ok) {
    throw new Error(`API ${res.status} en ${path}`);
  }
  return (await res.json()) as T;
}
