'use client';

import { useState } from 'react';
import { apiSocialAuthUrl, type SocialProvider } from '@/lib/auth';

// Clave de sessionStorage: el callback necesita saber qué proveedor y a dónde volver.
export const SOCIAL_PENDING_KEY = 'rayadito-social-pending';

interface SocialLoginButtonsProps {
  /** Ruta a la que volver tras autenticar (por defecto /dashboard). */
  next?: string;
}

export function SocialLoginButtons({ next = '/dashboard' }: SocialLoginButtonsProps) {
  const [loading, setLoading] = useState<SocialProvider | null>(null);
  const [error, setError] = useState('');

  async function start(provider: SocialProvider) {
    setError('');
    setLoading(provider);
    try {
      sessionStorage.setItem(
        SOCIAL_PENDING_KEY,
        JSON.stringify({ provider, next }),
      );
      const url = await apiSocialAuthUrl(provider);
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo continuar');
      setLoading(null);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-2.5 text-sm text-red-700">
          {error}
        </p>
      )}

      <button
        type="button"
        onClick={() => start('google-oauth2')}
        disabled={loading !== null}
        className={socialBtnCls}
      >
        <GoogleIcon />
        {loading === 'google-oauth2' ? 'Redirigiendo…' : 'Continuar con Google'}
      </button>

      <button
        type="button"
        onClick={() => start('facebook')}
        disabled={loading !== null}
        className={socialBtnCls}
      >
        <FacebookIcon />
        {loading === 'facebook' ? 'Redirigiendo…' : 'Continuar con Facebook'}
      </button>
    </div>
  );
}

const socialBtnCls =
  'flex w-full items-center justify-center gap-3 rounded-full border border-piedra-200 bg-white py-2.5 text-sm font-medium text-piedra-800 transition-colors hover:border-piedra-300 hover:bg-piedra-50 disabled:opacity-60';

/** Separador "o" para colocar entre el formulario y los botones sociales. */
export function SocialDivider() {
  return (
    <div className="my-5 flex items-center gap-3">
      <span className="h-px flex-1 bg-piedra-200" />
      <span className="text-xs uppercase tracking-wide text-piedra-400">o</span>
      <span className="h-px flex-1 bg-piedra-200" />
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.71-1.57 2.68-3.89 2.68-6.62Z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.02-3.7H.96v2.34A9 9 0 0 0 9 18Z"
      />
      <path
        fill="#FBBC05"
        d="M3.98 10.72a5.4 5.4 0 0 1 0-3.44V4.94H.96a9 9 0 0 0 0 8.12l3.02-2.34Z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.46.9 11.43 0 9 0A9 9 0 0 0 .96 4.94l3.02 2.34C4.68 5.16 6.66 3.58 9 3.58Z"
      />
    </svg>
  );
}

function FacebookIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#1877F2"
        d="M24 12.07C24 5.4 18.63 0 12 0S0 5.4 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.69 4.53-4.69 1.31 0 2.68.24 2.68.24v2.97h-1.51c-1.49 0-1.96.93-1.96 1.89v2.25h3.33l-.53 3.49h-2.8V24C19.61 23.1 24 18.1 24 12.07Z"
      />
    </svg>
  );
}
