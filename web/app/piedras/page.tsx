import type { Metadata } from 'next';
import { fetchPiedrasCategories, fetchProducts } from '@/lib/api';
import { CatalogContent } from '@/components/catalog/CatalogContent';

export const metadata: Metadata = {
  title: 'Piedras',
  description:
    'Piedras lapidadas de Chiloé — ágatas, cuarzos y minerales del sur de Chile.',
};

interface SearchParams {
  search?: string;
  category_id?: string;
  min_price?: string;
  max_price?: string;
  sortBy?: string;
  order?: string;
}

export default async function PiedrasPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const { search, category_id, min_price, max_price, sortBy, order } = searchParams;

  const [products, categories] = await Promise.all([
    fetchProducts({
      product_type: 'piedra',
      search,
      category_id,
      min_price,
      max_price,
      sortBy: sortBy as 'date_created' | 'price' | 'name' | undefined,
      order: order as 'asc' | 'desc' | undefined,
    }).catch(() => []),
    fetchPiedrasCategories().catch(() => []),
  ]);

  return (
    <CatalogContent
      title="Piedras"
      subtitle="Piedras Rayadito"
      products={products}
      categories={categories}
      filters={searchParams}
      baseHref="/piedras"
    />
  );
}
