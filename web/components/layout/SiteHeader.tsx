'use client';

import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { CartBadge } from './CartBadge';
import { AuthNav } from './AuthNav';
import { catalogHref, catalogs, store } from '@/lib/store-config';

/** Catálogo: visible en la barra desde `lg`, y también dentro del panel. */
const NAV = catalogs.map((c) => ({ href: catalogHref(c), label: c.label }));

/** Secundarias: en la barra solo desde `xl`; el resto del tiempo, en el panel. */
const NAV_EXTRA = [
  { href: '/nosotros', label: 'Nosotros' },
  { href: '/faq', label: 'Preguntas' },
  { href: '/contacto', label: 'Contacto' },
];

/**
 * Ancho en pantalla del logo para `sizes`: el alto lo fijan las clases
 * (h-8 / sm:h-10 / lg:h-11) y el ancho sale de la proporción del archivo.
 * Sin esto next/image asume el ancho real del PNG y baja la variante de 1920 px.
 */
const logoAncho = (alto: number) =>
  Math.ceil((alto * store.web.logo_width) / store.web.logo_height);
const LOGO_SIZES = `(min-width: 1024px) ${logoAncho(44)}px, (min-width: 640px) ${logoAncho(40)}px, ${logoAncho(32)}px`;

export function SiteHeader() {
  const pathname = usePathname();
  const [abierto, setAbierto] = useState(false);

  // Navegar cierra el panel (el layout no se remonta entre rutas).
  useEffect(() => setAbierto(false), [pathname]);

  // Escape cierra, como cualquier menú del sistema.
  useEffect(() => {
    if (!abierto) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setAbierto(false);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [abierto]);

  const claseEnlace = (href: string) =>
    [
      'text-sm font-medium uppercase tracking-wide transition-colors',
      pathname.startsWith(href)
        ? 'text-tierra-600 underline underline-offset-4'
        : 'text-piedra-700 hover:text-tierra-600',
    ].join(' ');

  return (
    <header className="sticky top-0 z-40 border-b border-piedra-200 bg-piedra-50/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-contenido items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-10 lg:py-4">
        <Link href="/" className="shrink-0" aria-label={`${store.name} — inicio`}>
          {/* Logo de store.json (`web.logo`). `alt` conserva el nombre para
              lectores de pantalla. */}
          <Image
            src={store.web.logo}
            alt={store.name}
            width={store.web.logo_width}
            height={store.web.logo_height}
            sizes={LOGO_SIZES}
            priority
            className="h-8 w-auto sm:h-10 lg:h-11"
          />
        </Link>

        {/* Barra de escritorio. Bajo `lg` el ancho no alcanza para los enlaces
            + sesión, así que todo eso se va al panel del botón hamburguesa. */}
        <nav aria-label="Principal" className="hidden items-center gap-6 lg:flex">
          {NAV.map(({ href, label }) => (
            <Link key={href} href={href} className={claseEnlace(href)}>
              {label}
            </Link>
          ))}
          {NAV_EXTRA.map(({ href, label }) => (
            <Link key={href} href={href} className={`hidden xl:inline ${claseEnlace(href)}`}>
              {label}
            </Link>
          ))}
          <CartBadge />
          <AuthNav />
        </nav>

        {/* En celular/tablet: solo el logo, el carrito y las 3 rayas. */}
        <div className="flex items-center gap-4 lg:hidden">
          <CartBadge />
          <button
            type="button"
            onClick={() => setAbierto((v) => !v)}
            aria-expanded={abierto}
            aria-controls="menu-movil"
            aria-label={abierto ? 'Cerrar menú' : 'Abrir menú'}
            className="-mr-1 rounded-md p-1.5 text-piedra-700 transition-colors hover:bg-piedra-100 hover:text-tierra-600"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
              className="h-7 w-7" aria-hidden="true">
              {abierto ? (
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Panel desplegable: todas las opciones, incluida la sesión. */}
      <div
        id="menu-movil"
        hidden={!abierto}
        className="border-t border-piedra-200 bg-piedra-50 lg:hidden"
      >
        <nav aria-label="Menú" className="mx-auto flex max-w-contenido flex-col px-4 py-2 sm:px-6">
          {[...NAV, ...NAV_EXTRA].map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`border-b border-piedra-100 py-3 ${claseEnlace(href)}`}
            >
              {label}
            </Link>
          ))}
          <div className="py-4">
            <AuthNav />
          </div>
        </nav>
      </div>
    </header>
  );
}
