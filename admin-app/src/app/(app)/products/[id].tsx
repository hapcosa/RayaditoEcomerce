/**
 * Edición de producto: precarga campos + foto, permite reemplazar la foto
 * principal, gestionar la galería (agregar/quitar) y eliminar el producto.
 * PATCH/DELETE a /api/admin/products/{id}/. Dinero en entero CLP.
 */
import { Image } from 'expo-image';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
} from 'react-native';

import { API_URL } from '@/api/config';
import {
  addGalleryImages,
  deleteGalleryImage,
  deleteProduct,
  getCategories,
  getProduct,
  updateProduct,
  type Category,
  type GalleryImage,
  type LocalImage,
} from '@/api/products';
import { ImageZoomViewer, type CropDest } from '@/components/image-zoom-viewer';
import { ProductFormFields, type ProductFormValue } from '@/components/product-form';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import { cropFromViewer, type ViewerTransform } from '@/utils/crop-image';
import { pickFromLibrary, takePhoto } from '@/utils/pick-image';

/** Óxido de la paleta tierra (mismo tono que el estado "rechazado"). */
const DANGER = '#A15C4A';

/** Absolutiza rutas de media relativas (MEDIA_URL). */
function photoUrl(photo: string | null): string | null {
  if (!photo) return null;
  return photo.startsWith('http') ? photo : `${API_URL}${photo}`;
}

