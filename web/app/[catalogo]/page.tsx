import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { fetchCatalogCategories, fetchProducts } from '@/lib/api';
import { CatalogContent } from '@/components/catalog/CatalogContent';
import { catalogByPath, catalogHref, catalogs, store } from '@/lib/store-config';

/**
 * Vitrina de un catálogo de store.json: /joyas y /piedras en Rayadito, /ropa en
 * un fork textil. Las rutas fijas (/carrito, /faq, …) tienen prioridad sobre
 * este segmento, y cualquier otro valor que no sea un catálogo da 404.
 */
export const dynamicParams = false;

export function generateStaticParams() {
  return catalogs.map((c) => ({ catalogo: c.path }));
}

interface Params {
  catalogo: string;
}

interface SearchParams {
  search?: string;
  category_id?: string;
  min_price?: string;
  max_price?: string;
  sortBy?: string;
  order?: string;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const catalog = catalogByPath((await params).catalogo);
  if (!catalog) return {};
  return { title: catalog.label, description: catalog.description };
}

export default async function CatalogPage({
  params,
  searchParams,
}: {
  // Next 15 entrega params y parámetros de búsqueda como promesas.
  params: Promise<Params>;
  searchParams: Promise<SearchParams>;
}) {
  const catalog = catalogByPath((await params).catalogo);
  if (!catalog) notFound();

  const filters = await searchParams;
  const { search, category_id, min_price, max_price, sortBy, order } = filters;

  const [products, categories] = await Promise.all([
    fetchProducts({
      product_type: catalog.slug,
      search,
      category_id,
      min_price,
      max_price,
      sortBy: sortBy as 'date_created' | 'price' | 'name' | undefined,
      order: order as 'asc' | 'desc' | undefined,
    }).catch(() => []),
    fetchCatalogCategories(catalog.path).catch(() => []),
  ]);

  return (
    <CatalogContent
      title={catalog.label}
      subtitle={store.name}
      products={products}
      categories={categories}
      filters={filters}
      baseHref={catalogHref(catalog)}
    />
  );
}
