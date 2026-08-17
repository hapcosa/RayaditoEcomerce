import { API_BASE_URL } from './api';

/** Tipos de mensaje que acepta el buzón (espeja Suggestion.Kind del backend). */
export const SUGGESTION_KINDS = [
  { value: 'sugerencia', label: 'Sugerencia' },
  { value: 'reclamo', label: 'Reclamo' },
  { value: 'felicitacion', label: 'Felicitación' },
  { value: 'otro', label: 'Otro' },
] as const;

export type SuggestionKind = (typeof SUGGESTION_KINDS)[number]['value'];

export interface SuggestionInput {
  name?: string;
  email?: string;
  kind: SuggestionKind;
  message: string;
}

/**
 * Envía un mensaje al buzón de sugerencias.
 * Endpoint público (AllowAny): POST /api/suggestions/create.
 */
export async function submitSuggestion(
  input: SuggestionInput,
): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE_URL}/suggestions/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
    cache: 'no-store',
  });
  if (!res.ok) {
    let detail = 'No pudimos enviar tu mensaje. Intenta de nuevo.';
    try {
      const data = await res.json();
      if (data?.message && typeof data.message === 'string') detail = data.message;
      else if (Array.isArray(data?.message)) detail = data.message[0];
    } catch {
      /* respuesta sin cuerpo JSON */
    }
    throw new Error(detail);
  }
  const data = (await res.json()) as { message?: string };
  return { message: data.message ?? '¡Gracias! Recibimos tu mensaje.' };
}
