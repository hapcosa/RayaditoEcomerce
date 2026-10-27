import type { MetadataRoute } from 'next';
import { fetchProducts } from '@/lib/api';
import { absoluteUrl } from '@/lib/site';
import { catalogHref, catalogs } from '@/lib/store-config';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();

  const staticEntries: MetadataRoute.Sitemap = [
    { url: absoluteUrl('/'), lastModified: now, changeFrequency: 'weekly', priority: 1 },
    ...catalogs.map((c) => ({
      url: absoluteUrl(catalogHref(c)),
      lastModified: now,
      changeFrequency: 'weekly' as const,
      priority: 0.9,
    })),
    { url: absoluteUrl('/nosotros'), lastModified: now, changeFrequency: 'monthly', priority: 0.5 },
    { url: absoluteUrl('/faq'), lastModified: now, changeFrequency: 'monthly', priority: 0.5 },
    { url: absoluteUrl('/contacto'), lastModified: now, changeFrequency: 'yearly', priority: 0.4 },
  ];

  // Fichas de producto. Si la API no responde, degradamos a solo estáticas.
  let productEntries: MetadataRoute.Sitemap = [];
  try {
    const products = await fetchProducts({ limit: 1000 });
    productEntries = products
      .filter((p) => p.slug && p.status === 'published')
      .map((p) => ({
        url: absoluteUrl(`/productos/${p.slug}`),
        lastModified: p.date_created ? new Date(p.date_created) : now,
        changeFrequency: 'weekly' as const,
        priority: 0.7,
      }));
  } catch {
    productEntries = [];
  }

  return [...staticEntries, ...productEntries];
}
