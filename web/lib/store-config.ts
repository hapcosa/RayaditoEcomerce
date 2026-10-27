/**
 * Identidad de la tienda y sus catálogos, desde `store.json` (raíz del repo).
 *
 * Es el mismo archivo que lee Django (`settings.STORE`): un fork cambia ahí el
 * nombre, los textos de marca y los catálogos públicos, y la tienda los sigue
 * sin tocar componentes. Los colores viven en `app/theme.css` y los textos
 * largos (portada, nosotros, FAQ) en `content/`.
 */
import storeJson from '../../store.json';

export interface Catalog {
  /** Valor de `Product.product_type` (ej. "joya"). */
  slug: string;
  /** Segmento de URL de la vitrina (ej. "joyas" → /joyas). */
  path: string;
  /** Nombre en plural para menús y títulos (ej. "Joyas"). */
  label: string;
  singular: string;
  /** `Category.ProductType` de las categorías de este catálogo. */
  category_type: string;
  description: string;
  /** Rótulo de una pieza en la imagen OG (ej. "Joya artesanal"). */
  item_label?: string;
}

export interface Store {
  slug: string;
  name: string;
  short_name: string;
  tagline: string;
  description: string;
  domain: string;
  catalogs: Catalog[];
  web: {
    title: string;
    description: string;
    location: string;
    logo: string;
    /** Tamaño real del logo en px: next/image lo usa para la proporción. */
    logo_width: number;
    logo_height: number;
    og_footer: string;
    contact: { email: string; instagram_url: string; whatsapp_url: string };
  };
}

export const store: Store = storeJson;

export const catalogs: Catalog[] = store.catalogs;

/** El primer catálogo es el principal: destino de "Ver todo" y "Explorar". */
export const primaryCatalog: Catalog = catalogs[0];

export function catalogHref(catalog: Catalog): string {
  return `/${catalog.path}`;
}

export function catalogByPath(path: string): Catalog | undefined {
  return catalogs.find((c) => c.path === path);
}

export function catalogBySlug(slug: string): Catalog | undefined {
  return catalogs.find((c) => c.slug === slug);
}

/**
 * Contacto y redes. Una variable de entorno, si está definida, gana sobre
 * store.json (también vacía: así se oculta un enlace sin tocar el archivo).
 */
export const contact = {
  email: process.env.NEXT_PUBLIC_CONTACT_EMAIL ?? store.web.contact.email,
  instagramUrl: process.env.NEXT_PUBLIC_INSTAGRAM_URL ?? store.web.contact.instagram_url,
  whatsappUrl: process.env.NEXT_PUBLIC_WHATSAPP_URL ?? store.web.contact.whatsapp_url,
};

/** Prefijo de las claves de localStorage (carrito, sesión) de esta tienda. */
export function storageKey(name: string): string {
  return `${store.slug}-${name}`;
}
