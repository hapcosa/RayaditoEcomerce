'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';
import { useWishlistStore } from '@/lib/store/wishlist';

export default function DashboardPage() {
  const router = useRouter();
  const { user, logout, access } = useAuthStore();
  const resetWishlist = useWishlistStore((s) => s.reset);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Esperar rehidratación antes de redirigir.
  useEffect(() => {
    if (!mounted) return;
    if (!access) {
      router.replace('/auth/login?next=/dashboard');
    }
  }, [mounted, access, router]);

  if (!mounted || !user) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16 text-center text-piedra-500">
        Cargando…
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <div className="mb-8">
        <p className="font-manuscrita text-xl text-tierra-600">Bienvenida/o</p>
        <h1 className="mt-1 font-serif text-3xl font-medium text-piedra-900">
          {user.get_full_name || `${user.first_name} ${user.last_name}`}
        </h1>
        <p className="mt-1 text-sm text-piedra-500">{user.email}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <DashCard
          title="Mis pedidos"
          description="Historial, estado y seguimiento de tus órdenes."
          href="/pedidos"
        />
        <DashCard
          title="Lista de deseos"
          description="Las piezas que guardaste como favoritas."
          href="/wishlist"
        />
        <DashCard
          title="Carrito"
          description="Ver y editar los productos guardados."
          href="/carrito"
        />
        <DashCard
          title="Joyas"
          description="Explorar el catálogo de joyería."
          href="/joyas"
        />
        <DashCard
          title="Piedras"
          description="Explorar el catálogo de piedras."
          href="/piedras"
        />
      </div>

      <button
        onClick={() => { logout(); resetWishlist(); router.replace('/'); }}
        className="mt-10 text-sm text-piedra-400 hover:text-red-500"
      >
        Cerrar sesión
      </button>
    </div>
  );
}

function DashCard({
  title,
  description,
  href,
  comingSoon,
}: {
  title: string;
  description: string;
  href: string;
  comingSoon?: boolean;
}) {
  return (
    <Link
      href={comingSoon ? '#' : href}
      className={[
        'flex flex-col gap-1 rounded-xl border p-5 transition-shadow',
        comingSoon
          ? 'cursor-default border-piedra-100 bg-piedra-50 text-piedra-400'
          : 'border-piedra-200 bg-white hover:shadow-md',
      ].join(' ')}
      aria-disabled={comingSoon}
    >
      <p className="font-medium">{title}</p>
      <p className="text-sm">{description}</p>
      {comingSoon && (
        <span className="mt-1 text-xs text-piedra-400">Próximamente</span>
      )}
    </Link>
  );
}
