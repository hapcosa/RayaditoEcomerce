/**
 * Capa de datos de la portada del sitio contra la API admin (`/api/admin/`).
 * Requiere staff (el header JWT lo agrega apiFetch).
 */
import { apiJson, apiUpload } from './client';
import type { LocalImage } from './products';

/** Tope de fotos activas; lo impone el backend (`HeroImage.MAX_ACTIVAS`). */
export const MAX_FOTOS_ACTIVAS = 3;

export type HeroImage = {
  id: number;
  image: string | null;
  alt_text: string;
  caption: string;
  position: number;
  is_active: boolean;
  date_created: string;
};

export async function listHeroImages(): Promise<HeroImage[]> {
  return apiJson<HeroImage[]>('/api/admin/hero-images/');
}

export async function createHeroImage(
  photo: LocalImage,
  fields: { alt_text: string; caption: string; position: number },
): Promise<HeroImage> {
  return apiUpload<HeroImage>('/api/admin/hero-images/', photo.uri, {
    fieldName: 'image',
    mimeType: photo.mimeType,
    parameters: {
      alt_text: fields.alt_text,
      caption: fields.caption,
      position: String(fields.position),
      is_active: 'true',
    },
  });
}

export async function updateHeroImage(
  id: number,
  fields: Partial<Pick<HeroImage, 'alt_text' | 'caption' | 'position' | 'is_active'>>,
): Promise<HeroImage> {
  return apiJson<HeroImage>(`/api/admin/hero-images/${id}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields),
  });
}

export async function deleteHeroImage(id: number): Promise<void> {
  await apiJson<null>(`/api/admin/hero-images/${id}/`, { method: 'DELETE' });
}
