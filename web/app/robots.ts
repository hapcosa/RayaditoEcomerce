import type { MetadataRoute } from 'next';
import { absoluteUrl } from '@/lib/site';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      // Rutas privadas o transaccionales: no aportan a SEO y no deben indexarse.
      disallow: ['/dashboard', '/auth', '/checkout', '/carrito', '/wishlist', '/api'],
    },
    sitemap: absoluteUrl('/sitemap.xml'),
    host: absoluteUrl('/'),
  };
}
