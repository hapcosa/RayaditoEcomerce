/**
 * ABM de atributos y de sus enumeraciones.
 *
 * Un atributo es la definición reutilizable ("Talla", "Métrica europea",
 * "Alto"); acá se crea y se le cargan los valores. Engancharlo a una categoría
 * se hace en la pantalla de Categorías.
 *
 * `kind` decide cómo se carga el valor en cada producto: solo `select` tiene
 * una lista fija (16, 17, 18…); texto/entero/decimal los escribe el staff
 * producto por producto. `is_variant_option` solo aplica a `select` — el
 * backend lo rechaza en los demás y acá ni se ofrece.
 */
import { Stack, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Switch,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  addAttributeValue,
  createAttribute,
  deleteAttribute,
  deleteAttributeValue,
  listAttributes,
  updateAttribute,
  updateAttributeValue,
  KIND_LABEL,
  type Attribute,
  type AttributeFields,
  type AttributeKind,
  type AttributeValue,
} from '@/api/attributes';
import { ThemedText } from '@/components/themed-text';
import { Field } from '@/components/product-form';
import { useTheme } from '@/hooks/use-theme';

const KINDS: AttributeKind[] = ['select', 'text', 'integer', 'decimal'];

/** Borrador del formulario de atributo. `id` null = alta. */
type Draft = AttributeFields & { id: number | null };

const NUEVO: Draft = {
  id: null,
  name: '',
  unit: '',
  kind: 'select',
  is_variant_option: false,
  sort_order: 0,
};

function mensaje(e: unknown, fallback = 'Error desconocido.'): string {
  return e instanceof Error ? e.message : fallback;
}

