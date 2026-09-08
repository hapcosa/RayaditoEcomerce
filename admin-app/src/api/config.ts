/**
 * URL base de la API DRF de Piedras Rayadito.
 *
 * Es configurable **en la app** (pantalla de login) y queda guardada en el
 * dispositivo: cambiar de servidor no exige recompilar. Eso importa porque la
 * misma app se usa contra la LAN de la casa, contra el servidor de prueba y
 * contra producción.
 *
 * El default sale de `EXPO_PUBLIC_API_URL` cuando el build la trae (dev), y si
 * no del dominio de producción, para que un APK recién instalado sirva sin
 * tener el PC al lado.
 */
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const STORAGE_KEY = 'rayadito.api.url';

/** Quita espacios y la barra final: todas las rutas empiezan con `/`. */
export function normalizeApiUrl(url: string): string {
  return url.trim().replace(/\/+$/, '');
}

export function isValidApiUrl(url: string): boolean {
  return /^https?:\/\/[^\s/]+/i.test(normalizeApiUrl(url));
}

export const DEFAULT_API_URL = normalizeApiUrl(
  process.env.EXPO_PUBLIC_API_URL ?? 'https://piedrasdelrayadito.cl',
);

let current = DEFAULT_API_URL;

/**
 * URL vigente. Es síncrona a propósito: `client.ts` y las pantallas la usan en
 * medio de armar una request. La carga desde el disco la hace `loadApiUrl()`
 * una sola vez, al arrancar (ver auth-context).
 */
export function apiUrl(): string {
  return current;
}

async function read(): Promise<string | null> {
  if (Platform.OS === 'web') return globalThis.localStorage?.getItem(STORAGE_KEY) ?? null;
  return SecureStore.getItemAsync(STORAGE_KEY);
}

async function write(value: string): Promise<void> {
  if (Platform.OS === 'web') {
    globalThis.localStorage?.setItem(STORAGE_KEY, value);
    return;
  }
  await SecureStore.setItemAsync(STORAGE_KEY, value);
}

/** Levanta la URL guardada. Si no hay ninguna (o quedó basura), usa el default. */
export async function loadApiUrl(): Promise<string> {
  try {
    const stored = await read();
    if (stored && isValidApiUrl(stored)) current = normalizeApiUrl(stored);
  } catch {
    // Un fallo del almacenamiento no puede dejar la app sin servidor.
  }
  return current;
}

export async function setApiUrl(url: string): Promise<string> {
  const limpia = normalizeApiUrl(url);
  if (!isValidApiUrl(limpia)) {
    throw new Error('La dirección tiene que empezar con http:// o https://');
  }
  current = limpia;
  await write(limpia);
  return limpia;
}
