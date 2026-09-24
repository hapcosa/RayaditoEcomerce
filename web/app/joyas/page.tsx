import type { Metadata } from 'next';
import { fetchJoyasCategories, fetchProducts } from '@/lib/api';
import { CatalogContent } from '@/components/catalog/CatalogContent';

export const metadata: Metadata = {
  title: 'Joyas',
  description:
    'Joyas artesanales de piedras de Chiloé — pulseras, collares, aros y más, hechos a mano.',
};

interface SearchParams {
  search?: string;
  category_id?: string;
  min_price?: string;
  max_price?: string;
  sortBy?: string;
  order?: string;
}

export default async function JoyasPage({
  searchParams,
}: {
  // Next 15 entrega los parámetros de búsqueda como promesa.
  searchParams: Promise<SearchParams>;
}) {
  const filters = await searchParams;
  const { search, category_id, min_price, max_price, sortBy, order } = filters;

  const [products, categories] = await Promise.all([
    fetchProducts({
      product_type: 'joya',
      search,
      category_id,
      min_price,
      max_price,
      sortBy: sortBy as 'date_created' | 'price' | 'name' | undefined,
      order: order as 'asc' | 'desc' | undefined,
    }).catch(() => []),
    fetchJoyasCategories().catch(() => []),
  ]);

  return (
    <CatalogContent
      title="Joyas"
      subtitle="Piedras Rayadito"
      products={products}
      categories={categories}
      filters={filters}
      baseHref="/joyas"
    />
  );
}
