'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth';

export function AuthNav() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const { user, logout } = useAuthStore();
  const router = useRouter();

  if (!mounted) return null;

  if (user) {
    return (
      <div className="flex items-center gap-3">
        <Link
          href="/dashboard"
          className="text-sm font-medium text-piedra-700 transition-colors hover:text-tierra-600"
        >
          {user.first_name}
        </Link>
        <button
          onClick={() => { logout(); router.push('/'); }}
          className="text-xs text-piedra-400 hover:text-red-500"
        >
          Salir
        </button>
      </div>
    );
  }

  return (
    <Link
      href="/auth/login"
      className="text-sm font-medium text-piedra-700 transition-colors hover:text-tierra-600"
    >
      Iniciar sesión
    </Link>
  );
}
