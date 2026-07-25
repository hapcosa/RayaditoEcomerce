'use client';

import Link from 'next/link';
import { useState } from 'react';
import { apiRegister } from '@/lib/auth';
import {
  AuthFormWrapper,
  Field,
  inputCls,
  submitCls,
} from '@/components/ui/AuthFormWrapper';

export default function RegistroPage() {
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    re_password: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  function set(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    if (form.password !== form.re_password) {
      setError('Las contraseñas no coinciden');
      return;
    }
    setLoading(true);
    try {
      await apiRegister(form);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al registrar');
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <AuthFormWrapper title="¡Cuenta creada!">
        <div className="flex flex-col items-center gap-4 py-4 text-center">
          <span className="font-manuscrita text-5xl text-tierra-500">✦</span>
          <p className="text-piedra-700">
            Te enviamos un correo de activación. Revísalo para completar el registro.
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
      title="Crear cuenta"
      subtitle={
        <>
          ¿Ya tienes cuenta?{' '}
          <Link href="/auth/login" className="text-tierra-600 hover:underline">
            Inicia sesión
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

        <div className="grid grid-cols-2 gap-3">
          <Field label="Nombre" id="first_name">
            <input
              id="first_name"
              type="text"
              autoComplete="given-name"
              required
              value={form.first_name}
              onChange={set('first_name')}
              className={inputCls}
              placeholder="María"
            />
          </Field>
          <Field label="Apellido" id="last_name">
            <input
              id="last_name"
              type="text"
              autoComplete="family-name"
              required
              value={form.last_name}
              onChange={set('last_name')}
              className={inputCls}
              placeholder="González"
            />
          </Field>
        </div>

        <Field label="Correo electrónico" id="email">
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={form.email}
            onChange={set('email')}
            className={inputCls}
            placeholder="hola@ejemplo.cl"
          />
        </Field>

        <Field label="Contraseña" id="password">
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={form.password}
            onChange={set('password')}
            className={inputCls}
          />
        </Field>

        <Field label="Repetir contraseña" id="re_password">
          <input
            id="re_password"
            type="password"
            autoComplete="new-password"
            required
            value={form.re_password}
            onChange={set('re_password')}
            className={inputCls}
          />
        </Field>

        <button type="submit" disabled={loading} className={`${submitCls} mt-1`}>
          {loading ? 'Creando cuenta…' : 'Crear cuenta'}
        </button>
      </form>
    </AuthFormWrapper>
  );
}
