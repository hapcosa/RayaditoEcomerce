import type { Category, Product, Review } from '@/types/product';
import type { HeroImage } from '@/types/homepage';
import type { HydratedCartItem, ShippingOption } from '@/types/cart';

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000/api';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
  const res = await fetch(url, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    // Server Components: revalidar cada 60 s en producción. En dev no hay caché.
    next: { revalidate: 60 },
    ...(init as RequestInit & { next?: unknown }),
  });
  if (!res.ok) throw new Error(`API ${res.status} en ${path}`);
  return res.json() as Promise<T>;
}

// ---------- Productos -------------------------------------------------------

export interface ProductListParams {
  product_type?: string;
  search?: string;
  category_id?: string | number;
  min_price?: string | number;
  max_price?: string | number;
  sortBy?: 'date_created' | 'price' | 'name';
  order?: 'asc' | 'desc';
  limit?: number;
}

export async function fetchProducts(
  params: ProductListParams = {},
): Promise<Product[]> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== '') qs.set(k, String(v));
  });
  const query = qs.toString() ? `?${qs}` : '';
  const data = await apiFetch<{ products: Product[] }>(`/products/${query}`);
  return data.products;
}

export async function fetchProduct(slug: string): Promise<Product> {
  const data = await apiFetch<{ product: Product }>(`/products/${slug}`);
  return data.product;
}

export async function fetchRelatedProducts(slug: string): Promise<Product[]> {
  const data = await apiFetch<{ related_products: Product[] }>(
    `/products/related/${slug}`,
  );
  return data.related_products;
}

// ---------- Categorías ------------------------------------------------------

export async function fetchJoyasCategories(): Promise<Category[]> {
  const data = await apiFetch<{ categories: Category[] }>(
    '/category/categories',
  );
  return data.categories;
}

export async function fetchPiedrasCategories(): Promise<Category[]> {
  const data = await apiFetch<{ categories: Category[] }>(
    '/category/piedrascategory',
  );
  return data.categories;
}

// ---------- Reseñas ---------------------------------------------------------

export async function fetchReviews(productId: number): Promise<Review[]> {
  const data = await apiFetch<{ reviews: Review[] }>(
    `/reviews/get-reviews/${productId}`,
  );
  return data.reviews;
}

// ---------- Carrito (guest, sin auth) ----------------------------------------

/**
 * Sincroniza items locales con el backend para obtener datos frescos
 * (precio actual, stock, foto). Endpoint AllowAny — no requiere auth.
 */
export async function syncCart(
  items: { product_id: number; count: number }[],
): Promise<HydratedCartItem[]> {
  const res = await fetch(`${API_BASE_URL}/cart/synch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cart_items: items }),
    cache: 'no-store',
  });
  if (!res.ok) return [];
  const data = (await res.json()) as { cart: HydratedCartItem[] };
  return data.cart;
}

// ---------- Envíos (opciones manuales, sin auth) ----------------------------

export async function fetchShippingOptions(): Promise<ShippingOption[]> {
  try {
    const data = await apiFetch<{ shipping_options: ShippingOption[] }>(
      '/shipp/get-shipping-options',
    );
    return data.shipping_options;
  } catch {
    return [];
  }
}

// ---------- Portada ---------------------------------------------------------

/**
 * Fotos de portada que el dueño administra desde la app admin.
 *
 * Si el backend no responde devuelve una lista vacía a propósito: la portada
 * tiene que seguir sirviéndose (con su fondo de respaldo) aunque la API esté
 * caída, porque es la primera página del sitio.
 */
export async function fetchHeroImages(): Promise<HeroImage[]> {
  try {
    return await apiFetch<HeroImage[]>('/homepage/hero');
  } catch {
    return [];
  }
}
