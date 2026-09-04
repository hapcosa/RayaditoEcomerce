'use client';

import { useState } from 'react';

/**
 * Número de seguimiento de la empresa de despacho (Starken), copiable.
 *
 * A propósito NO es un enlace: no hay integración con la API de Starken y no
 * queremos publicar una URL de rastreo inventada que lleve a un 404.
 */
export function TrackingNumber({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Sin permiso de portapapeles: el número sigue visible y seleccionable.
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-tierra-200 bg-tierra-50 px-4 py-3">
      <div className="min-w-0">
        <p className="text-xs uppercase tracking-wide text-tierra-600">
          Número de seguimiento
        </p>
        <p className="select-all font-mono text-base font-medium text-piedra-900">
          {value}
        </p>
      </div>
      <button
        type="button"
        onClick={copy}
        className="ml-auto rounded-full border border-tierra-300 px-4 py-1.5 text-xs font-medium text-tierra-700 hover:bg-tierra-100"
      >
        {copied ? 'Copiado' : 'Copiar'}
      </button>
    </div>
  );
}
