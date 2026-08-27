/**
 * Selección de imágenes (cámara o galería) SIN recompresión ni resize: se sube
 * el archivo original con la mayor calidad posible (decisión explícita del dueño).
 * El backend lo guarda tal cual en `photos/%y/%m`.
 */
import * as ImagePicker from 'expo-image-picker';

import type { LocalImage } from '@/api/products';

/** Deriva nombre y mime del asset; cae a jpg si el picker no los informa. */
function toLocalImage(asset: ImagePicker.ImagePickerAsset): LocalImage {
  const mimeType = asset.mimeType ?? 'image/jpeg';
  const extFromMime = mimeType.split('/')[1] ?? 'jpg';
  const name = asset.fileName ?? `producto-${Date.now()}.${extFromMime}`;
  return { uri: asset.uri, name, mimeType };
}

/** Toma una foto con la cámara. `null` si el usuario cancela o niega permiso. */
export async function takePhoto(): Promise<LocalImage | null> {
  const perm = await ImagePicker.requestCameraPermissionsAsync();
  if (!perm.granted) return null;
  // quality: 1 = sin compresión adicional del picker (máxima calidad).
  const res = await ImagePicker.launchCameraAsync({
    mediaTypes: ['images'],
    quality: 1,
  });
  if (res.canceled || !res.assets[0]) return null;
  return toLocalImage(res.assets[0]);
}

/** Elige una o varias imágenes de la galería. `[]` si cancela o niega permiso. */
export async function pickFromLibrary(multiple = false): Promise<LocalImage[]> {
  const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (!perm.granted) return [];
  const res = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images'],
    allowsMultipleSelection: multiple,
    quality: 1,
  });
  if (res.canceled) return [];
  return res.assets.map(toLocalImage);
}
