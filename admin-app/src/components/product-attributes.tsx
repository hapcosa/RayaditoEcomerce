/**
 * Ficha de atributos del producto: la talla del anillo, el alto de la piedra.
 *
 * Qué atributos aparecen lo decide la **categoría** elegida (propios +
 * heredados de las ancestras), así que la lista se recarga cada vez que el
 * staff cambia de categoría en el formulario. Los valores ya cargados se
 * conservan por id de atributo: cambiar de categoría y volver no los pierde.
 *
 * Acá no hay variantes: un anillo es una pieza única de una talla, así que el
 * valor va directo al producto (ver product/admin_api.py → attribute_values).
 */
import { Link } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, TextInput, View } from 'react-native';

import {
  getCategoryAttributes,
  getProductAttributes,
  type ProductAttributeField,
} from '@/api/attributes';
import { Field } from '@/components/product-form';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';

/**
 * Lo elegido por atributo. `value_id` es para los `select` (un valor de la
 * enumeración); `value` es el texto que se escribe en los libres.
 */
export type AttributeDraft = Record<number, { value_id: number | null; value: string }>;

/** Enganche de categoría visto como ficha de producto, todavía sin valor. */
function sinValor(link: {
  attribute: ProductAttributeField['attribute'];
  is_required: boolean;
  inherited_from: ProductAttributeField['inherited_from'];
}): ProductAttributeField {
  return {
    attribute: link.attribute,
    is_required: link.is_required,
    inherited_from: link.inherited_from,
    value_id: null,
    value: null,
  };
}

/**
 * Carga qué atributos aplican y mantiene lo que el staff va eligiendo.
 *
 * En edición la primera carga sale del producto (trae los valores guardados);
 * de ahí en más, y siempre en el alta, sale de la categoría elegida.
 */
export function useProductAttributes(categoryId: number | null, productId?: number) {
  const [fields, setFields] = useState<ProductAttributeField[]>([]);
  const [draft, setDraft] = useState<AttributeDraft>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const primeraCarga = useRef(true);

  useEffect(() => {
    if (categoryId == null) {
      setFields([]);
      return;
    }
    const desdeProducto = primeraCarga.current && productId != null;
    primeraCarga.current = false;

    let vivo = true;
    setLoading(true);
    (async () => {
      try {
        const data = desdeProducto
          ? await getProductAttributes(productId!)
          : (await getCategoryAttributes(categoryId)).map(sinValor);
        if (!vivo) return;
        setFields(data);
        // Solo siembra los que no tocó el staff: un cambio de categoría no
        // debe pisar lo que ya venía escribiendo.
        setDraft((prev) => {
          const next = { ...prev };
          for (const f of data) {
            if (next[f.attribute.id] === undefined) {
              next[f.attribute.id] = { value_id: f.value_id, value: f.value ?? '' };
            }
          }
          return next;
        });
        setError(null);
      } catch (e) {
        if (vivo) setError(e instanceof Error ? e.message : 'No se cargaron los atributos.');
      } finally {
        if (vivo) setLoading(false);
      }
    })();
    return () => {
      vivo = false;
    };
  }, [categoryId, productId]);

  function setValor(attributeId: number, patch: Partial<AttributeDraft[number]>) {
    setDraft((prev) => ({
      ...prev,
      [attributeId]: { ...(prev[attributeId] ?? { value_id: null, value: '' }), ...patch },
    }));
  }

  return { fields, draft, setValor, loading, error };
}

/** Cuerpo del PUT. Manda solo los atributos que la categoría tiene enganchados. */
export function attributePayload(fields: ProductAttributeField[], draft: AttributeDraft) {
  return fields.map((f) =>
    f.attribute.kind === 'select'
      ? { attribute_id: f.attribute.id, value_id: draft[f.attribute.id]?.value_id ?? null }
      : { attribute_id: f.attribute.id, value: (draft[f.attribute.id]?.value ?? '').trim() },
  );
}

/** Primer obligatorio sin cargar, o `null` si está todo. */
export function faltaAtributo(
  fields: ProductAttributeField[],
  draft: AttributeDraft,
): string | null {
  for (const f of fields) {
    if (!f.is_required) continue;
    const d = draft[f.attribute.id];
    const vacio =
      f.attribute.kind === 'select' ? d?.value_id == null : !(d?.value ?? '').trim();
    if (vacio) return `Falta cargar "${f.attribute.name}".`;
  }
  return null;
}

type Props = {
  fields: ProductAttributeField[];
  draft: AttributeDraft;
  onChange: (attributeId: number, patch: Partial<AttributeDraft[number]>) => void;
  loading: boolean;
  error: string | null;
};

export function ProductAttributeFields({ fields, draft, onChange, loading, error }: Props) {
  const theme = useTheme();

  if (loading) return <ActivityIndicator color={theme.accent} />;
  if (error) {
    return (
      <ThemedText type="small" themeColor="textSecondary">
        {error}
      </ThemedText>
    );
  }
  if (fields.length === 0) {
    return (
      <Field label="Atributos">
        <Link href="/(app)/categories" asChild>
          <Pressable hitSlop={8}>
            <ThemedText type="linkPrimary">
              Esta categoría no tiene atributos. Tocá acá para engancharle, por ejemplo, la talla.
            </ThemedText>
          </Pressable>
        </Link>
      </Field>
    );
  }

  return (
    <>
      {fields.map((f) => {
        const { attribute: a } = f;
        const d = draft[a.id];
        const label = [
          a.name,
          a.unit ? ` (${a.unit})` : '',
          f.is_required ? ' *' : '',
        ].join('');

        return (
          <Field key={a.id} label={label}>
            {a.kind === 'select' ? (
              a.values.length === 0 ? (
                <Link href="/(app)/attributes" asChild>
                  <Pressable hitSlop={8}>
                    <ThemedText type="linkPrimary">
                      "{a.name}" no tiene valores todavía. Tocá acá para cargarlos.
                    </ThemedText>
                  </Pressable>
                </Link>
              ) : (
                <View style={styles.chips}>
                  {a.values.map((v) => {
                    const selected = d?.value_id === v.id;
                    return (
                      <Pressable
                        key={v.id}
                        // Tocar el elegido lo deselecciona: así se borra el valor.
                        onPress={() =>
                          onChange(a.id, { value_id: selected ? null : v.id })
                        }
                        style={[
                          styles.chip,
                          {
                            backgroundColor: selected ? theme.accent : theme.backgroundElement,
                          },
                        ]}
                      >
                        <ThemedText
                          type="small"
                          style={{ color: selected ? theme.onAccent : theme.text }}
                        >
                          {v.value}
                        </ThemedText>
                      </Pressable>
                    );
                  })}
                </View>
              )
            ) : (
              <TextInput
                style={[
                  styles.input,
                  { backgroundColor: theme.backgroundElement, color: theme.text },
                ]}
                value={d?.value ?? ''}
                onChangeText={(t) => onChange(a.id, { value: t })}
                keyboardType={
                  a.kind === 'integer'
                    ? 'number-pad'
                    : a.kind === 'decimal'
                      ? 'numbers-and-punctuation'
                      : 'default'
                }
                placeholder={a.kind === 'decimal' ? '3,5' : a.kind === 'integer' ? '18' : ''}
                placeholderTextColor={theme.textSecondary}
              />
            )}
            {f.inherited_from && (
              <ThemedText type="small" themeColor="textSecondary">
                Heredado de {f.inherited_from.name}
              </ThemedText>
            )}
          </Field>
        );
      })}
    </>
  );
}

const styles = StyleSheet.create({
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999 },
  input: { borderRadius: 10, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16 },
});
