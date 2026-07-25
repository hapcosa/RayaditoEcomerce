import Link from 'next/link';
import type { Category, Product } from '@/types/product';
import { ProductCard } from '@/components/ui/ProductCard';

interface CatalogContentProps {
  title: string;
  subtitle: string;
  products: Product[];
  categories: Category[];
  /** Valores actuales de filtros (vienen de searchParams). */
  filters: {
    search?: string;
    category_id?: string;
    min_price?: string;
    max_price?: string;
    sortBy?: string;
    order?: string;
  };
  baseHref: string;
}

export function CatalogContent({
  title,
  subtitle,
  products,
  categories,
  filters,
  baseHref,
}: CatalogContentProps) {
  const { search, category_id, min_price, max_price, sortBy, order } = filters;

  // Construye la URL de filtro manteniendo los params existentes.
  function filterHref(overrides: Record<string, string | undefined>): string {
    const merged = { search, category_id, min_price, max_price, sortBy, order, ...overrides };
    const qs = new URLSearchParams();
    Object.entries(merged).forEach(([k, v]) => {
      if (v) qs.set(k, v);
    });
    const str = qs.toString();
    return str ? `${baseHref}?${str}` : baseHref;
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      {/* Encabezado */}
      <div className="mb-10">
        <p className="font-manuscrita text-xl text-tierra-600">{subtitle}</p>
        <h1 className="mt-1 font-serif text-4xl font-medium text-piedra-900">{title}</h1>
      </div>

      <div className="flex flex-col gap-8 lg:flex-row lg:items-start">
        {/* Barra lateral de filtros */}
        <aside className="w-full shrink-0 lg:w-56">
          <form method="GET" action={baseHref} className="flex flex-col gap-5">
            {/* Búsqueda */}
            <div>
              <label
                htmlFor="search"
                className="mb-1 block text-xs font-semibold uppercase tracking-wide text-piedra-600"
              >
                Buscar
              </label>
              <input
                id="search"
                name="search"
                type="search"
                defaultValue={search}
                placeholder="Nombre o descripción…"
                className="w-full rounded-lg border border-piedra-200 bg-white px-3 py-2 text-sm text-piedra-900 placeholder-piedra-400 focus:border-tierra-400 focus:outline-none focus:ring-1 focus:ring-tierra-300"
              />
            </div>

            {/* Categoría */}
            {categories.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-piedra-600">
                  Categoría
                </p>
                <ul className="flex flex-col gap-1">
                  <li>
                    <Link
                      href={filterHref({ category_id: undefined })}
                      className={[
                        'text-sm transition-colors',
                        !category_id
                          ? 'font-semibold text-tierra-600'
                          : 'text-piedra-700 hover:text-tierra-600',
                      ].join(' ')}
                    >
                      Todas
                    </Link>
                  </li>
                  {categories.map((cat) => (
                    <li key={cat.id}>
                      <Link
                        href={filterHref({ category_id: String(cat.id) })}
                        className={[
                          'text-sm transition-colors',
                          category_id === String(cat.id)
                            ? 'font-semibold text-tierra-600'
                            : 'text-piedra-700 hover:text-tierra-600',
                        ].join(' ')}
                      >
                        {cat.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Precio */}
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-piedra-600">
                Precio (CLP)
              </p>
              <div className="flex items-center gap-2">
                <input
                  name="min_price"
                  type="number"
                  min={0}
                  defaultValue={min_price}
                  placeholder="Mín"
                  className="w-full rounded-lg border border-piedra-200 bg-white px-2 py-1.5 text-sm text-piedra-900 placeholder-piedra-400 focus:border-tierra-400 focus:outline-none"
                />
                <span className="text-piedra-400">–</span>
                <input
                  name="max_price"
                  type="number"
                  min={0}
                  defaultValue={max_price}
                  placeholder="Máx"
                  className="w-full rounded-lg border border-piedra-200 bg-white px-2 py-1.5 text-sm text-piedra-900 placeholder-piedra-400 focus:border-tierra-400 focus:outline-none"
                />
              </div>
            </div>

            {/* Ordenar */}
            <div>
              <label
                htmlFor="sortBy"
                className="mb-1 block text-xs font-semibold uppercase tracking-wide text-piedra-600"
              >
                Ordenar por
              </label>
              <select
                id="sortBy"
                name="sortBy"
                defaultValue={sortBy ?? 'date_created'}
                className="w-full rounded-lg border border-piedra-200 bg-white px-3 py-2 text-sm text-piedra-900 focus:border-tierra-400 focus:outline-none"
              >
                <option value="date_created">Más recientes</option>
                <option value="price">Precio</option>
                <option value="name">Nombre</option>
              </select>
            </div>

            <button
              type="submit"
              className="rounded-full bg-tierra-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-tierra-600"
            >
              Filtrar
            </button>

            {Object.values(filters).some(Boolean) && (
              <Link
                href={baseHref}
                className="text-center text-xs text-piedra-500 hover:text-tierra-600"
              >
                Limpiar filtros
              </Link>
            )}
          </form>
        </aside>

        {/* Grilla de productos */}
        <div className="flex-1">
          {products.length === 0 ? (
            <div className="flex flex-col items-center gap-4 py-24 text-center text-piedra-500">
              <span className="font-manuscrita text-5xl text-piedra-300">✦</span>
              <p className="text-lg">No se encontraron productos.</p>
              {Object.values(filters).some(Boolean) && (
                <Link href={baseHref} className="text-sm text-tierra-600 hover:underline">
                  Quitar filtros
                </Link>
              )}
            </div>
          ) : (
            <>
              <p className="mb-4 text-sm text-piedra-500">
                {products.length} {products.length === 1 ? 'producto' : 'productos'}
              </p>
              <ul className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
                {products.map((product) => (
                  <li key={product.id}>
                    <ProductCard product={product} />
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
