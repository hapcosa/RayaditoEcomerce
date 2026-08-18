'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState, Suspense } from 'react';
import type { Metadata } from 'next';
import { apiLogin, apiMe } from '@/lib/auth';
import { useAuthStore } from '@/lib/store/auth';
import { useSyncGuestCart } from '@/components/providers/AuthProvider';
import {
  AuthFormWrapper,
  Field,
  inputCls,
  submitCls,
} from '@/components/ui/AuthFormWrapper';
import {
  SocialLoginButtons,
  SocialDivider,
} from '@/components/ui/SocialLoginButtons';

// Next.js 14: useSearchParams necesita Suspense cuando la página no es dinámica.
function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get('next') ?? '/dashboard';

  const login = useAuthStore((s) => s.login);
  const syncGuestCart = useSyncGuestCart();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { access, refresh } = await apiLogin(email, password);
      const user = await apiMe(access);
      login(access, refresh, user);
      await syncGuestCart(access);
      router.replace(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthFormWrapper
      title="Iniciar sesión"
      subtitle={
        <>
          ¿No tienes cuenta?{' '}
          <Link href="/auth/registro" className="text-tierra-600 hover:underline">
            Regístrate
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && (
          <p className="rounded-lg bg-red-50 px-4 py-2.5 text-sm text-red-700">
            {error}
          </p>
        )}

        <Field label="Correo electrónico" id="email">
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputCls}
            placeholder="hola@ejemplo.cl"
          />
        </Field>

        <Field label="Contraseña" id="password">
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputCls}
          />
        </Field>

        <div className="text-right">
          <Link
            href="/auth/reset"
            className="text-xs text-piedra-500 hover:text-tierra-600"
          >
            ¿Olvidaste tu contraseña?
          </Link>
        </div>

        <button type="submit" disabled={loading} className={submitCls}>
          {loading ? 'Ingresando…' : 'Ingresar'}
        </button>
      </form>

      <SocialDivider />
      <SocialLoginButtons next={next} />
    </AuthFormWrapper>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