export default function AttributesScreen() {
  const theme = useTheme();
  const [attrs, setAttrs] = useState<Attribute[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  /** Atributo cuya enumeración está desplegada. */
  const [abierto, setAbierto] = useState<number | null>(null);
  /** Texto del input de "agregar valor", por atributo. */
  const [nuevoValor, setNuevoValor] = useState<Record<number, string>>({});

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    setError(null);
    try {
      setAttrs(await listAttributes());
    } catch (e) {
      setError(mensaje(e, 'No se pudieron cargar los atributos.'));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const inputStyle = [
    styles.input,
    { backgroundColor: theme.backgroundElement, color: theme.text },
  ];

  async function guardar() {
    if (!draft) return;
    const name = draft.name.trim();
    if (!name) {
      Alert.alert('Falta el nombre', 'Poné un nombre (ej. Talla, Métrica europea).');
      return;
    }
    setSaving(true);
    try {
      const fields: AttributeFields = {
        name,
        unit: draft.unit.trim(),
        kind: draft.kind,
        // El backend rechaza variantes fuera de `select`; no lo mandamos igual.
        is_variant_option: draft.kind === 'select' && draft.is_variant_option,
        sort_order: draft.sort_order,
      };
      const guardado =
        draft.id == null
          ? await createAttribute(fields)
          : await updateAttribute(draft.id, fields);
      setDraft(null);
      // Recién creado y de selección: abrí la enumeración para cargar los valores.
      if (guardado.kind === 'select') setAbierto(guardado.id);
      await load();
    } catch (e) {
      Alert.alert('No se pudo guardar', mensaje(e));
    } finally {
      setSaving(false);
    }
  }

  function borrar(attr: Attribute) {
    Alert.alert(
      'Borrar atributo',
      `¿Borrar "${attr.name}" y todos sus valores? No se puede deshacer.`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Borrar',
          style: 'destructive',
          onPress: async () => {
            setSaving(true);
            try {
              await deleteAttribute(attr.id);
              if (draft?.id === attr.id) setDraft(null);
              await load();
            } catch (e) {
              // 409: hay productos o variantes usándolo.
              Alert.alert('No se pudo borrar', mensaje(e));
            } finally {
              setSaving(false);
            }
          },
        },
      ],
    );
  }

  async function agregarValor(attr: Attribute) {
    const texto = (nuevoValor[attr.id] ?? '').trim();
    if (!texto) return;
    setSaving(true);
    try {
      await addAttributeValue(attr.id, {
        value: texto,
        // Si el valor es un número (una talla), lo guardamos también como
        // número para poder ordenar 9 antes que 10.
        numeric_value: /^-?\d+([.,]\d+)?$/.test(texto) ? texto.replace(',', '.') : null,
        // Al final de la lista: así el orden de carga es el orden que se ve.
        sort_order: attr.values.length,
      });
      setNuevoValor({ ...nuevoValor, [attr.id]: '' });
      await load();
    } catch (e) {
      // 400 si el atributo no es de selección, 409 si el valor ya existe.
      Alert.alert('No se pudo agregar', mensaje(e));
    } finally {
      setSaving(false);
    }
  }

  function borrarValor(attr: Attribute, value: AttributeValue) {
    Alert.alert('Borrar valor', `¿Borrar "${value.value}" de ${attr.name}?`, [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Borrar',
        style: 'destructive',
        onPress: async () => {
          setSaving(true);
          try {
            await deleteAttributeValue(attr.id, value.id);
            await load();
          } catch (e) {
            // 409: hay productos o variantes con este valor.
            Alert.alert('No se pudo borrar', mensaje(e));
          } finally {
            setSaving(false);
          }
        },
      },
    ]);
  }

  /**
   * Mueve un valor una posición. Renumera `sort_order` por índice y patchea
   * solo los que cambian: los valores viejos vienen todos en 0 (el default) y
   * ahí el backend desempata alfabéticamente ("10" antes que "9").
   */
  async function moverValor(attr: Attribute, desde: number, hacia: number) {
    if (hacia < 0 || hacia >= attr.values.length) return;
    const orden = [...attr.values];
    const [movido] = orden.splice(desde, 1);
    orden.splice(hacia, 0, movido);
    setSaving(true);
    try {
      for (const [i, v] of orden.entries()) {
        if (v.sort_order !== i) await updateAttributeValue(attr.id, v.id, { sort_order: i });
      }
      await load();
    } catch (e) {
      Alert.alert('No se pudo reordenar', mensaje(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.background }]}>
      <Stack.Screen options={{ title: 'Atributos' }} />

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.accent} />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.list}
          keyboardShouldPersistTaps="handled"
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} />
          }
        >
          <ThemedText type="subtitle">Atributos</ThemedText>
          <ThemedText type="small" themeColor="textSecondary">
            Definiciones reutilizables: tallas, colores, medidas. Para que
            aparezcan en un producto hay que engancharlas a su categoría desde
            Categorías.
          </ThemedText>

          {error && (
            <ThemedText type="small" themeColor="textSecondary">
              {error}
            </ThemedText>
          )}

          {draft ? (
            <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
              <ThemedText type="smallBold">
                {draft.id == null ? 'Nuevo atributo' : 'Editar atributo'}
              </ThemedText>

              <Field label="Nombre">
                <TextInput
                  style={inputStyle}
                  value={draft.name}
                  onChangeText={(t) => setDraft({ ...draft, name: t })}
                  placeholder="Métrica europea"
                  placeholderTextColor={theme.textSecondary}
                  autoFocus
                />
              </Field>

              <Field label="Cómo se carga">
                <View style={styles.chips}>
                  {KINDS.map((k) => {
                    const sel = draft.kind === k;
                    return (
                      <Pressable
                        key={k}
                        onPress={() =>
                          setDraft({
                            ...draft,
                            kind: k,
                            is_variant_option:
                              k === 'select' ? draft.is_variant_option : false,
                          })
                        }
                        style={[
                          styles.chip,
                          { backgroundColor: sel ? theme.accent : theme.backgroundSelected },
                        ]}
                      >
                        <ThemedText
                          type="small"
                          style={{ color: sel ? theme.onAccent : theme.text }}
                        >
                          {KIND_LABEL[k]}
                        </ThemedText>
                      </Pressable>
                    );
                  })}
                </View>
                <ThemedText type="small" themeColor="textSecondary">
                  {draft.kind === 'select'
                    ? 'Lista fija de valores (tallas, colores).'
                    : 'El valor se escribe en cada producto (alto, ancho, largo).'}
                </ThemedText>
              </Field>

              <Field label="Unidad (opcional)">
                <TextInput
                  style={inputStyle}
                  value={draft.unit}
                  onChangeText={(t) => setDraft({ ...draft, unit: t })}
                  placeholder="cm"
                  placeholderTextColor={theme.textSecondary}
                />
              </Field>

              {draft.kind === 'select' && (
                <View style={styles.switchRow}>
                  <View style={styles.switchText}>
                    <ThemedText type="smallBold">Genera variantes</ThemedText>
                    <ThemedText type="small" themeColor="textSecondary">
                      Cada valor pasa a ser una variante comprable con su propio
                      stock (una talla sí, un alto en cm no).
                    </ThemedText>
                  </View>
                  <Switch
                    value={draft.is_variant_option}
                    onValueChange={(v) => setDraft({ ...draft, is_variant_option: v })}
                    thumbColor={theme.accent}
                  />
                </View>
              )}

              <View style={styles.acciones}>
                <Pressable onPress={() => setDraft(null)} hitSlop={8} disabled={saving}>
                  <ThemedText type="small" themeColor="textSecondary">
                    Cancelar
                  </ThemedText>
                </Pressable>
                <Pressable
                  onPress={guardar}
                  disabled={saving}
                  style={[styles.boton, { backgroundColor: theme.accent }]}
                >
                  {saving ? (
                    <ActivityIndicator color={theme.onAccent} />
                  ) : (
                    <ThemedText type="smallBold" style={{ color: theme.onAccent }}>
                      Guardar
                    </ThemedText>
                  )}
                </Pressable>
              </View>
            </View>
          ) : (
            <Pressable
              onPress={() => setDraft(NUEVO)}
              style={[styles.boton, styles.botonAncho, { backgroundColor: theme.accent }]}
            >
              <ThemedText type="smallBold" style={{ color: theme.onAccent }}>
                + Nuevo atributo
              </ThemedText>
            </Pressable>
          )}

          {attrs.length === 0 && !error ? (
            <ThemedText type="small" themeColor="textSecondary">
              Todavía no hay atributos. Creá el primero (ej. &quot;Métrica
              europea&quot; con sus tallas).
            </ThemedText>
          ) : null}

          {attrs.map((a) => {
            const desplegado = abierto === a.id;
            return (
              <View
                key={a.id}
                style={[styles.card, { backgroundColor: theme.backgroundElement }]}
              >
                <ThemedText type="smallBold">
                  {a.name}
                  {a.unit ? ` (${a.unit})` : ''}
                </ThemedText>
                <ThemedText type="small" themeColor="textSecondary">
                  {KIND_LABEL[a.kind]}
                  {a.kind === 'select' ? ` · ${a.values.length} valor${a.values.length === 1 ? '' : 'es'}` : ''}
                  {a.is_variant_option ? ' · genera variantes' : ''}
                  {a.usage_count ? ` · en uso en ${a.usage_count}` : ''}
                </ThemedText>

                <View style={styles.acciones}>
                  {a.kind === 'select' && (
                    <Pressable
                      onPress={() => setAbierto(desplegado ? null : a.id)}
                      hitSlop={8}
                      disabled={saving}
                    >
                      <ThemedText type="linkPrimary">
                        {desplegado ? 'Ocultar valores' : 'Valores'}
                      </ThemedText>
                    </Pressable>
                  )}
                  <Pressable
                    onPress={() =>
                      setDraft({
                        id: a.id,
                        name: a.name,
                        unit: a.unit,
                        kind: a.kind,
                        is_variant_option: a.is_variant_option,
                        sort_order: a.sort_order,
                      })
                    }
                    hitSlop={8}
                    disabled={saving}
                  >
                    <ThemedText type="linkPrimary">Editar</ThemedText>
                  </Pressable>
                  <Pressable onPress={() => borrar(a)} hitSlop={8} disabled={saving}>
                    <ThemedText type="small" style={{ color: theme.danger }}>
                      Borrar
                    </ThemedText>
                  </Pressable>
                </View>

                {desplegado && a.kind === 'select' && (
                  <View style={styles.valores}>
                    {a.values.map((v, i) => (
                      <View key={v.id} style={styles.valorFila}>
                        <ThemedText type="small" style={styles.valorTexto}>
                          {v.value}
                        </ThemedText>
                        <Pressable
                          onPress={() => moverValor(a, i, i - 1)}
                          hitSlop={8}
                          disabled={saving || i === 0}
                        >
                          <ThemedText
                            type="small"
                            themeColor={i === 0 ? 'textSecondary' : 'text'}
                          >
                            ↑
                          </ThemedText>
                        </Pressable>
                        <Pressable
                          onPress={() => moverValor(a, i, i + 1)}
                          hitSlop={8}
                          disabled={saving || i === a.values.length - 1}
                        >
                          <ThemedText
                            type="small"
                            themeColor={
                              i === a.values.length - 1 ? 'textSecondary' : 'text'
                            }
                          >
                            ↓
                          </ThemedText>
                        </Pressable>
                        <Pressable
                          onPress={() => borrarValor(a, v)}
                          hitSlop={8}
                          disabled={saving}
                        >
                          <ThemedText type="small" style={{ color: theme.danger }}>
                            Borrar
                          </ThemedText>
                        </Pressable>
                      </View>
                    ))}

                    <View style={styles.valorFila}>
                      <TextInput
                        style={[...inputStyle, styles.valorInput]}
                        value={nuevoValor[a.id] ?? ''}
                        onChangeText={(t) => setNuevoValor({ ...nuevoValor, [a.id]: t })}
                        onSubmitEditing={() => agregarValor(a)}
                        placeholder="16"
                        placeholderTextColor={theme.textSecondary}
                        returnKeyType="done"
                      />
                      <Pressable
                        onPress={() => agregarValor(a)}
                        disabled={saving}
                        style={[styles.boton, { backgroundColor: theme.accent }]}
                      >
                        <ThemedText type="smallBold" style={{ color: theme.onAccent }}>
                          Agregar
                        </ThemedText>
                      </Pressable>
                    </View>
                  </View>
                )}
              </View>
            );
          })}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  list: { padding: 16, gap: 12 },
  card: { borderRadius: 12, padding: 14, gap: 10 },
  input: { borderRadius: 10, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20 },
  acciones: { flexDirection: 'row', alignItems: 'center', gap: 20 },
  boton: { borderRadius: 24, paddingVertical: 12, paddingHorizontal: 22, alignItems: 'center' },
  botonAncho: { alignSelf: 'stretch' },
  switchRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  switchText: { flex: 1, gap: 2 },
  valores: { gap: 8, paddingTop: 4 },
  valorFila: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  valorTexto: { flex: 1 },
  valorInput: { flex: 1 },
});
