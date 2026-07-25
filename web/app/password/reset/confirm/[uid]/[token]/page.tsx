'use client';

import Link from 'next/link';
import { useState } from 'react';
import { apiResetPasswordConfirm } from '@/lib/auth';
import {
  AuthFormWrapper,
  Field,
  inputCls,
  submitCls,
} from '@/components/ui/AuthFormWrapper';

interface PageProps {
  params: { uid: string; token: string };
}

export default function ResetPasswordConfirmPage({ params }: PageProps) {
  const [newPassword, setNewPassword] = useState('');
  const [reNewPassword, setReNewPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    if (newPassword !== reNewPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }
    setLoading(true);
    try {
      await apiResetPasswordConfirm({
        uid: params.uid,
        token: params.token,
        new_password: newPassword,
        re_new_password: reNewPassword,
      });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al restablecer');
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <AuthFormWrapper title="Contraseña actualizada">
        <div className="flex flex-col items-center gap-4 py-4 text-center">
          <span className="font-manuscrita text-5xl text-tierra-500">✦</span>
          <p className="text-piedra-700">
            Tu contraseña fue cambiada exitosamente.
          </p>
          <Link
            href="/auth/login"
            className="mt-2 rounded-full bg-tierra-500 px-6 py-2.5 text-sm font-medium text-white hover:bg-tierra-600"
          >
            Iniciar sesión
          </Link>
        </div>
      </AuthFormWrapper>
    );
  }

  return (
    <AuthFormWrapper title="Nueva contraseña">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && (
          <p className="rounded-lg bg-red-50 px-4 py-2.5 text-sm text-red-700">
            {error}
          </p>
        )}

        <Field label="Nueva contraseña" id="new_password">
          <input
            id="new_password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className={inputCls}
          />
        </Field>

        <Field label="Repetir contraseña" id="re_new_password">
          <input
            id="re_new_password"
            type="password"
            autoComplete="new-password"
            required
            value={reNewPassword}
            onChange={(e) => setReNewPassword(e.target.value)}
            className={inputCls}
          />
        </Field>

        <button type="submit" disabled={loading} className={submitCls}>
          {loading ? 'Guardando…' : 'Guardar contraseña'}
        </button>
      </form>
    </AuthFormWrapper>
  );
}
