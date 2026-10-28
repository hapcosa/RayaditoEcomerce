import Link from 'next/link';
import { fetchHeroImages, fetchProducts } from '@/lib/api';
import { HeroMosaic } from '@/components/home/HeroMosaic';
import { ProductCard } from '@/components/ui/ProductCard';
import { home } from '@/content/home';
import { catalogHref, catalogs, primaryCatalog, store } from '@/lib/store-config';

// Revalida la portada cada 5 min (ni las fotos de portada ni las últimas
// creaciones cambian a cada instante).
export const revalidate = 300;

export default async function HomePage() {
  const [hero, latest] = await Promise.all([
    fetchHeroImages(),
    fetchProducts({ sortBy: 'date_created', order: 'desc', limit: 8 }).catch(
      () => [],
    ),
  ]);

  return (
    <div className="min-h-screen">
      {/* ── Portada ───────────────────────────────────────────────────────
          Las fotos las sube el dueño desde la app admin (hasta 3, ver
          `homepage.HeroImage`). El fondo de gradientes queda debajo y hace de
          respaldo mientras no haya ninguna foto cargada. */}
      <section className="relative overflow-hidden">
        <div
          aria-hidden
          className="absolute inset-0"
          style={{
            backgroundImage: [
              // Luz cálida superior derecha, con el naranjo del logo.
              'radial-gradient(120% 90% at 80% 0%, rgb(var(--color-tierra-400) / 0.18), transparent 62%)',
              // Contraluz frío abajo a la izquierda: da profundidad sin dibujar
              // ningún patrón (las rayas diagonales se sacaron a pedido).
              'radial-gradient(90% 70% at 0% 100%, rgb(var(--color-agata-200) / 0.30), transparent 65%)',
              // Base clara para legibilidad.
              'linear-gradient(180deg, rgb(var(--color-piedra-100) / 0.70), rgb(var(--color-piedra-50) / 0.95))',
            ].join(','),
          }}
        />

        <div
          className={`relative mx-auto max-w-contenido px-4 sm:px-6 lg:px-10 ${
            hero.length > 0 ? 'py-16 sm:py-20' : 'py-28 sm:py-36'
          }`}
        >
          <div className="mx-auto flex max-w-prosa flex-col items-center gap-6 text-center">
            <p className="font-manuscrita text-2xl text-tierra-700">{home.eyebrow}</p>

            <h1 className="text-balance font-serif text-5xl font-medium leading-tight text-piedra-900 drop-shadow-sm sm:text-7xl">
              {store.name}
            </h1>

            <p className="max-w-prosa text-lg leading-relaxed text-piedra-800">
              {home.intro}
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                href={catalogHref(primaryCatalog)}
                className="rounded-full bg-tierra-500 px-7 py-3 text-sm font-medium uppercase tracking-wide text-piedra-50 shadow-sm transition-colors hover:bg-tierra-600"
              >
                Ver {primaryCatalog.label.toLowerCase()}
              </Link>
              {catalogs.slice(1).map((c) => (
                <Link
                  key={c.path}
                  href={catalogHref(c)}
                  className="rounded-full border border-piedra-400 bg-piedra-50/70 px-7 py-3 text-sm font-medium uppercase tracking-wide text-piedra-800 backdrop-blur-sm transition-colors hover:border-agata-500 hover:text-agata-600"
                >
                  {c.label}
                </Link>
              ))}
            </div>
          </div>

          {hero.length > 0 && (
            <div className="mt-14">
              <HeroMosaic images={hero} />
            </div>
          )}
        </div>
      </section>

      {/* ── Últimas creaciones ─────────────────────────────────────────────
          Van debajo de la portada, que es donde el dueño quiere que aparezca
          lo que va subiendo. */}
      {latest.length > 0 && (
        <section className="mx-auto max-w-contenido px-4 sm:px-6 lg:px-10 py-16 sm:py-20">
          <div className="mb-8 flex items-end justify-between gap-4">
            <div>
              <p className="font-manuscrita text-xl text-tierra-600">
                {home.latestEyebrow}
              </p>
              <h2 className="font-serif text-3xl font-medium text-piedra-900">
                {home.latestTitle}
              </h2>
            </div>
            <Link
              href={catalogHref(primaryCatalog)}
              className="hidden shrink-0 text-sm font-medium uppercase tracking-wide text-tierra-600 hover:text-tierra-700 sm:inline"
            >
              Ver todo →
            </Link>
          </div>

          <ul className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {latest.map((product) => (
              <li key={product.id}>
                {/* 2/3/4/5 columnas: en movil cada tarjeta es media pantalla. */}
                <ProductCard
                  product={product}
                  sizes="(min-width: 1280px) 18vw, (min-width: 1024px) 23vw, (min-width: 640px) 31vw, 48vw"
                />
              </li>
            ))}
          </ul>

          <div className="mt-8 text-center sm:hidden">
            <Link
              href={catalogHref(primaryCatalog)}
              className="text-sm font-medium uppercase tracking-wide text-tierra-600 hover:text-tierra-700"
            >
              Ver todo →
            </Link>
          </div>
        </section>
      )}
    </div>
  );
}
