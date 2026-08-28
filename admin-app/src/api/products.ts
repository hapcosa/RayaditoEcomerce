/**
 * Capa de datos de productos y categorías contra la API admin (`/api/admin/`).
 * Todos los endpoints requieren staff (el header JWT lo agrega apiFetch).
 *
 * Dinero en entero CLP (ver AGENTS.md): `price`/`compare_price` son number enteros.
 */
import { apiFetch, apiJson, apiUpload } from './client';

export type ProductStatus = 'draft' | 'published' | 'archived';

export type GalleryImage = {
  id: number;
  product: number;
  photos: string | null;
};

export type Product = {
  id: number;
  name: string;
  slug: string;
  product_type: string;
  photo: string | null;
  description: string;
  price: number;
  compare_price: number;
  category: number;
  status: ProductStatus;
  is_featured: boolean;
  sold: boolean;
  available_stock: number;
  date_created: string;
  gallery: GalleryImage[];
};

export type Category = {
  id: number;
  name: string;
  parent: number | null;
  ProductType: string;
};

/** Imagen local elegida (cámara/galería) lista para multipart. */
export type LocalImage = {
  uri: string;
  name: string;
  mimeType: string;
};

/** Campos editables de un producto (sin la foto, que se maneja aparte). */
export type ProductFields = {
  name: string;
  description: string;
  price: number;
  compare_price: number;
  category: number;
  product_type: string;
  status: ProductStatus;
  is_featured: boolean;
};

export type NewProduct = ProductFields & { photo: LocalImage };

/** DRF pagina la lista; toleramos respuesta paginada o array plano. */
type Paginated<T> = { results: T[] };

function isPaginated<T>(data: T[] | Paginated<T>): data is Paginated<T> {
  return !Array.isArray(data) && Array.isArray((data as Paginated<T>).results);
}

export async function listProducts(): Promise<Product[]> {
  const data = await apiJson<Product[] | Paginated<Product>>('/api/admin/products/');
  return isPaginated(data) ? data.results : data;
}

export async function getCategories(): Promise<Category[]> {
  return apiJson<Category[]>('/api/admin/categories/');
}

/** Serializa los campos a strings para un form multipart (todo va como texto). */
function fieldsToParams(fields: ProductFields): Record<string, string> {
  return {
    name: fields.name,
    description: fields.description,
    price: String(fields.price),
    compare_price: String(fields.compare_price),
    category: String(fields.category),
    product_type: fields.product_type,
    status: fields.status,
    is_featured: fields.is_featured ? 'true' : 'false',
  };
}

export async function getProduct(id: number): Promise<Product> {
  return apiJson<Product>(`/api/admin/products/${id}/`);
}

export async function createProduct(input: NewProduct): Promise<Product> {
  // Foto a calidad completa vía uploader multipart nativo (ver apiUpload).
  return apiUpload<Product>('/api/admin/products/', input.photo.uri, {
    fieldName: 'photo',
    mimeType: input.photo.mimeType,
    parameters: fieldsToParams(input),
  });
}

/**
 * Actualiza los campos de un producto (PATCH). Si `photo` viene, reemplaza la
 * foto principal a calidad completa vía multipart; si no, manda PATCH JSON
 * (el backend acepta ambos parsers).
 */
export async function updateProduct(
  id: number,
  fields: ProductFields,
  photo?: LocalImage | null,
): Promise<Product> {
  const path = `/api/admin/products/${id}/`;
  if (photo) {
    return apiUpload<Product>(path, photo.uri, {
      fieldName: 'photo',
      mimeType: photo.mimeType,
      parameters: fieldsToParams(fields),
    }, 'PATCH');
  }
  return apiJson<Product>(path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields),
  });
}

export async function deleteProduct(id: number): Promise<void> {
  await apiJson<null>(`/api/admin/products/${id}/`, { method: 'DELETE' });
}

/** Borra una imagen de la galería del producto (DELETE .../images/{imageId}/). */
export async function deleteGalleryImage(
  productId: number,
  imageId: number,
): Promise<void> {
  const res = await apiFetch(
    `/api/admin/products/${productId}/images/${imageId}/`,
    { method: 'DELETE' },
  );
  if (!res.ok && res.status !== 204) {
    throw new Error(`No se pudo borrar la imagen (${res.status}).`);
  }
}

/**
 * Sube imágenes adicionales a la galería del producto (campo `images`).
 * El uploader nativo envía un archivo por request, y el backend responde solo
 * con las imágenes creadas en ESA request; subimos secuencialmente y acumulamos
 * todas para devolver el set completo de imágenes recién agregadas.
 */
export async function addGalleryImages(
  productId: number,
  images: LocalImage[],
): Promise<{ gallery: GalleryImage[] }> {
  const created: GalleryImage[] = [];
  for (const img of images) {
    const res = await apiUpload<{ gallery: GalleryImage[] }>(
      `/api/admin/products/${productId}/images/`,
      img.uri,
      { fieldName: 'images', mimeType: img.mimeType, parameters: {} },
    );
    created.push(...res.gallery);
  }
  return { gallery: created };
}
