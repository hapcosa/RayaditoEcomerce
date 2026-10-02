/**
 * `next/image` solo optimiza hosts declarados en `remotePatterns`: cualquier
 * otro devuelve 400 y la foto no se ve. La media la sirve Django, cuyo origen
 * es `NEXT_PUBLIC_BACKEND_URL` (ver lib/media.ts y docs/DEPLOY.md), así que el
 * host se deriva de esa misma variable en vez de hardcodear el dominio: los
 * forks del template no tienen que tocar este archivo.
 *
 * Con la media en un bucket (`MEDIA_STORAGE=s3`) la API devuelve URLs
 * absolutas del dominio público del bucket, que se declara aparte en
 * `NEXT_PUBLIC_MEDIA_URL`.
 */

/** Deriva un remotePattern de una URL. Null si falta o no es válida. */
function patternFrom(raw) {
  if (!raw) return null;
  try {
    const { protocol, hostname, port } = new URL(raw);
    return {
      protocol: protocol.replace(':', ''),
      hostname,
      ...(port ? { port } : {}),
    };
  } catch {
    return null;
  }
}

const configuredPatterns = [
  process.env.NEXT_PUBLIC_BACKEND_URL,
  process.env.NEXT_PUBLIC_MEDIA_URL,
]
  .map(patternFrom)
  .filter(Boolean);

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    // Media servida por Django / object storage (Fase 7).
    remotePatterns: [
      { protocol: 'http', hostname: 'localhost' },
      { protocol: 'http', hostname: '127.0.0.1' },
      { protocol: 'https', hostname: 'res.cloudinary.com' },
      ...configuredPatterns,
    ],
  },
};

export default nextConfig;
