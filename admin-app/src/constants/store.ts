/**
 * Tienda y catálogos, desde el `store.json` del repo.
 *
 * `app.config.js` lo copia a `expo.extra.store` al compilar: el APK trae los
 * catálogos de su tienda (Rayadito: joya y piedra; un fork textil: ropa) sin
 * pedirlos a la red. Agregar un catálogo exige un APK nuevo, igual que
 * cualquier otro cambio de la app.
 */
import Constants from 'expo-constants';

export type StoreCatalog = {
  /** Valor de `product_type` que acepta la API admin. */
  slug: string;
  /** Segmento de la vitrina en el sitio (ej. "joyas" → /joyas). */
  path: string;
  label: string;
  singular: string;
  /** `Category.ProductType` de las categorías de este catálogo. */
  category_type: string;
};

export type StoreConfig = {
  slug: string;
  name: string;
  short_name: string;
  domain: string;
  catalogs: StoreCatalog[];
};

const extra = Constants.expoConfig?.extra as { store?: StoreConfig } | undefined;
if (!extra?.store) {
  throw new Error('Falta expo.extra.store: la app debe arrancar con app.config.js.');
}

export const store: StoreConfig = extra.store;
export const catalogs: StoreCatalog[] = store.catalogs;
export const primaryCatalog: StoreCatalog = catalogs[0];

/** "/joyas o /piedras", para textos de ayuda. */
export function catalogPathsText(): string {
  const paths = catalogs.map((c) => `/${c.path}`);
  return paths.length > 1 ? `${paths.slice(0, -1).join(', ')} o ${paths.at(-1)}` : paths[0];
}

/** "joya o piedra", para mensajes de validación. */
export function catalogSingularsText(): string {
  const names = catalogs.map((c) => c.singular.toLowerCase());
  return names.length > 1 ? `${names.slice(0, -1).join(', ')} o ${names.at(-1)}` : names[0];
}
