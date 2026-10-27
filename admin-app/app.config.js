/**
 * Config dinámica de Expo: toma app.json tal cual y le suma la tienda.
 *
 * Lee `store.json` de la raíz del repo (el mismo que usan Django y la tienda
 * Next.js) al compilar o arrancar Metro, y lo deja en `expo.extra.store`. La
 * app lo lee con expo-constants (ver src/constants/store.ts): catálogos para
 * el tipo de producto, nombre de la tienda y dominio por defecto de la API.
 *
 * Nombre visible, paquete Android, esquema e íconos siguen en app.json: son la
 * identidad nativa del APK y un fork los cambia ahí (ver docs/FORK.md).
 */
const fs = require('fs');
const path = require('path');

const STORE_PATH = path.join(__dirname, '..', 'store.json');

function readStore() {
  if (!fs.existsSync(STORE_PATH)) {
    throw new Error(`No existe ${STORE_PATH}: la app admin necesita el store.json del repo.`);
  }
  const store = JSON.parse(fs.readFileSync(STORE_PATH, 'utf8'));
  // Solo lo que usa la app; el resto (textos web, correos) no va en el bundle.
  return {
    slug: store.slug,
    name: store.name,
    short_name: store.short_name,
    domain: store.domain,
    catalogs: store.catalogs.map(({ slug, path: catalogPath, label, singular, category_type }) => ({
      slug,
      path: catalogPath,
      label,
      singular,
      category_type,
    })),
  };
}

module.exports = ({ config }) => ({
  ...config,
  extra: { ...config.extra, store: readStore() },
});
