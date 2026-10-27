/**
 * Almacenamiento seguro de los tokens JWT (access + refresh).
 * Nativo: expo-secure-store (Keychain/Keystore). Web: localStorage (fallback dev).
 */
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

import { store } from '@/constants/store';

// Con el slug de la tienda: en Rayadito siguen siendo 'rayadito.jwt.*', así que
// actualizar el APK no cierra la sesión.
const ACCESS_KEY = `${store.slug}.jwt.access`;
const REFRESH_KEY = `${store.slug}.jwt.refresh`;

async function setItem(key: string, value: string): Promise<void> {
  if (Platform.OS === 'web') {
    globalThis.localStorage?.setItem(key, value);
    return;
  }
  await SecureStore.setItemAsync(key, value);
}

async function getItem(key: string): Promise<string | null> {
  if (Platform.OS === 'web') {
    return globalThis.localStorage?.getItem(key) ?? null;
  }
  return SecureStore.getItemAsync(key);
}

async function deleteItem(key: string): Promise<void> {
  if (Platform.OS === 'web') {
    globalThis.localStorage?.removeItem(key);
    return;
  }
  await SecureStore.deleteItemAsync(key);
}

export async function saveTokens(access: string, refresh: string): Promise<void> {
  await Promise.all([setItem(ACCESS_KEY, access), setItem(REFRESH_KEY, refresh)]);
}

export async function saveAccess(access: string): Promise<void> {
  await setItem(ACCESS_KEY, access);
}

export function getAccess(): Promise<string | null> {
  return getItem(ACCESS_KEY);
}

export function getRefresh(): Promise<string | null> {
  return getItem(REFRESH_KEY);
}

export async function clearTokens(): Promise<void> {
  await Promise.all([deleteItem(ACCESS_KEY), deleteItem(REFRESH_KEY)]);
}
