'use client';

import { useState } from 'react';
import {
  SUGGESTION_KINDS,
  submitSuggestion,
  type SuggestionKind,
} from '@/lib/suggestions';

const inputCls =
  'w-full rounded-lg border border-piedra-300 bg-white/90 px-3 py-2 text-sm text-piedra-900 placeholder-piedra-400 focus:border-tierra-400 focus:outline-none focus:ring-1 focus:ring-tierra-300';

export function SuggestionForm() {
  const [kind, setKind] = useState<SuggestionKind>('sugerencia');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [ok, setOk] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setOk(null);
    setLoading(true);
    try {
      const res = await submitSuggestion({
        kind,
        name: name.trim() || undefined,
        email: email.trim() || undefined,
        message: message.trim(),
      });
      setOk(res.message);
      setName('');
      setEmail('');
      setMessage('');
      setKind('sugerencia');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No pudimos enviar tu mensaje.');
    } finally {
      setLoading(false);
    }
  }

  if (ok) {
    return (
      <div className="flex flex-col items-start gap-2">
        <span className="font-manuscrita text-3xl text-tierra-400">✦</span>
        <p className="text-sm text-piedra-200">{ok}</p>
        <button
          type="button"
          onClick={() => setOk(null)}
          className="text-xs text-tierra-300 hover:underline"
        >
          Enviar otro mensaje
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div>
        <label htmlFor="suggestion-kind" className="sr-only">
          Tipo de mensaje
        </label>
        <select
          id="suggestion-kind"
          value={kind}
          onChange={(e) => setKind(e.target.value as SuggestionKind)}
          className={inputCls}
        >
          {SUGGESTION_KINDS.map((k) => (
            <option key={k.value} value={k.value}>
              {k.label}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="suggestion-name" className="sr-only">
            Nombre (opcional)
          </label>
          <input
            id="suggestion-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={inputCls}
            placeholder="Nombre (opcional)"
            maxLength={120}
          />
        </div>
        <div>
          <label htmlFor="suggestion-email" className="sr-only">
            Correo (opcional)
          </label>
          <input
            id="suggestion-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputCls}
            placeholder="Correo (opcional)"
          />
        </div>
      </div>

      <div>
        <label htmlFor="suggestion-message" className="sr-only">
          Mensaje
        </label>
        <textarea
          id="suggestion-message"
          required
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className={`${inputCls} resize-y`}
          placeholder="Cuéntanos tu sugerencia, reclamo o felicitación…"
          rows={3}
          minLength={3}
          maxLength={2000}
        />
      </div>

      {error && <p className="text-xs text-red-300">{error}</p>}

      <button
        type="submit"
        disabled={loading}
        className="self-start rounded-full bg-tierra-500 px-5 py-2.5 text-sm font-medium uppercase tracking-wide text-white transition-colors hover:bg-tierra-600 disabled:bg-piedra-600 disabled:text-piedra-400"
      >
        {loading ? 'Enviando…' : 'Enviar'}
      </button>
    </form>
  );
}
