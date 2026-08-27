'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useRef, useState } from 'react';
import { apiSocialLogin, apiMe, type SocialProvider } from '@/lib/auth';
import { useAuthStore } from '@/lib/store/auth';
import { useSyncGuestCart } from '@/components/providers/AuthProvider';
import { SOCIAL_PENDING_KEY } from '@/components/ui/SocialLoginButtons';
import { AuthFormWrapper } from '@/components/ui/AuthFormWrapper';

// El code de OAuth es de un solo uso. React StrictMode (dev) desmonta y
// remonta el componente, y un `useRef` se reinicia en cada montaje, así que
// NO evita el doble intercambio: Google recibe el mismo code dos veces y
// responde "Malformed auth code". Este guard a nivel de módulo sí sobrevive
// los remounts y garantiza un único intercambio por code.
const processedCodes = new Set<string>();

function SocialCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useAuthStore((s) => s.login);
  const syncGuestCart = useSyncGuestCart();
  const [error, setError] = useState('');
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    async function run() {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const oauthError = searchParams.get('error');

      if (oauthError) {
        setError('Cancelaste el acceso o el proveedor lo rechazó.');
        return;
      }
      if (!code || !state) {
        setError('Faltan parámetros de autenticación.');
        return;
      }
      // Un solo intercambio por code, aun con el doble montaje de StrictMode.
      if (processedCodes.has(code)) return;
      processedCodes.add(code);

      let pending: { provider: SocialProvider; next: string } | null = null;
      try {
        pending = JSON.parse(sessionStorage.getItem(SOCIAL_PENDING_KEY) ?? 'null');
      } catch {
        pending = null;
      }
      if (!pending?.provider) {
        setError('No se pudo identificar el proveedor. Intenta de nuevo.');
        return;
      }
      sessionStorage.removeItem(SOCIAL_PENDING_KEY);

      try {
        const { access, refresh } = await apiSocialLogin(
          pending.provider,
          state,
          code,
        );
        const user = await apiMe(access);
        login(access, refresh, user);
        await syncGuestCart(access);
        router.replace(pending.next || '/dashboard');
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'No se pudo completar el acceso.',
        );
      }
    }

    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (error) {
    return (
      <AuthFormWrapper title="No pudimos iniciar sesión">
        <div className="flex flex-col items-center gap-4 py-2 text-center">
          <p className="text-sm text-red-700">{error}</p>
          <Link href="/auth/login" className="text-sm text-tierra-600 hover:underline">
            Volver al inicio de sesión
          </Link>
        </div>
      </AuthFormWrapper>
    );
  }

  return (
    <AuthFormWrapper title="Iniciando sesión…">
      <div className="flex flex-col items-center gap-4 py-4 text-center">
        <span className="font-manuscrita text-4xl text-tierra-500">✦</span>
        <p className="text-sm text-piedra-600">Conectando tu cuenta…</p>
      </div>
    </AuthFormWrapper>
  );
}

export default function SocialCallbackPage() {
  return (
    <Suspense>
      <SocialCallback />
    </Suspense>
  );
}
