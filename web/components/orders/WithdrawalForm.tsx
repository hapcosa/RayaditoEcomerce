'use client';

import { useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { requestWithdrawal, type WithdrawalResult } from '@/lib/withdrawal';

const inputCls =
  'w-full rounded-lg border border-piedra-300 bg-white px-3 py-2 text-sm text-piedra-900 placeholder-piedra-400 focus:border-tierra-400 focus:outline-none focus:ring-1 focus:ring-tierra-300';

export function WithdrawalForm() {
  // El detalle del pedido enlaza con ?pedido=<número> para no tener que copiarlo.
  const searchParams = useSearchParams();
  const [orderNumber, setOrderNumber] = useState(searchParams.get('pedido') ?? '');
  const [email, setEmail] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WithdrawalResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      setResult(
        await requestWithdrawal({
          order_number: orderNumber.trim(),
          email: email.trim(),
          reason: reason.trim(),
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No pudimos registrar tu solicitud.');
    } finally {
      setLoading(false);
    }
  }

  if (result) {
    return (
      <div role="status" className="rounded-2xl border border-tierra-200 bg-tierra-50 p-6">
        <p className="font-serif text-xl text-piedra-900">{result.message}</p>
        <p className="mt-3 text-sm text-piedra-700">Código de tu solicitud:</p>
        <p className="mt-1 font-mono text-2xl font-semibold tracking-wide text-tierra-700">
          {result.code}
        </p>
        <p className="mt-4 text-sm leading-relaxed text-piedra-700">
          Guarda este código: es tu constancia de que ejerciste el derecho a
          retracto. También te lo enviamos por correo. Te escribiremos con las
          instrucciones para devolver el producto.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm text-piedra-700">
          Número de pedido
          <input
            required
            value={orderNumber}
            onChange={(e) => setOrderNumber(e.target.value)}
            className={inputCls}
            placeholder="Ej. 130551234567"
            inputMode="numeric"
            maxLength={64}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-piedra-700">
          Correo con el que compraste
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputCls}
            placeholder="tu@correo.cl"
          />
        </label>
      </div>
      <label className="flex flex-col gap-1 text-sm text-piedra-700">
        Motivo (opcional, no es obligatorio indicarlo)
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className={`${inputCls} min-h-24`}
          maxLength={2000}
        />
      </label>

      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="self-start rounded-full bg-tierra-600 px-6 py-3 text-sm font-semibold text-white hover:bg-tierra-700 disabled:opacity-60"
      >
        {loading ? 'Enviando…' : 'Me arrepiento de mi compra'}
      </button>
    </form>
  );
}
