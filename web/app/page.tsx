import Link from 'next/link';
import { fetchHeroImages, fetchProducts } from '@/lib/api';
import { HeroMosaic } from '@/components/home/HeroMosaic';
import { ProductCard } from '@/components/ui/ProductCard';

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
              // Bandas suaves: son fondo, no deben competir con las fotos.
              'repeating-linear-gradient(115deg,' +
                ' rgb(var(--color-agata-200) / 0.28) 0px, rgb(var(--color-agata-200) / 0.28) 22px,' +
                ' rgb(var(--color-agata-100) / 0.22) 22px, rgb(var(--color-agata-100) / 0.22) 40px,' +
                ' rgb(var(--color-piedra-200) / 0.20) 40px, rgb(var(--color-piedra-200) / 0.20) 64px,' +
                ' rgb(var(--color-piedra-50) / 0.60) 64px, rgb(var(--color-piedra-50) / 0.60) 92px)',
              // Luz cálida superior derecha, con el naranjo del logo.
              'radial-gradient(120% 90% at 80% 0%, rgb(var(--color-tierra-400) / 0.16), transparent 60%)',
              // Base clara para legibilidad.
              'linear-gradient(180deg, rgb(var(--color-piedra-50) / 0.20), rgb(var(--color-piedra-50) / 0.90))',
            ].join(','),
          }}
        />

        <div
          className={`relative mx-auto max-w-6xl px-6 ${
            hero.length > 0 ? 'py-16 sm:py-20' : 'py-28 sm:py-36'
          }`}
        >
          <div className="mx-auto flex max-w-prosa flex-col items-center gap-6 text-center">
            <p className="font-manuscrita text-2xl text-tierra-700">desde Chiloé</p>

            <h1 className="text-balance font-serif text-5xl font-medium leading-tight text-piedra-900 drop-shadow-sm sm:text-7xl">
              Piedras Rayadito
            </h1>

            <p className="max-w-prosa text-lg leading-relaxed text-piedra-800">
              Joyería y lapidación de piedras del sur de Chile. Cada pieza es
              única, trabajada a mano con ágatas y minerales recogidos en las
              playas de la isla.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/joyas"
                className="rounded-full bg-tierra-500 px-7 py-3 text-sm font-medium uppercase tracking-wide text-piedra-50 shadow-sm transition-colors hover:bg-tierra-600"
              >
                Ver joyas
              </Link>
              <Link
                href="/piedras"
                className="rounded-full border border-piedra-400 bg-piedra-50/70 px-7 py-3 text-sm font-medium uppercase tracking-wide text-piedra-800 backdrop-blur-sm transition-colors hover:border-agata-500 hover:text-agata-600"
              >
                Piedras
              </Link>
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
        <section className="mx-auto max-w-6xl px-6 py-16 sm:py-20">
          <div className="mb-8 flex items-end justify-between gap-4">
            <div>
              <p className="font-manuscrita text-xl text-tierra-600">
                recién salidas del taller
              </p>
              <h2 className="font-serif text-3xl font-medium text-piedra-900">
                Últimas creaciones
              </h2>
            </div>
            <Link
              href="/joyas"
              className="hidden shrink-0 text-sm font-medium uppercase tracking-wide text-tierra-600 hover:text-tierra-700 sm:inline"
            >
              Ver todo →
            </Link>
          </div>

          <ul className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
            {latest.map((product) => (
              <li key={product.id}>
                <ProductCard product={product} />
              </li>
            ))}
          </ul>

          <div className="mt-8 text-center sm:hidden">
            <Link
              href="/joyas"
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
