import type { Metadata } from 'next';
import { Cormorant_Garamond, Inter, Caveat } from 'next/font/google';
import { SiteHeader } from '@/components/layout/SiteHeader';
import { SiteFooter } from '@/components/layout/SiteFooter';
import { AuthProvider } from '@/components/providers/AuthProvider';
import { JsonLd } from '@/components/seo/JsonLd';
import { SITE_URL } from '@/lib/site';
import './globals.css';

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
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000'),
  title: {
    default: 'Piedras Rayadito — Joyería y lapidación de piedras de Chiloé',
    template: '%s · Piedras Rayadito',
  },
  description:
    'Joyería artesanal y lapidación de piedras de Chiloé. Piezas únicas hechas a mano en el sur de Chile.',
  openGraph: {
    type: 'website',
    locale: 'es_CL',
    siteName: 'Piedras Rayadito',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const organizationJsonLd: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Piedras Rayadito',
    url: SITE_URL,
    description:
      'Joyería artesanal y lapidación de piedras de Chiloé. Piezas únicas hechas a mano en el sur de Chile.',
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
