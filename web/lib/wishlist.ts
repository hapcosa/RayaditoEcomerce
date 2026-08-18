import { API_BASE_URL } from './api';
import type { Product } from '@/types/product';

function authHeaders(access: string) {
  return { 'Content-Type': 'application/json', Authorization: `JWT ${access}` };
}

export interface WishlistItem {
  id: number;
  product: Product;
  created_at: string;
}

/** GET /api/wishlist/list — ítems del usuario autenticado. */
export async function fetchWishlist(access: string): Promise<WishlistItem[]> {
  const res = await fetch(`${API_BASE_URL}/wishlist/list`, {
    headers: authHeaders(access),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`wishlist ${res.status}`);
  const data = (await res.json()) as { wishlist: WishlistItem[] };
  return data.wishlist;
}

/** POST /api/wishlist/add — agrega un producto (idempotente). */
export async function addToWishlist(
  access: string,
  productId: number,
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/wishlist/add`, {
    method: 'POST',
    headers: authHeaders(access),
    body: JSON.stringify({ product_id: productId }),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`wishlist add ${res.status}`);
}

/** DELETE /api/wishlist/remove/:productId — quita un producto. */
export async function removeFromWishlist(
  access: string,
  productId: number,
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/wishlist/remove/${productId}`, {
    method: 'DELETE',
    headers: authHeaders(access),
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`wishlist remove ${res.status}`);
}
