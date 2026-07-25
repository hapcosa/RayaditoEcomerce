'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useCartStore, selectTotalItems } from '@/lib/store/cart';

export function CartBadge() {
  // Evita mismatch de hidratación: localStorage no existe en SSR.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const total = useCartStore(selectTotalItems);

  return (
    <Link
      href="/carrito"
      aria-label={`Carrito${mounted && total > 0 ? ` (${total} items)` : ''}`}
      className="relative text-piedra-700 transition-colors hover:text-tierra-600"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
        className="h-6 w-6" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round"
          d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" />
      </svg>
      {mounted && total > 0 && (
        <span className="absolute -right-2 -top-2 flex h-4 w-4 items-center justify-center rounded-full bg-tierra-500 text-[10px] font-bold text-white">
          {total > 9 ? '9+' : total}
        </span>
      )}
    </Link>
  );
}
