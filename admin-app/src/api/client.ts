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
import { File, UploadType } from 'expo-file-system';

import { apiUrl } from './config';
import { clearTokens, getAccess, getRefresh, saveAccess } from './tokens';

async function refreshAccess(): Promise<string | null> {
  const refresh = await getRefresh();
  if (!refresh) return null;
  const res = await fetch(`${apiUrl()}/auth/jwt/refresh`, {
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

  const res = await fetch(`${apiUrl()}${path}`, { ...options, headers });

  if (res.status === 401 && retry) {
    const newAccess = await refreshAccess();
    if (newAccess) return apiFetch(path, options, false);
    await clearTokens();
  }
  return res;
}

/** Error de la API que conserva el status y el cuerpo (para errores de validación DRF). */
export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

/**
 * Aplana los errores de validación de DRF a un mensaje legible.
 * DRF devuelve `{campo: ["msg", ...], ...}` o `{detail: "..."}`.
 */
function messageFromBody(status: number, body: unknown): string {
  if (body && typeof body === 'object') {
    const obj = body as Record<string, unknown>;
    if (typeof obj.detail === 'string') return obj.detail;
    const parts: string[] = [];
    for (const [field, val] of Object.entries(obj)) {
      const text = Array.isArray(val) ? val.join(' ') : String(val);
      parts.push(field === 'non_field_errors' ? text : `${field}: ${text}`);
    }
    if (parts.length) return parts.join('\n');
  }
  if (typeof body === 'string' && body.trim()) return body;
  return `Error ${status}`;
}

async function readBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function apiJson<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await apiFetch(path, options);
  const body = await readBody(res);
  if (!res.ok) {
    throw new ApiError(res.status, body, messageFromBody(res.status, body));
  }
  return body as T;
}

function parseBody(text: string): unknown {
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

/** Metadatos del archivo local a subir en un multipart. */
export type MultipartUpload = {
  /** Nombre del campo del archivo (p. ej. `photo` o `images`). */
  fieldName: string;
  mimeType: string;
  /** Campos de texto adicionales del form (todo como string). */
  parameters: Record<string, string>;
};

/**
 * Sube un archivo local con `multipart/form-data` usando el uploader NATIVO de
 * expo-file-system. Streamea el archivo tal cual (sin recomprimir → máxima
 * calidad) y evita el `fetch`/FormData WinterCG de Expo, que no soporta el shape
 * `{uri,name,type}` de RN ("Unsupported FormDataPart implementation").
 * Agrega el header `JWT` y reintenta una vez ante 401 (igual que apiFetch).
 */
export async function apiUpload<T>(
  path: string,
  fileUri: string,
  upload: MultipartUpload,
  method: 'POST' | 'PUT' | 'PATCH' = 'POST',
  retry = true,
): Promise<T> {
  const access = await getAccess();
  const headers: Record<string, string> = {};
  if (access) headers.Authorization = `JWT ${access}`;

  const res = await new File(fileUri).upload(`${apiUrl()}${path}`, {
    httpMethod: method,
    uploadType: UploadType.MULTIPART,
    fieldName: upload.fieldName,
    mimeType: upload.mimeType,
    parameters: upload.parameters,
    headers,
  });

  if (res.status === 401 && retry) {
    const newAccess = await refreshAccess();
    if (newAccess) return apiUpload(path, fileUri, upload, method, false);
    await clearTokens();
  }

  const body = parseBody(res.body);
  if (res.status < 200 || res.status >= 300) {
    throw new ApiError(res.status, body, messageFromBody(res.status, body));
  }
  return body as T;
}
