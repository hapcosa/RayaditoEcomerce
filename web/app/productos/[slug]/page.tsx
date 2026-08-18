import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { fetchProduct, fetchRelatedProducts, fetchReviews } from '@/lib/api';
import { ProductGallery } from '@/components/ui/ProductGallery';
import { ProductCard } from '@/components/ui/ProductCard';
import { StarRating } from '@/components/ui/StarRating';
import { AddToCartButton } from '@/components/ui/AddToCartButton';
import { WishlistButton } from '@/components/ui/WishlistButton';
import { JsonLd } from '@/components/seo/JsonLd';
import { formatCLP } from '@/lib/format';
import { absoluteUrl } from '@/lib/site';

interface PageProps {
  params: { slug: string };
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  try {
    const product = await fetchProduct(params.slug);
    const canonical = absoluteUrl(`/productos/${product.slug ?? params.slug}`);
    return {
      title: product.name,
      description: product.description.slice(0, 160),
      alternates: { canonical },
      openGraph: {
        type: 'website',
        url: canonical,
        title: product.name,
        description: product.description.slice(0, 160),
        images: product.photo ? [{ url: product.photo }] : [],
      },
    };
  } catch {
    return { title: 'Producto no encontrado' };
  }
}

export default async function ProductDetailPage({ params }: PageProps) {
  let product;
  try {
    product = await fetchProduct(params.slug);
  } catch {
    notFound();
  }

  const [related, reviews] = await Promise.all([
    fetchRelatedProducts(product.slug ?? String(product.id)).catch(() => []),
    fetchReviews(product.id).catch(() => []),
  ]);

  const hasDiscount = product.compare_price > product.price;
  const outOfStock = product.available_stock === 0;
  const avgRating =
    reviews.length > 0
      ? reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length
      : 0;

  const catalogHref =
    product.product_type === 'piedra' ? '/piedras' : '/joyas';
  const catalogLabel =
    product.product_type === 'piedra' ? 'Piedras' : 'Joyas';

  const productUrl = absoluteUrl(`/productos/${product.slug ?? product.id}`);
  const productJsonLd: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    description: product.description,
    url: productUrl,
    ...(product.photo ? { image: product.photo } : {}),
    offers: {
      '@type': 'Offer',
      url: productUrl,
      // Moneda siempre en entero CLP (ver AGENTS.md).
      priceCurrency: 'CLP',
      price: product.price,
      availability: outOfStock
        ? 'https://schema.org/OutOfStock'
        : 'https://schema.org/InStock',
    },
    ...(reviews.length > 0
      ? {
          aggregateRating: {
            '@type': 'AggregateRating',
            ratingValue: Number(avgRating.toFixed(1)),
            reviewCount: reviews.length,
          },
        }
      : {}),
  };

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <JsonLd data={productJsonLd} />
      {/* Breadcrumb */}
      <nav className="mb-8 flex items-center gap-2 text-sm text-piedra-500" aria-label="Breadcrumb">
        <Link href="/" className="hover:text-tierra-600">Inicio</Link>
        <span>/</span>
        <Link href={catalogHref} className="hover:text-tierra-600">{catalogLabel}</Link>
        <span>/</span>
        <span className="text-piedra-800">{product.name}</span>
      </nav>

      {/* Producto principal */}
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-2">
        {/* Galería */}
        <ProductGallery
          mainPhoto={product.photo}
          productName={product.name}
          gallery={product.gallery}
        />

        {/* Información */}
        <div className="flex flex-col gap-5">
          <div>
            <h1 className="font-serif text-3xl font-medium text-piedra-900">
              {product.name}
            </h1>

            {reviews.length > 0 && (
              <div className="mt-2 flex items-center gap-2">
                <StarRating rating={avgRating} />
                <span className="text-sm text-piedra-500">
                  {reviews.length} {reviews.length === 1 ? 'reseña' : 'reseñas'}
                </span>
              </div>
            )}
          </div>

          {/* Precio */}
          <div className="flex items-baseline gap-3">
            <span className="text-2xl font-semibold text-piedra-900">
              {formatCLP(product.price)}
            </span>
            {hasDiscount && (
              <span className="text-base text-piedra-400 line-through">
                {formatCLP(product.compare_price)}
              </span>
            )}
          </div>

          {/* Stock */}
          <p
            className={[
              'text-sm font-medium',
              outOfStock ? 'text-piedra-400' : 'text-green-700',
            ].join(' ')}
          >
            {outOfStock ? 'Sin stock' : `${product.available_stock} disponibles`}
          </p>

          {/* Variantes */}
          {product.variants.filter((v) => v.is_active).length > 0 && (
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-piedra-600">
                Variantes
              </p>
              <ul className="flex flex-wrap gap-2">
                {product.variants
                  .filter((v) => v.is_active)
                  .map((v) => (
                    <li
                      key={v.id}
                      className="rounded-full border border-piedra-200 px-3 py-1 text-sm text-piedra-700"
                    >
                      {v.sku}
                      {v.price_override != null &&
                        ` · ${formatCLP(v.price_override)}`}
                    </li>
                  ))}
              </ul>
            </div>
          )}

          {/* Atributos */}
          {product.attributes.length > 0 && (
            <dl className="grid grid-cols-2 gap-x-6 gap-y-2 rounded-xl border border-piedra-200 p-4">
              {product.attributes.map((attr) => (
                <div key={attr.id} className="col-span-1">
                  <dt className="text-xs text-piedra-500">{attr.attribute_name}</dt>
                  <dd className="text-sm font-medium text-piedra-900">
                    {attr.value_display}
                    {attr.attribute_unit ? ` ${attr.attribute_unit}` : ''}
                  </dd>
                </div>
              ))}
            </dl>
          )}

          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="flex-1">
              <AddToCartButton productId={product.id} outOfStock={outOfStock} />
            </div>
            <WishlistButton productId={product.id} />
          </div>

          {/* Descripción */}
          <div className="border-t border-piedra-200 pt-5">
            <p className="text-sm font-semibold uppercase tracking-wide text-piedra-600">
              Descripción
            </p>
            <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-piedra-700">
              {product.description}
            </p>
          </div>
        </div>
      </div>

      {/* Reseñas */}
      {reviews.length > 0 && (
        <section className="mt-16">
          <h2 className="font-serif text-2xl font-medium text-piedra-900">
            Reseñas ({reviews.length})
          </h2>
          <ul className="mt-6 flex flex-col gap-5">
            {reviews.map((review) => (
              <li
                key={review.id}
                className="rounded-xl border border-piedra-200 p-5"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <StarRating rating={review.rating} size="sm" />
                    <span className="text-sm font-medium text-piedra-800">
                      {review.user_name || 'Cliente'}
                    </span>
                  </div>
                  <time className="text-xs text-piedra-400">
                    {new Date(review.created_at).toLocaleDateString('es-CL')}
                  </time>
                </div>
                {review.comment && (
                  <p className="mt-2 text-sm leading-relaxed text-piedra-700">
                    {review.comment}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Productos relacionados */}
      {related.length > 0 && (
        <section className="mt-16">
          <h2 className="font-serif text-2xl font-medium text-piedra-900">
            También te puede gustar
          </h2>
          <ul className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((p) => (
              <li key={p.id}>
                <ProductCard product={p} />
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
