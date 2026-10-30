import type { Metadata } from 'next';
import { Cormorant_Garamond, Inter, Caveat } from 'next/font/google';
import { SiteHeader } from '@/components/layout/SiteHeader';
import { SiteFooter } from '@/components/layout/SiteFooter';
import { AuthProvider } from '@/components/providers/AuthProvider';
import { JsonLd } from '@/components/seo/JsonLd';
import { SITE_URL } from '@/lib/site';
import './theme.css';
import './globals.css';
import { store } from '@/lib/store-config';

// Serif editorial para títulos, sans legible para texto, manuscrita para acentos.
const serif = Cormorant_Garamond({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-serif',
  display: 'swap',
});

const sans = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

const manuscrita = Caveat({
  subsets: ['latin'],
  weight: ['400', '600'],
  variable: '--font-manuscrita',
  display: 'swap',
  // Solo acentos (eyebrows, footer, ✦): no se precarga para no competir con la
  // imagen principal y el texto, que son los que definen FCP/LCP.
  preload: false,
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000'),
  title: {
    default: store.web.title,
    template: `%s · ${store.name}`,
  },
  description: store.web.description,
  openGraph: {
    type: 'website',
    locale: 'es_CL',
    siteName: store.name,
  },
};
// Los iconos y la og-image por defecto salen de las convenciones de archivo del
// App Router: app/icon.png, app/apple-icon.png y app/opengraph-image.png.

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const organizationJsonLd: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: store.name,
    url: SITE_URL,
    description: store.web.description,
  };

  return (
    <html lang="es-CL" className={`${serif.variable} ${sans.variable} ${manuscrita.variable}`}>
      <body>
        <JsonLd data={organizationJsonLd} />
        <a href="#contenido" className="skip-link">
          Saltar al contenido
        </a>
        <AuthProvider>
          <SiteHeader />
          <main id="contenido">{children}</main>
          <SiteFooter />
        </AuthProvider>
      </body>
    </html>
  );
}