export default function EditProductScreen() {
  const theme = useTheme();
  const router = useRouter();
  const params = useLocalSearchParams<{ id: string }>();
  const productId = Number(params.id);

  const [form, setForm] = useState<ProductFormValue | null>(null);
  const [currentPhoto, setCurrentPhoto] = useState<string | null>(null);
  const [newPhoto, setNewPhoto] = useState<LocalImage | null>(null);
  const [gallery, setGallery] = useState<GalleryImage[]>([]);

  const [categories, setCategories] = useState<Category[]>([]);
  const [loadingCats, setLoadingCats] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [addingImages, setAddingImages] = useState(false);
  const [zoomUri, setZoomUri] = useState<string | null>(null);
  const [cropping, setCropping] = useState(false);

  const patch = (p: Partial<ProductFormValue>) =>
    setForm((f) => (f ? { ...f, ...p } : f));

  useEffect(() => {
    (async () => {
      try {
        const [product, cats] = await Promise.all([
          getProduct(productId),
          getCategories(),
        ]);
        setCategories(cats);
        setForm({
          name: product.name,
          description: product.description,
          price: String(product.price),
          comparePrice: product.compare_price ? String(product.compare_price) : '',
          // 'general' es el estado heredado: no es elegible, asi que el form
          // arranca vacio y obliga a clasificar el producto antes de guardar.
          productType: product.product_type === 'general' ? null : product.product_type,
          status: product.status,
          isFeatured: product.is_featured,
          categoryId: product.category,
        });
        setCurrentPhoto(photoUrl(product.photo));
        setGallery(product.gallery);
      } catch (e) {
        setLoadError(e instanceof Error ? e.message : 'No se pudo cargar el producto.');
      } finally {
        setLoading(false);
        setLoadingCats(false);
      }
    })();
  }, [productId]);

  async function onTakePhoto() {
    const img = await takePhoto();
    if (img) setNewPhoto(img);
  }
  async function onPickPhoto() {
    const imgs = await pickFromLibrary(false);
    if (imgs[0]) setNewPhoto(imgs[0]);
  }

  async function onAddGalleryImages() {
    const imgs = await pickFromLibrary(true);
    if (imgs.length === 0) return;
    setAddingImages(true);
    try {
      const res = await addGalleryImages(productId, imgs);
      setGallery((prev) => [...prev, ...res.gallery]);
    } catch (e) {
      Alert.alert('Error', e instanceof Error ? e.message : 'No se pudieron subir las imágenes.');
    } finally {
      setAddingImages(false);
    }
  }

  function onRemoveGalleryImage(imageId: number) {
    Alert.alert('Quitar imagen', '¿Quitar esta imagen de la galería?', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Quitar',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteGalleryImage(productId, imageId);
            setGallery((prev) => prev.filter((g) => g.id !== imageId));
          } catch (e) {
            Alert.alert('Error', e instanceof Error ? e.message : 'No se pudo quitar la imagen.');
          }
        },
      },
    ]);
  }

  function openZoom(uri: string) {
    setZoomUri(uri);
  }

  function closeZoom() {
    setZoomUri(null);
  }

  /**
   * Guarda el recorte encuadrado en el visor. Según el destino elegido:
   * - `gallery`: lo sube como foto NUEVA de la galería, sin tocar la original.
   * - `main`: lo deja como foto principal (queda pendiente y se sube al tocar
   *   "Guardar cambios", igual que el reemplazo por cámara/galería).
   */
  async function onCrop(t: ViewerTransform, dest: CropDest) {
    if (!zoomUri) return;
    setCropping(true);
    try {
      const cropped = await cropFromViewer(zoomUri, t);
      if (!cropped) {
        Alert.alert('Recorte muy chico', 'Ajustá el encuadre y probá de nuevo.');
        return;
      }
      if (dest === 'main') {
        setNewPhoto(cropped);
        closeZoom();
        Alert.alert('Listo', 'El recorte quedó como foto principal. Tocá "Guardar cambios" para aplicarlo.');
      } else {
        const { gallery: created } = await addGalleryImages(productId, [cropped]);
        setGallery((prev) => [...prev, ...created]);
        closeZoom();
        Alert.alert('Recorte guardado', 'Se agregó a la galería; la foto original quedó intacta.');
      }
    } catch (e) {
      Alert.alert('No se pudo recortar', e instanceof Error ? e.message : 'Error desconocido.');
    } finally {
      setCropping(false);
    }
  }

  function validate(f: ProductFormValue): string | null {
    if (!f.name.trim()) return 'El nombre es obligatorio.';
    if (!f.description.trim()) return 'La descripción es obligatoria.';
    if (!f.price) return 'El precio es obligatorio.';
    if (f.categoryId == null) return 'Elegí una categoría.';
    if (f.productType == null) return 'Elegí el tipo: joya o piedra.';
    return null;
  }

  async function onSave() {
    if (!form) return;
    const err = validate(form);
    if (err) {
      Alert.alert('Faltan datos', err);
      return;
    }
    setSaving(true);
    try {
      await updateProduct(
        productId,
        {
          name: form.name.trim(),
          description: form.description.trim(),
          price: Number(form.price),
          compare_price: form.comparePrice ? Number(form.comparePrice) : 0,
          category: form.categoryId!,
          product_type: form.productType!,
          status: form.status,
          is_featured: form.isFeatured,
        },
        newPhoto,
      );
      router.back();
    } catch (e) {
      Alert.alert('No se pudo guardar', e instanceof Error ? e.message : 'Error desconocido.');
    } finally {
      setSaving(false);
    }
  }

  function onDelete() {
    Alert.alert('Eliminar producto', 'Esta acción no se puede deshacer. ¿Eliminar?', [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Eliminar',
        style: 'destructive',
        onPress: async () => {
          setDeleting(true);
          try {
            await deleteProduct(productId);
            router.back();
          } catch (e) {
            Alert.alert('No se pudo eliminar', e instanceof Error ? e.message : 'Error desconocido.');
            setDeleting(false);
          }
        },
      },
    ]);
  }

  if (loading) {
    return (
      <View style={[styles.center, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (loadError || !form) {
    return (
      <View style={[styles.center, { backgroundColor: theme.background }]}>
        <ThemedText type="small" themeColor="textSecondary">
          {loadError ?? 'Producto no encontrado.'}
        </ThemedText>
      </View>
    );
  }

  const photoPreview = newPhoto?.uri ?? currentPhoto;

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: theme.background }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {/* Foto principal */}
        <View style={styles.photoBox}>
          {photoPreview ? (
            <Pressable style={styles.photo} onPress={() => openZoom(photoPreview)}>
              <Image source={{ uri: photoPreview }} style={styles.photoImg} contentFit="cover" />
            </Pressable>
          ) : (
            <View style={[styles.photo, styles.photoEmpty, { backgroundColor: theme.backgroundElement }]}>
              <ThemedText type="small" themeColor="textSecondary">
                Sin foto
              </ThemedText>
            </View>
          )}
          <View style={styles.photoBtns}>
            <Pressable style={[styles.btn, { backgroundColor: theme.backgroundElement }]} onPress={onTakePhoto}>
              <ThemedText type="smallBold">Cámara</ThemedText>
            </Pressable>
            <Pressable style={[styles.btn, { backgroundColor: theme.backgroundElement }]} onPress={onPickPhoto}>
              <ThemedText type="smallBold">Reemplazar</ThemedText>
            </Pressable>
          </View>
        </View>

        <ProductFormFields
          value={form}
          onChange={patch}
          categories={categories}
          loadingCats={loadingCats}
        />

        {/* Galería */}
        <View style={styles.field}>
          <ThemedText type="smallBold" style={styles.label}>
            Galería
          </ThemedText>
          <View style={styles.galleryGrid}>
            {gallery.map((img) => {
              const uri = photoUrl(img.photos);
              return (
                <View key={img.id} style={styles.galleryItem}>
                  <Pressable
                    onPress={() => uri && openZoom(uri)}
                    style={styles.galleryImg}
                  >
                    {uri ? (
                      <Image source={{ uri }} style={styles.galleryImg} contentFit="cover" />
                    ) : (
                      <View style={[styles.galleryImg, { backgroundColor: theme.backgroundElement }]} />
                    )}
                  </Pressable>
                  <Pressable
                    style={styles.removeBadge}
                    onPress={() => onRemoveGalleryImage(img.id)}
                    hitSlop={8}
                  >
                    <ThemedText type="smallBold" style={styles.removeBadgeText}>
                      ✕
                    </ThemedText>
                  </Pressable>
                </View>
              );
            })}
            <Pressable
              style={[styles.galleryAdd, { backgroundColor: theme.backgroundElement }]}
              onPress={onAddGalleryImages}
              disabled={addingImages}
            >
              {addingImages ? (
                <ActivityIndicator />
              ) : (
                <ThemedText type="small" themeColor="textSecondary">
                  + Agregar
                </ThemedText>
              )}
            </Pressable>
          </View>
          <ThemedText type="small" themeColor="textSecondary">
            Tocá una imagen para verla o recortarla; usá ✕ para quitarla.
          </ThemedText>
        </View>

        <Pressable
          style={[styles.submit, { backgroundColor: theme.text, opacity: saving ? 0.6 : 1 }]}
          onPress={onSave}
          disabled={saving}
        >
          {saving ? (
            <ActivityIndicator color={theme.background} />
          ) : (
            <ThemedText type="smallBold" style={{ color: theme.background }}>
              Guardar cambios
            </ThemedText>
          )}
        </Pressable>

        <Pressable
          style={[styles.deleteBtn, { borderColor: DANGER, opacity: deleting ? 0.6 : 1 }]}
          onPress={onDelete}
          disabled={deleting}
        >
          {deleting ? (
            <ActivityIndicator color={DANGER} />
          ) : (
            <ThemedText type="smallBold" style={{ color: DANGER }}>
              Eliminar producto
            </ThemedText>
          )}
        </Pressable>
      </ScrollView>

      <ImageZoomViewer
        visible={zoomUri != null}
        uri={zoomUri}
        onClose={closeZoom}
        onCrop={onCrop}
        busy={cropping}
      />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  content: { padding: 20, gap: 16, paddingBottom: 48 },
  photoBox: { gap: 12, alignItems: 'center' },
  photo: { width: '100%', height: 220, borderRadius: 12 },
  photoImg: { width: '100%', height: '100%', borderRadius: 12 },
  photoEmpty: { alignItems: 'center', justifyContent: 'center' },
  photoBtns: { flexDirection: 'row', gap: 12 },
  btn: { paddingHorizontal: 20, paddingVertical: 10, borderRadius: 10 },
  field: { gap: 6 },
  label: { marginLeft: 2 },
  galleryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  galleryItem: { width: 88, height: 88 },
  galleryImg: { width: 88, height: 88, borderRadius: 10 },
  removeBadge: {
    position: 'absolute',
    top: -6,
    right: -6,
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: 'rgba(0,0,0,0.75)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  removeBadgeText: { color: '#fff', lineHeight: 18 },
  galleryAdd: {
    width: 88,
    height: 88,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submit: { paddingVertical: 16, borderRadius: 12, alignItems: 'center', marginTop: 8 },
  deleteBtn: { paddingVertical: 14, borderRadius: 12, alignItems: 'center', borderWidth: 1 },
});
