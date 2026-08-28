/**
 * URLs de media servidas por Django.
 *
 * La API devuelve rutas relativas a `MEDIA_URL` (`/public/photos/...`). Cuando
 * el front corre en su propio origen —hoy en dev, y mientras Next no esté
 * detrás del mismo proxy que Django— `next/image` resuelve esa ruta contra sí
 * mismo, no encuentra el archivo y responde 400: ninguna foto de producto se
 * ve. Prefijar el backend arregla eso y sigue siendo correcto cuando ambos
 * comparten dominio.
 */
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://127.0.0.1:8000';

export function mediaUrl(path: string | null | undefined): string {
  if (!path) return '';
  // Ya absoluta (object storage de Fase 7, o el backend mismo).
  if (/^https?:\/\//i.test(path)) return path;
  return `${BACKEND_URL}${path.startsWith('/') ? path : `/${path}`}`;
}
