'use client';

import Link from 'next/link';
import { mediaUrl } from '@/lib/media';
import Image from 'next/image';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { useWishlistStore } from '@/lib/store/wishlist';
import { formatCLP } from '@/lib/format';

export default function WishlistPage() {
  const router = useRouter();
  const access = useAuthStore((s) => s.access);
  const { items, loaded, load, remove } = useWishlistStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (!access) {
      router.replace('/auth/login?next=/wishlist');
      return;
    }
    load(access);
  }, [mounted, access, load, router]);

  if (!mounted || !access) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16 text-center text-piedra-500">
        Cargando…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <p className="font-manuscrita text-xl text-tierra-600">tus favoritos</p>
      <h1 className="mt-1 font-serif text-3xl font-medium text-piedra-900">
        Lista de deseos
      </h1>

      {loaded && items.length === 0 ? (
        <div className="mt-12 flex flex-col items-center gap-4 text-center">
          <span className="font-manuscrita text-5xl text-tierra-300">♡</span>
          <p className="text-piedra-600">Todavía no guardaste ninguna pieza.</p>
          <Link
            href="/joyas"
            className="rounded-full bg-tierra-500 px-6 py-2.5 text-sm font-medium uppercase tracking-wide text-piedra-50 hover:bg-tierra-600"
          >
            Explorar joyas
          </Link>
        </div>
      ) : (
        <ul className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => {
            const p = item.product;
            const href = `/productos/${p.slug ?? p.id}`;
            return (
              <li
                key={item.id}
                className="flex flex-col overflow-hidden rounded-xl border border-piedra-200 bg-white"
              >
                <Link href={href} className="group relative aspect-square overflow-hidden bg-piedra-100">
                  {p.photo ? (
                    <Image
                      src={mediaUrl(p.photo)}
                      alt={p.name}
                      fill
                      sizes="(max-width: 640px) 100vw, 33vw"
                      className="object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                  ) : (
                    <span className="flex h-full items-center justify-center font-manuscrita text-4xl text-piedra-300">
                      ✦
                    </span>
                  )}
                </Link>
                <div className="flex flex-1 flex-col gap-2 p-4">
                  <Link href={href} className="text-sm font-medium text-piedra-900 hover:text-tierra-600">
                    {p.name}
                  </Link>
                  <span className="text-base font-semibold text-piedra-900">
                    {formatCLP(p.price)}
                  </span>
                  <button
                    type="button"
                    onClick={() => access && remove(access, p.id)}
                    className="mt-auto self-start text-xs text-piedra-400 hover:text-red-500"
                  >
                    Quitar
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
