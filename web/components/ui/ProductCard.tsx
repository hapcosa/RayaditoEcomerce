import Image from 'next/image';
import Link from 'next/link';
import type { Product } from '@/types/product';
import { formatCLP } from '@/lib/format';

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const href = `/productos/${product.slug ?? product.id}`;
  const hasDiscount = product.compare_price > product.price;

  return (
    <Link
      href={href}
      className="group flex flex-col overflow-hidden rounded-xl border border-piedra-200 bg-white transition-shadow hover:shadow-md"
    >
      <div className="relative aspect-square overflow-hidden bg-piedra-100">
        {product.photo ? (
          <Image
            src={product.photo}
            alt={product.name}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            className="object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <span className="font-manuscrita text-4xl text-piedra-300">✦</span>
          </div>
        )}
        {product.available_stock === 0 && (
          <span className="absolute left-2 top-2 rounded-full bg-piedra-800/80 px-2.5 py-0.5 text-xs font-medium text-piedra-50">
            Agotado
          </span>
        )}
        {hasDiscount && (
          <span className="absolute right-2 top-2 rounded-full bg-tierra-500 px-2.5 py-0.5 text-xs font-medium text-white">
            Oferta
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-1.5 p-4">
        <p className="line-clamp-2 text-sm font-medium text-piedra-900 group-hover:text-tierra-600">
          {product.name}
        </p>
        <div className="mt-auto flex items-baseline gap-2">
          <span className="text-base font-semibold text-piedra-900">
            {formatCLP(product.price)}
          </span>
          {hasDiscount && (
            <span className="text-xs text-piedra-400 line-through">
              {formatCLP(product.compare_price)}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
