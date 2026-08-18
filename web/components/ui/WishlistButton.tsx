'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { useWishlistStore } from '@/lib/store/wishlist';

interface WishlistButtonProps {
  productId: number;
  /** 'full' = botón con texto (ficha); 'icon' = solo corazón. */
  variant?: 'full' | 'icon';
}

export function WishlistButton({ productId, variant = 'full' }: WishlistButtonProps) {
  const router = useRouter();
  const access = useAuthStore((s) => s.access);
  const { ids, loaded, load, add, remove } = useWishlistStore();
  const [busy, setBusy] = useState(false);

  // Cargar la lista una vez cuando hay sesión.
  useEffect(() => {
    if (access && !loaded) load(access);
  }, [access, loaded, load]);

  const inWishlist = ids.includes(productId);

  async function handleClick() {
    if (!access) {
      router.push(`/auth/login?next=/productos`);
      return;
    }
    setBusy(true);
    try {
      if (inWishlist) await remove(access, productId);
      else await add(access, productId);
    } finally {
      setBusy(false);
    }
  }

  const label = inWishlist ? 'Quitar de favoritos' : 'Agregar a favoritos';

  if (variant === 'icon') {
    return (
      <button
        type="button"
        onClick={handleClick}
        disabled={busy}
        aria-pressed={inWishlist}
        aria-label={label}
        title={label}
        className="flex h-9 w-9 items-center justify-center rounded-full border border-piedra-200 bg-white text-lg transition-colors hover:border-tierra-400 disabled:opacity-50"
      >
        <span className={inWishlist ? 'text-tierra-500' : 'text-piedra-400'}>
          {inWishlist ? '♥' : '♡'}
        </span>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={busy}
      aria-pressed={inWishlist}
      className={[
        'flex items-center justify-center gap-2 rounded-full border px-5 py-3 text-sm font-medium uppercase tracking-wide transition-colors disabled:opacity-50',
        inWishlist
          ? 'border-tierra-400 bg-tierra-50 text-tierra-700 hover:bg-tierra-100'
          : 'border-piedra-300 text-piedra-800 hover:border-tierra-400 hover:text-tierra-600',
      ].join(' ')}
    >
      <span className={inWishlist ? 'text-tierra-500' : ''}>
        {inWishlist ? '♥' : '♡'}
      </span>
      {label}
    </button>
  );
}
