/**
 * Inserta un bloque de datos estructurados (JSON-LD) en el <head>/DOM.
 * Los buscadores lo leen para rich results (schema.org).
 */
export function JsonLd({ data }: { data: Record<string, unknown> }) {
  return (
    <script
      type="application/ld+json"
      // El contenido es JSON serializado por nosotros, no input del usuario.
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}
