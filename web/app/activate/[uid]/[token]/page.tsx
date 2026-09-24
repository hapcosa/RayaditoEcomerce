'use client';

import Link from 'next/link';
import { use, useEffect, useState } from 'react';
import { apiActivate } from '@/lib/auth';
import { AuthFormWrapper } from '@/components/ui/AuthFormWrapper';

interface PageProps {
  // Next 15 entrega los parámetros de ruta como promesa, también en el cliente.
  params: Promise<{ uid: string; token: string }>;
}

export default function ActivatePage({ params }: PageProps) {
  const { uid, token } = use(params);
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');

  useEffect(() => {
    apiActivate(uid, token)
      .then(() => setStatus('ok'))
      .catch(() => setStatus('error'));
  }, [uid, token]);

  return (
    <AuthFormWrapper title="Activación de cuenta">
      <div className="flex flex-col items-center gap-4 py-4 text-center">
        {status === 'loading' && (
          <p className="text-piedra-500">Activando cuenta…</p>
        )}
        {status === 'ok' && (
          <>
            <span className="font-manuscrita text-5xl text-tierra-500">✦</span>
            <p className="text-piedra-700">
              ¡Cuenta activada! Ya puedes iniciar sesión.
            </p>
            <Link
              href="/auth/login"
              className="mt-2 rounded-full bg-tierra-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-tierra-600"
            >
              Iniciar sesión
            </Link>
          </>
        )}
        {status === 'error' && (
          <>
            <p className="text-red-600">Enlace inválido o ya utilizado.</p>
            <Link href="/auth/login" className="text-sm text-tierra-600 hover:underline">
              Volver al inicio
            </Link>
          </>
        )}
      </div>
    </AuthFormWrapper>
  );
}
