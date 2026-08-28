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

import {
  createProduct,
  getCategories,
  type Category,
  type LocalImage,
} from '@/api/products';
import { ProductFormFields, type ProductFormValue } from '@/components/product-form';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
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
  const router = useRouter();

  const [form, setForm] = useState<ProductFormValue>(EMPTY_FORM);
  const [photo, setPhoto] = useState<LocalImage | null>(null);

  const [categories, setCategories] = useState<Category[]>([]);
  const [loadingCats, setLoadingCats] = useState(true);
  const [submitting, setSubmitting] = useState(false);

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
      await createProduct({
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
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {/* Foto */}
        <View style={styles.photoBox}>
          {photo ? (
            <Image source={{ uri: photo.uri }} style={styles.photo} contentFit="cover" />
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
        </View>

        <ProductFormFields
          value={form}
          onChange={patch}
          categories={categories}
          loadingCats={loadingCats}
        />

        <Pressable
          style={[styles.submit, { backgroundColor: theme.text, opacity: submitting ? 0.6 : 1 }]}
          onPress={onSubmit}
          disabled={submitting}
        >
          {submitting ? (
            <ActivityIndicator color={theme.background} />
          ) : (
            <ThemedText type="smallBold" style={{ color: theme.background }}>
              Crear producto
            </ThemedText>
          )}
        </Pressable>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 20, gap: 16, paddingBottom: 48 },
  photoBox: { gap: 12, alignItems: 'center' },
  photo: { width: '100%', height: 220, borderRadius: 12 },
  photoEmpty: { alignItems: 'center', justifyContent: 'center' },
  photoBtns: { flexDirection: 'row', gap: 12 },
  btn: { paddingHorizontal: 20, paddingVertical: 10, borderRadius: 10 },
  submit: { paddingVertical: 16, borderRadius: 12, alignItems: 'center', marginTop: 8 },
});
