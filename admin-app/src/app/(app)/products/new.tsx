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
  Switch,
  TextInput,
  View,
} from 'react-native';

import {
  createProduct,
  getCategories,
  type Category,
  type LocalImage,
  type ProductStatus,
} from '@/api/products';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import { pickFromLibrary, takePhoto } from '@/utils/pick-image';

const STATUS_OPTIONS: { value: ProductStatus; label: string }[] = [
  { value: 'published', label: 'Publicado' },
  { value: 'draft', label: 'Borrador' },
  { value: 'archived', label: 'Archivado' },
];

/** Solo dígitos: el precio es entero CLP. */
function digitsOnly(text: string): string {
  return text.replace(/[^0-9]/g, '');
}

export default function NewProductScreen() {
  const theme = useTheme();
  const router = useRouter();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [comparePrice, setComparePrice] = useState('');
  const [productType, setProductType] = useState('general');
  const [status, setStatus] = useState<ProductStatus>('published');
  const [isFeatured, setIsFeatured] = useState(false);
  const [photo, setPhoto] = useState<LocalImage | null>(null);

  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [loadingCats, setLoadingCats] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const cats = await getCategories();
        setCategories(cats);
        if (cats[0]) setCategoryId(cats[0].id);
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
    if (!name.trim()) return 'El nombre es obligatorio.';
    if (!description.trim()) return 'La descripción es obligatoria.';
    if (!price) return 'El precio es obligatorio.';
    if (categoryId == null) return 'Elegí una categoría.';
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
        name: name.trim(),
        description: description.trim(),
        price: Number(price),
        compare_price: comparePrice ? Number(comparePrice) : 0,
        category: categoryId!,
        product_type: productType.trim() || 'general',
        status,
        is_featured: isFeatured,
        photo: photo!,
      });
      router.back();
    } catch (e) {
      Alert.alert('No se pudo crear', e instanceof Error ? e.message : 'Error desconocido.');
    } finally {
      setSubmitting(false);
    }
  }

  const inputStyle = [
    styles.input,
    { backgroundColor: theme.backgroundElement, color: theme.text },
  ];

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

        <Field label="Nombre">
          <TextInput style={inputStyle} value={name} onChangeText={setName} placeholder="Anillo ágata" placeholderTextColor={theme.textSecondary} />
        </Field>

        <Field label="Descripción">
          <TextInput
            style={[inputStyle, styles.multiline]}
            value={description}
            onChangeText={setDescription}
            placeholder="Plata y ágata de Chiloé"
            placeholderTextColor={theme.textSecondary}
            multiline
          />
        </Field>

        <Field label="Precio (CLP)">
          <TextInput style={inputStyle} value={price} onChangeText={(t) => setPrice(digitsOnly(t))} keyboardType="number-pad" placeholder="25000" placeholderTextColor={theme.textSecondary} />
        </Field>

        <Field label="Precio comparación (opcional)">
          <TextInput style={inputStyle} value={comparePrice} onChangeText={(t) => setComparePrice(digitsOnly(t))} keyboardType="number-pad" placeholder="0" placeholderTextColor={theme.textSecondary} />
        </Field>

        <Field label="Tipo de producto">
          <TextInput style={inputStyle} value={productType} onChangeText={setProductType} placeholder="general" placeholderTextColor={theme.textSecondary} autoCapitalize="none" />
        </Field>

        {/* Categoría */}
        <Field label="Categoría">
          {loadingCats ? (
            <ActivityIndicator />
          ) : categories.length === 0 ? (
            <ThemedText type="small" themeColor="textSecondary">
              No hay categorías cargadas en el backend.
            </ThemedText>
          ) : (
            <View style={styles.chips}>
              {categories.map((c) => {
                const selected = c.id === categoryId;
                return (
                  <Pressable
                    key={c.id}
                    onPress={() => setCategoryId(c.id)}
                    style={[
                      styles.chip,
                      { backgroundColor: selected ? theme.text : theme.backgroundElement },
                    ]}
                  >
                    <ThemedText type="small" style={{ color: selected ? theme.background : theme.text }}>
                      {c.name}
                    </ThemedText>
                  </Pressable>
                );
              })}
            </View>
          )}
        </Field>

        {/* Estado */}
        <Field label="Estado">
          <View style={styles.chips}>
            {STATUS_OPTIONS.map((o) => {
              const selected = o.value === status;
              return (
                <Pressable
                  key={o.value}
                  onPress={() => setStatus(o.value)}
                  style={[styles.chip, { backgroundColor: selected ? theme.text : theme.backgroundElement }]}
                >
                  <ThemedText type="small" style={{ color: selected ? theme.background : theme.text }}>
                    {o.label}
                  </ThemedText>
                </Pressable>
              );
            })}
          </View>
        </Field>

        <View style={styles.switchRow}>
          <ThemedText type="smallBold">Destacado</ThemedText>
          <Switch value={isFeatured} onValueChange={setIsFeatured} />
        </View>

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

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <View style={styles.field}>
      <ThemedText type="smallBold" style={styles.label}>
        {label}
      </ThemedText>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  content: { padding: 20, gap: 16, paddingBottom: 48 },
  photoBox: { gap: 12, alignItems: 'center' },
  photo: { width: '100%', height: 220, borderRadius: 12 },
  photoEmpty: { alignItems: 'center', justifyContent: 'center' },
  photoBtns: { flexDirection: 'row', gap: 12 },
  btn: { paddingHorizontal: 20, paddingVertical: 10, borderRadius: 10 },
  field: { gap: 6 },
  label: { marginLeft: 2 },
  input: { borderRadius: 10, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16 },
  multiline: { minHeight: 90, textAlignVertical: 'top' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20 },
  switchRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 4 },
  submit: { paddingVertical: 16, borderRadius: 12, alignItems: 'center', marginTop: 8 },
});
