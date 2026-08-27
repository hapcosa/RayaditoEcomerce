/**
 * URL base de la API DRF de Piedras Rayadito.
 *
 * En dev, el teléfono NO puede usar `localhost` (eso es el propio teléfono):
 * apuntá a la IP LAN de la máquina que corre Django, p. ej.
 *   EXPO_PUBLIC_API_URL=http://192.168.1.50:8000
 * Ver admin-app/.env.example.
 */
export const API_URL = (
  process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000'
).replace(/\/+$/, '');
