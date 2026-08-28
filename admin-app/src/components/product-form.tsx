/**
 * Campos de formulario compartidos entre alta (`products/new`) y edición
 * (`products/[id]`) de producto. Solo los campos de texto/categoría/estado; cada
 * pantalla arma su propia sección de foto/galería y su botón de acción.
 *
 * Los precios se manejan como string en el form (input numérico) y cada pantalla
 * los convierte a entero CLP al enviar (ver AGENTS.md: dinero entero CLP).
 */
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Switch,
  TextInput,
  View,
} from 'react-native';

import type { Category, ProductStatus } from '@/api/products';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';

export const STATUS_OPTIONS: { value: ProductStatus; label: string }[] = [
  { value: 'published', label: 'Publicado' },
  { value: 'draft', label: 'Borrador' },
  { value: 'archived', label: 'Archivado' },
];

/** Solo dígitos: el precio es entero CLP. */
export function digitsOnly(text: string): string {
  return text.replace(/[^0-9]/g, '');
}

/** Estado del formulario (precios como string mientras se editan). */
export type ProductFormValue = {
  name: string;
  description: string;
  price: string;
  comparePrice: string;
  productType: string;
  status: ProductStatus;
  isFeatured: boolean;
  categoryId: number | null;
};

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <View style={styles.field}>
      <ThemedText type="smallBold" style={styles.label}>
        {label}
      </ThemedText>
      {children}
    </View>
  );
}

type Props = {
  value: ProductFormValue;
  onChange: (patch: Partial<ProductFormValue>) => void;
  categories: Category[];
  loadingCats: boolean;
};

export function ProductFormFields({ value, onChange, categories, loadingCats }: Props) {
  const theme = useTheme();
  const inputStyle = [
    styles.input,
    { backgroundColor: theme.backgroundElement, color: theme.text },
  ];

  return (
    <>
      <Field label="Nombre">
        <TextInput
          style={inputStyle}
          value={value.name}
          onChangeText={(t) => onChange({ name: t })}
          placeholder="Anillo ágata"
          placeholderTextColor={theme.textSecondary}
        />
      </Field>

      <Field label="Descripción">
        <TextInput
          style={[inputStyle, styles.multiline]}
          value={value.description}
          onChangeText={(t) => onChange({ description: t })}
          placeholder="Plata y ágata de Chiloé"
          placeholderTextColor={theme.textSecondary}
          multiline
        />
      </Field>

      <Field label="Precio (CLP)">
        <TextInput
          style={inputStyle}
          value={value.price}
          onChangeText={(t) => onChange({ price: digitsOnly(t) })}
          keyboardType="number-pad"
          placeholder="25000"
          placeholderTextColor={theme.textSecondary}
        />
      </Field>

      <Field label="Precio comparación (opcional)">
        <TextInput
          style={inputStyle}
          value={value.comparePrice}
          onChangeText={(t) => onChange({ comparePrice: digitsOnly(t) })}
          keyboardType="number-pad"
          placeholder="0"
          placeholderTextColor={theme.textSecondary}
        />
      </Field>

      <Field label="Tipo de producto">
        <TextInput
          style={inputStyle}
          value={value.productType}
          onChangeText={(t) => onChange({ productType: t })}
          placeholder="general"
          placeholderTextColor={theme.textSecondary}
          autoCapitalize="none"
        />
      </Field>

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
              const selected = c.id === value.categoryId;
              return (
                <Pressable
                  key={c.id}
                  onPress={() => onChange({ categoryId: c.id })}
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

      <Field label="Estado">
        <View style={styles.chips}>
          {STATUS_OPTIONS.map((o) => {
            const selected = o.value === value.status;
            return (
              <Pressable
                key={o.value}
                onPress={() => onChange({ status: o.value })}
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
        <Switch value={value.isFeatured} onValueChange={(v) => onChange({ isFeatured: v })} />
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  field: { gap: 6 },
  label: { marginLeft: 2 },
  input: { borderRadius: 10, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16 },
  multiline: { minHeight: 90, textAlignVertical: 'top' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20 },
  switchRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 4 },
});
