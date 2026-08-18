import Link from 'next/link';
import { fetchProducts } from '@/lib/api';
import { ProductCard } from '@/components/ui/ProductCard';

// Revalida la portada cada 5 min (los "últimos productos" no cambian a cada instante).
export const revalidate = 300;

export default async function HomePage() {
  const latest = await fetchProducts({
    sortBy: 'date_created',
    order: 'desc',
    limit: 8,
  }).catch(() => []);

  return (
    <div className="min-h-screen">
      {/* ── Hero ──────────────────────────────────────────────────────────
          Fondo "ágata rayada" hecho con gradientes CSS (autocontenido, sin
          assets externos). Para usar una foto real del taller/producto,
          reemplazá el `backgroundImage` de este div por `url('/hero.jpg')`
          (dejar el overlay claro para legibilidad del texto). */}
      <section className="relative overflow-hidden">
        <div
          aria-hidden
          className="absolute inset-0"
          style={{
            backgroundImage: [
              // Bandas diagonales tipo veta de ágata.
              'repeating-linear-gradient(115deg,' +
                ' rgba(232,198,176,0.55) 0px, rgba(232,198,176,0.55) 22px,' +
                ' rgba(244,219,160,0.45) 22px, rgba(244,219,160,0.45) 40px,' +
                ' rgba(216,162,132,0.40) 40px, rgba(216,162,132,0.40) 64px,' +
                ' rgba(250,249,246,0.60) 64px, rgba(250,249,246,0.60) 92px)',
              // Luz cálida superior derecha.
              'radial-gradient(120% 90% at 80% 0%, rgba(203,135,47,0.30), transparent 60%)',
              // Base clara para legibilidad.
              'linear-gradient(180deg, rgba(250,249,246,0.10), rgba(250,249,246,0.85))',
            ].join(','),
          }}
        />

        <div className="relative mx-auto flex max-w-prosa flex-col items-center gap-8 px-6 py-28 text-center sm:py-36">
          <p className="font-manuscrita text-2xl text-tierra-700">desde Chiloé</p>

          <h1 className="text-balance font-serif text-5xl font-medium leading-tight text-piedra-900 drop-shadow-sm sm:text-7xl">
            Piedras Rayadito
          </h1>

          <p className="max-w-prosa text-lg leading-relaxed text-piedra-800">
            Joyería y lapidación de piedras del sur de Chile. Cada pieza es única,
            trabajada a mano con ágatas y minerales recogidos en las playas de la
            isla.
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
      </section>

      {/* ── Últimos productos ─────────────────────────────────────────────── */}
      {latest.length > 0 && (
        <section className="mx-auto max-w-6xl px-6 py-16 sm:py-20">
          <div className="mb-8 flex items-end justify-between gap-4">
            <div>
              <p className="font-manuscrita text-xl text-tierra-600">
                recién salidas del taller
              </p>
              <h2 className="font-serif text-3xl font-medium text-piedra-900">
                Últimos productos
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
