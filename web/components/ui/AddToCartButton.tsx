'use client';

import { useState } from 'react';
import { useCartStore } from '@/lib/store/cart';

interface AddToCartButtonProps {
  productId: number;
  outOfStock: boolean;
}

export function AddToCartButton({ productId, outOfStock }: AddToCartButtonProps) {
  const addItem = useCartStore((s) => s.addItem);
  const items = useCartStore((s) => s.items);
  const [added, setAdded] = useState(false);

  const inCart = items.some((i) => i.product_id === productId);

  function handleAdd() {
    if (inCart || outOfStock) return;
    addItem(productId);
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  }

  if (outOfStock) {
    return (
      <button
        disabled
        className="w-full rounded-full bg-piedra-200 px-8 py-3 text-sm font-medium uppercase tracking-wide text-piedra-400"
      >
        Sin stock
      </button>
    );
  }

  if (inCart) {
    return (
      <a
        href="/carrito"
        className="flex w-full items-center justify-center gap-2 rounded-full border border-tierra-500 px-8 py-3 text-sm font-medium uppercase tracking-wide text-tierra-600 transition-colors hover:bg-tierra-50"
      >
        <CartIcon />
        Ver carrito
      </a>
    );
  }

  return (
    <button
      onClick={handleAdd}
      className={[
        'w-full rounded-full px-8 py-3 text-sm font-medium uppercase tracking-wide text-white transition-colors',
        added
          ? 'bg-green-600 hover:bg-green-700'
          : 'bg-tierra-500 hover:bg-tierra-600',
      ].join(' ')}
    >
      {added ? '¡Agregado!' : 'Añadir al carrito'}
    </button>
  );
}

function CartIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden="true">
      <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3z" />
      <path d="M16 16.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM6.5 18a1.5 1.5 0 100-3 1.5 1.5 0 000 3z" />
    </svg>
  );
}
