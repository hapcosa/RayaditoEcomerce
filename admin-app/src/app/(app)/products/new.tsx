/**
 * Alta de producto: formulario + foto de cámara/galería, subida multipart a
 * POST /api/admin/products/. Dinero en entero CLP (sin decimales).
 */
import { Image } from 'expo-image';
import { useRouter } from 'expo-router';
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
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import {
  addGalleryImages,
  createProduct,
  getCategories,
  type Category,
  type LocalImage,
} from '@/api/products';
import { ImageZoomViewer } from '@/components/image-zoom-viewer';
import { ProductFormFields, type ProductFormValue } from '@/components/product-form';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import { cropFromViewer, type ViewerTransform } from '@/utils/crop-image';
import { pickFromLibrary, takePhoto } from '@/utils/pick-image';

const EMPTY_FORM: ProductFormValue = {
  name: '',
  description: '',
  price: '',
  comparePrice: '',
  productType: null,
  status: 'published',
  isFeatured: false,
  categoryId: null,
};

export default function NewProductScreen() {
  const theme = useTheme();
  // El boton de guardar/eliminar quedaba bajo la barra de gestos del sistema.
  const insets = useSafeAreaInsets();
  const router = useRouter();

  const [form, setForm] = useState<ProductFormValue>(EMPTY_FORM);
  const [photo, setPhoto] = useState<LocalImage | null>(null);

  const [categories, setCategories] = useState<Category[]>([]);
  const [loadingCats, setLoadingCats] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  /**
   * Galería del alta. El producto todavía no existe, así que las fotos quedan
   * locales y se suben con `addGalleryImages` recién después del POST.
   */
  const [extras, setExtras] = useState<LocalImage[]>([]);

  /**
   * Encuadre, igual que en la pantalla de edición. `target` dice a qué foto se
   * le aplica el recorte: la principal, o el índice dentro de `extras`.
   */
  const [zoom, setZoom] = useState<{ uri: string; target: 'main' | number } | null>(null);
  const [cropping, setCropping] = useState(false);

  const patch = (p: Partial<ProductFormValue>) => setForm((f) => ({ ...f, ...p }));

  useEffect(() => {
    (async () => {
      try {
        const cats = await getCategories();
        setCategories(cats);
        if (cats[0]) patch({ categoryId: cats[0].id });
      } catch (e) {
        Alert.alert('Error', e instanceof Error ? e.message : 'No se cargaron las categorías.');
      } finally {
        setLoadingCats(false);
      }
    })();
  }, []);

  async function onTakePhoto() {
    const img = await takePhoto();
    if (img) setPhoto(img);
  }
  async function onPickPhoto() {
    const imgs = await pickFromLibrary(false);
    if (imgs[0]) setPhoto(imgs[0]);
  }

  async function onAddExtras() {
    const imgs = await pickFromLibrary(true);
    if (imgs.length > 0) setExtras((prev) => [...prev, ...imgs]);
  }

  function onRemoveExtra(i: number) {
    setExtras((prev) => prev.filter((_, j) => j !== i));
  }

  /** Reemplaza la foto encuadrada por su recorte; el archivo original no se toca. */
  async function onCrop(t: ViewerTransform) {
    if (!zoom) return;
    const { uri, target } = zoom;
    setCropping(true);
    try {
      const cropped = await cropFromViewer(uri, t);
      if (!cropped) {
        Alert.alert('Recorte muy chico', 'Ajustá el encuadre y probá de nuevo.');
        return;
      }
      if (target === 'main') {
        setPhoto(cropped);
      } else {
        setExtras((prev) => prev.map((img, j) => (j === target ? cropped : img)));
      }
      setZoom(null);
    } catch (e) {
      Alert.alert('No se pudo recortar', e instanceof Error ? e.message : 'Error desconocido.');
    } finally {
      setCropping(false);
    }
  }

  function validate(): string | null {
    if (!form.name.trim()) return 'El nombre es obligatorio.';
    if (!form.description.trim()) return 'La descripción es obligatoria.';
    if (!form.price) return 'El precio es obligatorio.';
    if (form.categoryId == null) return 'Elegí una categoría.';
    if (form.productType == null) return 'Elegí el tipo: joya o piedra.';
    if (!photo) return 'Agregá una foto del producto.';
    return null;
  }

  async function onSubmit() {
    const err = validate();
    if (err) {
      Alert.alert('Faltan datos', err);
      return;
    }
    setSubmitting(true);
    try {
      const created = await createProduct({
        name: form.name.trim(),
        description: form.description.trim(),
        price: Number(form.price),
        compare_price: form.comparePrice ? Number(form.comparePrice) : 0,
        category: form.categoryId!,
        product_type: form.productType!,
        status: form.status,
        is_featured: form.isFeatured,
        photo: photo!,
      });
      if (extras.length > 0) {
        // El producto ya existe: si la galería falla, no se pierde el alta.
        try {
          await addGalleryImages(created.id, extras);
        } catch (e) {
          Alert.alert(
            'Producto creado',
            `Se creó el producto, pero no se pudieron subir las fotos de galería: ${
              e instanceof Error ? e.message : 'error desconocido'
            }. Agregalas desde la pantalla de edición.`,
          );
        }
      }
      router.back();
    } catch (e) {
      Alert.alert('No se pudo crear', e instanceof Error ? e.message : 'Error desconocido.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: theme.background }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={[styles.content, { paddingBottom: 48 + insets.bottom }]}
        keyboardShouldPersistTaps="handled"
      >
        {/* Foto */}
        <View style={styles.photoBox}>
          {photo ? (
            <Pressable style={styles.photo} onPress={() => setZoom({ uri: photo.uri, target: 'main' })}>
              <Image source={{ uri: photo.uri }} style={styles.photoImg} contentFit="cover" />
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
              <ThemedText type="smallBold">Galería</ThemedText>
            </Pressable>
          </View>
          {photo && (
            <ThemedText type="small" themeColor="textSecondary">
              Tocá la foto para encuadrarla.
            </ThemedText>
          )}
        </View>

        <ProductFormFields
          value={form}
          onChange={patch}
          categories={categories}
          loadingCats={loadingCats}
        />

        {/* Galería: opcional, se sube después de crear el producto. */}
        <View style={styles.field}>
          <ThemedText type="smallBold" style={styles.label}>
            Galería
          </ThemedText>
          <View style={styles.galleryGrid}>
            {extras.map((img, i) => (
              <View key={`${img.uri}-${i}`} style={styles.galleryItem}>
                <Pressable
                  style={styles.galleryImg}
                  onPress={() => setZoom({ uri: img.uri, target: i })}
                >
                  <Image source={{ uri: img.uri }} style={styles.galleryImg} contentFit="cover" />
                </Pressable>
                <Pressable style={styles.removeBadge} onPress={() => onRemoveExtra(i)} hitSlop={8}>
                  <ThemedText type="smallBold" style={styles.removeBadgeText}>
                    ✕
                  </ThemedText>
                </Pressable>
              </View>
            ))}
            <Pressable
              style={[styles.galleryAdd, { backgroundColor: theme.backgroundElement }]}
              onPress={onAddExtras}
            >
              <ThemedText type="small" themeColor="textSecondary">
                + Agregar
              </ThemedText>
            </Pressable>
          </View>
          <ThemedText type="small" themeColor="textSecondary">
            Tocá una imagen para encuadrarla; usá ✕ para quitarla.
          </ThemedText>
        </View>

        <Pressable
          style={[styles.submit, { backgroundColor: theme.accent, opacity: submitting ? 0.6 : 1 }]}
          onPress={onSubmit}
          disabled={submitting}
        >
          {submitting ? (
            <ActivityIndicator color={theme.onAccent} />
          ) : (
            <ThemedText type="smallBold" style={{ color: theme.onAccent }}>
              Crear producto
            </ThemedText>
          )}
        </Pressable>
      </ScrollView>

      <ImageZoomViewer
        visible={zoom != null}
        uri={zoom?.uri ?? null}
        onClose={() => setZoom(null)}
        onCrop={onCrop}
        dests={['main']}
        busy={cropping}
      />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
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
});
