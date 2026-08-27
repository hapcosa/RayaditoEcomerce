/**
 * Capa de datos de productos y categorías contra la API admin (`/api/admin/`).
 * Todos los endpoints requieren staff (el header JWT lo agrega apiFetch).
 *
 * Dinero en entero CLP (ver AGENTS.md): `price`/`compare_price` son number enteros.
 */
import { apiJson, apiUpload } from './client';

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

export type NewProduct = {
  name: string;
  description: string;
  price: number;
  compare_price: number;
  category: number;
  product_type: string;
  status: ProductStatus;
  is_featured: boolean;
  photo: LocalImage;
};

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

export async function createProduct(input: NewProduct): Promise<Product> {
  // Foto a calidad completa vía uploader multipart nativo (ver apiUpload).
  return apiUpload<Product>('/api/admin/products/', input.photo.uri, {
    fieldName: 'photo',
    mimeType: input.photo.mimeType,
    parameters: {
      name: input.name,
      description: input.description,
      price: String(input.price),
      compare_price: String(input.compare_price),
      category: String(input.category),
      product_type: input.product_type,
      status: input.status,
      is_featured: input.is_featured ? 'true' : 'false',
    },
  });
}

/**
 * Sube imágenes adicionales a la galería del producto (campo `images`).
 * El uploader nativo envía un archivo por request; subimos secuencialmente y
 * devolvemos la galería resultante de la última respuesta.
 */
export async function addGalleryImages(
  productId: number,
  images: LocalImage[],
): Promise<{ gallery: GalleryImage[] }> {
  let last: { gallery: GalleryImage[] } = { gallery: [] };
  for (const img of images) {
    last = await apiUpload<{ gallery: GalleryImage[] }>(
      `/api/admin/products/${productId}/images/`,
      img.uri,
      { fieldName: 'images', mimeType: img.mimeType, parameters: {} },
    );
  }
  return last;
}
