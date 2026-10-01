/**
 * Publicaciones de Instagram contra la API admin (`/api/admin/instagram/`).
 *
 * La app solo programa: el backend publica desde un timer cada pocos minutos
 * (ver social/services.py), así que "Publicar ahora" sale en unos minutos y no
 * al instante. Ver social/admin_api.py.
 */
import { apiJson } from './client';

export type InstagramPostStatus =
  | 'scheduled'
  | 'publishing'
  | 'published'
  | 'failed'
  | 'cancelled';

export type InstagramPost = {
  id: number;
  product: number;
  product_name: string;
  caption: string;
  status: InstagramPostStatus;
  scheduled_for: string;
  attempts: number;
  permalink: string;
  last_error: string;
  created_at: string;
  published_at: string | null;
};

export type InstagramDraft = {
  /** False si faltan las credenciales en el servidor. */
  configured: boolean;
  /** Texto sugerido con lo que el producto tiene GUARDADO. */
  caption: string;
  photo_count: number;
  product_url: string;
  /** Solo un producto visible en la tienda se puede publicar. */
  publishable: boolean;
};

const BASE = '/api/admin/instagram/posts/';

export async function getInstagramDraft(productId: number): Promise<InstagramDraft> {
  return apiJson<InstagramDraft>(`${BASE}draft/?product=${productId}`);
}

export async function listInstagramPosts(productId: number): Promise<InstagramPost[]> {
  return apiJson<InstagramPost[]>(`${BASE}?product=${productId}`);
}

export async function scheduleInstagramPost(
  productId: number,
  caption: string,
  scheduledFor: Date | null,
): Promise<InstagramPost> {
  return apiJson<InstagramPost>(BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      product: productId,
      caption,
      scheduled_for: scheduledFor ? scheduledFor.toISOString() : null,
    }),
  });
}

/** 409 si ya no está programada (se publicó o la está publicando el servidor). */
export async function cancelInstagramPost(id: number): Promise<void> {
  await apiJson<null>(`${BASE}${id}/`, { method: 'DELETE' });
}
