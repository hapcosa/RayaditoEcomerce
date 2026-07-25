/**
 * Funciones de API para autenticación (djoser + simplejwt).
 * Viven bajo /auth/ (no bajo /api/), por eso usan NEXT_PUBLIC_BACKEND_URL.
 * Header de autorización: "JWT <access_token>" (no "Bearer").
 */
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://127.0.0.1:8000';

const AUTH = `${BACKEND_URL}/auth`;

export interface UserInfo {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  get_full_name: string;
}

// ---------- Login / tokens --------------------------------------------------

export async function apiLogin(
  email: string,
  password: string,
): Promise<{ access: string; refresh: string }> {
  const res = await fetch(`${AUTH}/jwt/create/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
    cache: 'no-store',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as Record<string, unknown>;
    throw new Error((err.detail as string) ?? 'Credenciales inválidas');
  }
  return res.json();
}

export async function apiRefresh(
  refresh: string,
): Promise<{ access: string }> {
  const res = await fetch(`${AUTH}/jwt/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error('Sesión expirada');
  return res.json();
}

// ---------- Registro / activación -------------------------------------------

export interface RegisterData {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  re_password: string;
}

export async function apiRegister(data: RegisterData): Promise<UserInfo> {
  const res = await fetch(`${AUTH}/users/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    cache: 'no-store',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as Record<string, unknown>;
    const msg = (Object.values(err).flat() as string[]).join(' ') || 'Error al registrar';
    throw new Error(msg);
  }
  return res.json();
}

export async function apiActivate(uid: string, token: string): Promise<void> {
  const res = await fetch(`${AUTH}/users/activation/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uid, token }),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error('Enlace inválido o ya utilizado');
}

// ---------- Datos del usuario -----------------------------------------------

export async function apiMe(access: string): Promise<UserInfo> {
  const res = await fetch(`${AUTH}/users/me/`, {
    headers: { Authorization: `JWT ${access}` },
    cache: 'no-store',
  });
  if (!res.ok) throw new Error('Sesión expirada');
  return res.json();
}

// ---------- Reset de contraseña ---------------------------------------------

export async function apiResetPassword(email: string): Promise<void> {
  // Siempre devuelve 204; nunca revelar si el email existe.
  await fetch(`${AUTH}/users/reset_password/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
    cache: 'no-store',
  });
}

export interface ResetPasswordConfirmData {
  uid: string;
  token: string;
  new_password: string;
  re_new_password: string;
}

export async function apiResetPasswordConfirm(
  data: ResetPasswordConfirmData,
): Promise<void> {
  const res = await fetch(`${AUTH}/users/reset_password_confirm/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    cache: 'no-store',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as Record<string, unknown>;
    const msg = (Object.values(err).flat() as string[]).join(' ') || 'Enlace inválido o expirado';
    throw new Error(msg);
  }
}

// ---------- Carrito backend (requiere auth) ----------------------------------

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? `${BACKEND_URL}/api`;

export async function apiGetCartItems(
  access: string,
): Promise<{ id: number; count: number; product: { id: number } }[]> {
  const res = await fetch(`${API_BASE}/cart/cart-items`, {
    headers: { Authorization: `JWT ${access}` },
    cache: 'no-store',
  });
  if (!res.ok) return [];
  const data = await res.json() as { cart: { id: number; count: number; product: { id: number } }[] };
  return data.cart;
}

export async function apiAddCartItem(
  access: string,
  productId: number,
): Promise<void> {
  await fetch(`${API_BASE}/cart/add-item`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `JWT ${access}`,
    },
    body: JSON.stringify({ product_id: productId }),
    cache: 'no-store',
  });
}
