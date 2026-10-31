/**
 * Capa de datos de la portada del sitio contra la API admin (`/api/admin/`).
 * Requiere staff (el header JWT lo agrega apiFetch).
 */
import { apiJson, apiUpload } from './client';
import type { LocalImage } from './products';

/**
 * Cuántas fotos muestra la portada. Lo elige la dueña entre `min_hero_photos`
 * y `max_hero_photos`, que manda el backend (`homepage.HomepageSettings`).
 */
export type HomepageSettings = {
  hero_max_photos: number;
  min_hero_photos: number;
  max_hero_photos: number;
};

export async function getHomepageSettings(): Promise<HomepageSettings> {
  return apiJson<HomepageSettings>('/api/admin/homepage-settings/');
}

/** Bajar el número archiva (no borra) las últimas fotos activas. */
export async function setHeroMaxPhotos(n: number): Promise<HomepageSettings> {
  return apiJson<HomepageSettings>('/api/admin/homepage-settings/', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hero_max_photos: n }),
  });
}

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

/**
 * Sube una foto nueva. No manda `is_active`: el backend la pone en la portada
 * si hay cupo y, si está llena, la deja archivada.
 */
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

/**
 * Reemplaza la foto de una portada existente (recorte desde el visor): conserva
 * id, posición y si está activa; solo cambia el archivo.
 */
export async function replaceHeroImage(
  id: number,
  photo: LocalImage,
): Promise<HeroImage> {
  return apiUpload<HeroImage>(
    `/api/admin/hero-images/${id}/`,
    photo.uri,
    { fieldName: 'image', mimeType: photo.mimeType, parameters: {} },
    'PATCH',
  );
}

export async function deleteHeroImage(id: number): Promise<void> {
  await apiJson<null>(`/api/admin/hero-images/${id}/`, { method: 'DELETE' });
}
