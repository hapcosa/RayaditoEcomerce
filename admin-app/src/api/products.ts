/**
 * Capa de datos de productos y categorías contra la API admin (`/api/admin/`).
 * Todos los endpoints requieren staff (el header JWT lo agrega apiFetch).
 *
 * Dinero en entero CLP (ver AGENTS.md): `price`/`compare_price` son number enteros.
 */
import { apiJson } from './client';

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

function imagePart(img: LocalImage) {
  // RN FormData acepta este shape para archivos; el cast evita el tipado web-only.
  return { uri: img.uri, name: img.name, type: img.mimeType } as unknown as Blob;
}

export async function createProduct(input: NewProduct): Promise<Product> {
  const form = new FormData();
  form.append('name', input.name);
  form.append('description', input.description);
  form.append('price', String(input.price));
  form.append('compare_price', String(input.compare_price));
  form.append('category', String(input.category));
  form.append('product_type', input.product_type);
  form.append('status', input.status);
  form.append('is_featured', input.is_featured ? 'true' : 'false');
  form.append('photo', imagePart(input.photo));

  return apiJson<Product>('/api/admin/products/', { method: 'POST', body: form });
}

/** Sube imágenes adicionales a la galería del producto (campo `images`). */
export async function addGalleryImages(
  productId: number,
  images: LocalImage[],
): Promise<{ gallery: GalleryImage[] }> {
  const form = new FormData();
  for (const img of images) form.append('images', imagePart(img));
  return apiJson<{ gallery: GalleryImage[] }>(
    `/api/admin/products/${productId}/images/`,
    { method: 'POST', body: form },
  );
}
