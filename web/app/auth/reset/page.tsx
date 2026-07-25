'use client';

import Link from 'next/link';
import { useState } from 'react';
import { apiResetPassword } from '@/lib/auth';
import {
  AuthFormWrapper,
  Field,
  inputCls,
  submitCls,
} from '@/components/ui/AuthFormWrapper';

export default function ResetPasswordPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await apiResetPassword(email);
    } finally {
      // Siempre mostrar éxito (no revelar si el email existe).
      setSent(true);
      setLoading(false);
    }
  }

  if (sent) {
    return (
      <AuthFormWrapper title="Revisa tu correo">
        <div className="flex flex-col items-center gap-4 py-4 text-center">
          <span className="font-manuscrita text-5xl text-tierra-500">✦</span>
          <p className="text-piedra-700">
            Si el correo existe en nuestro sistema, recibirás un enlace para
            restablecer tu contraseña.
          </p>
          <Link
            href="/auth/login"
            className="mt-2 text-sm text-tierra-600 hover:underline"
          >
            Volver al inicio de sesión
          </Link>
        </div>
      </AuthFormWrapper>
    );
  }

  return (
    <AuthFormWrapper
      title="Restablecer contraseña"
      subtitle="Ingresa tu correo y te enviaremos un enlace."
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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

        <button type="submit" disabled={loading} className={submitCls}>
          {loading ? 'Enviando…' : 'Enviar enlace'}
        </button>

        <Link
          href="/auth/login"
          className="text-center text-xs text-piedra-500 hover:text-tierra-600"
        >
          Volver
        </Link>
      </form>
    </AuthFormWrapper>
  );
}
