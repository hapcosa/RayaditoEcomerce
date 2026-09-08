/**
 * ABM de categorías. Sin categorías no se puede dar de alta un producto (el
 * picker del formulario queda vacío), así que esta pantalla es el arranque de
 * un catálogo nuevo.
 *
 * El rubro (`ProductType`) es texto libre: el repo es template multi-rubro (ver
 * AGENTS.md). Los chips "Joya"/"Piedra" son atajos de esta tienda, no un enum —
 * pero solo esos dos valores hacen que el producto caiga en /joyas o /piedras.
 */
import { Stack, useFocusEffect } from 'expo-router';
import { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import {
  createCategory,
  deleteCategory,
  getCategories,
  updateCategory,
  type Category,
} from '@/api/products';
import { ThemedText } from '@/components/themed-text';
import { Field } from '@/components/product-form';
import { useTheme } from '@/hooks/use-theme';

/** Rubros de esta tienda. El campo acepta cualquier texto; esto son atajos. */
const RUBROS_SUGERIDOS = ['Joya', 'Piedra'];

/** Borrador del formulario. `id` null = alta. */
type Draft = { id: number | null; name: string; ProductType: string; parent: number | null };

const NUEVA: Draft = { id: null, name: '', ProductType: '', parent: null };

/**
 * Categorías que pueden ser madre de `id`: todas menos ella misma y su
 * descendencia (el backend rechaza el ciclo, pero mejor no ofrecerlo).
 */
function posiblesMadres(cats: Category[], id: number | null): Category[] {
  if (id == null) return cats;
  const prohibidas = new Set<number>([id]);
  // Varias pasadas: la lista viene plana y sin orden topológico.
  let crecio = true;
  while (crecio) {
    crecio = false;
    for (const c of cats) {
      if (c.parent != null && prohibidas.has(c.parent) && !prohibidas.has(c.id)) {
        prohibidas.add(c.id);
        crecio = true;
      }
    }
  }
  return cats.filter((c) => !prohibidas.has(c.id));
}

export default function CategoriesScreen() {
  const theme = useTheme();
  const [cats, setCats] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    setError(null);
    try {
      setCats(await getCategories());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudieron cargar las categorías.');
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

  const nombrePorId = useMemo(
    () => new Map(cats.map((c) => [c.id, c.name])),
    [cats],
  );

  const inputStyle = [
    styles.input,
    { backgroundColor: theme.backgroundElement, color: theme.text },
  ];

  async function guardar() {
    if (!draft) return;
    const name = draft.name.trim();
    const rubro = draft.ProductType.trim();
    if (!name) {
      Alert.alert('Falta el nombre', 'Poné un nombre para la categoría.');
      return;
    }
    if (!rubro) {
      Alert.alert('Falta el rubro', 'Indicá el rubro (ej. Joya o Piedra).');
      return;
    }
    setSaving(true);
    try {
      const fields = { name, ProductType: rubro, parent: draft.parent };
      if (draft.id == null) await createCategory(fields);
      else await updateCategory(draft.id, fields);
      setDraft(null);
      await load();
    } catch (e) {
      Alert.alert(
        'No se pudo guardar',
        e instanceof Error ? e.message : 'Error desconocido.',
      );
    } finally {
      setSaving(false);
    }
  }

  function borrar(cat: Category) {
    Alert.alert(
      'Borrar categoría',
      `¿Borrar "${cat.name}"? No se puede deshacer.`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Borrar',
          style: 'destructive',
          onPress: async () => {
            setSaving(true);
            try {
              await deleteCategory(cat.id);
              if (draft?.id === cat.id) setDraft(null);
              await load();
            } catch (e) {
              // 409: el backend no la borra si tiene productos o subcategorías.
              Alert.alert(
                'No se pudo borrar',
                e instanceof Error ? e.message : 'Error desconocido.',
              );
            } finally {
              setSaving(false);
            }
          },
        },
      ],
    );
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.background }]}>
      <Stack.Screen options={{ title: 'Categorías' }} />

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
          <ThemedText type="subtitle">Categorías</ThemedText>
          <ThemedText type="small" themeColor="textSecondary">
            Todo producto necesita una. El rubro decide la vitrina del sitio:
            &quot;Joya&quot; → /joyas, &quot;Piedra&quot; → /piedras.
          </ThemedText>

          {error && (
            <ThemedText type="small" themeColor="textSecondary">
              {error}
            </ThemedText>
          )}

          {draft ? (
            <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
              <ThemedText type="smallBold">
                {draft.id == null ? 'Nueva categoría' : 'Editar categoría'}
              </ThemedText>

              <Field label="Nombre">
                <TextInput
                  style={inputStyle}
                  value={draft.name}
                  onChangeText={(t) => setDraft({ ...draft, name: t })}
                  placeholder="Anillos"
                  placeholderTextColor={theme.textSecondary}
                  autoFocus
                />
              </Field>

              <Field label="Rubro">
                <View style={styles.chips}>
                  {RUBROS_SUGERIDOS.map((r) => {
                    const sel = draft.ProductType.trim().toLowerCase() === r.toLowerCase();
                    return (
                      <Pressable
                        key={r}
                        onPress={() => setDraft({ ...draft, ProductType: r })}
                        style={[
                          styles.chip,
                          { backgroundColor: sel ? theme.accent : theme.backgroundSelected },
                        ]}
                      >
                        <ThemedText
                          type="small"
                          style={{ color: sel ? theme.onAccent : theme.text }}
                        >
                          {r}
                        </ThemedText>
                      </Pressable>
                    );
                  })}
                </View>
                <TextInput
                  style={inputStyle}
                  value={draft.ProductType}
                  onChangeText={(t) => setDraft({ ...draft, ProductType: t })}
                  placeholder="Joya"
                  placeholderTextColor={theme.textSecondary}
                />
              </Field>

              <Field label="Cuelga de (opcional)">
                <View style={styles.chips}>
                  <Pressable
                    onPress={() => setDraft({ ...draft, parent: null })}
                    style={[
                      styles.chip,
                      {
                        backgroundColor:
                          draft.parent == null ? theme.accent : theme.backgroundSelected,
                      },
                    ]}
                  >
                    <ThemedText
                      type="small"
                      style={{ color: draft.parent == null ? theme.onAccent : theme.text }}
                    >
                      Ninguna
                    </ThemedText>
                  </Pressable>
                  {posiblesMadres(cats, draft.id).map((c) => {
                    const sel = draft.parent === c.id;
                    return (
                      <Pressable
                        key={c.id}
                        onPress={() => setDraft({ ...draft, parent: c.id })}
                        style={[
                          styles.chip,
                          { backgroundColor: sel ? theme.accent : theme.backgroundSelected },
                        ]}
                      >
                        <ThemedText
                          type="small"
                          style={{ color: sel ? theme.onAccent : theme.text }}
                        >
                          {c.name}
                        </ThemedText>
                      </Pressable>
                    );
                  })}
                </View>
              </Field>

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
              onPress={() => setDraft(NUEVA)}
              style={[styles.boton, styles.botonAncho, { backgroundColor: theme.accent }]}
            >
              <ThemedText type="smallBold" style={{ color: theme.onAccent }}>
                + Nueva categoría
              </ThemedText>
            </Pressable>
          )}

          {cats.length === 0 && !error ? (
            <ThemedText type="small" themeColor="textSecondary">
              Todavía no hay categorías. Creá la primera para poder cargar productos.
            </ThemedText>
          ) : null}

          {cats.map((c) => (
            <View
              key={c.id}
              style={[styles.card, { backgroundColor: theme.backgroundElement }]}
            >
              <ThemedText type="smallBold">{c.name}</ThemedText>
              <ThemedText type="small" themeColor="textSecondary">
                {c.ProductType || 'Sin rubro'} · {c.product_count} producto
                {c.product_count === 1 ? '' : 's'}
                {c.parent != null ? ` · dentro de ${nombrePorId.get(c.parent) ?? '—'}` : ''}
              </ThemedText>
              <View style={styles.acciones}>
                <Pressable
                  onPress={() =>
                    setDraft({
                      id: c.id,
                      name: c.name,
                      ProductType: c.ProductType,
                      parent: c.parent,
                    })
                  }
                  hitSlop={8}
                  disabled={saving}
                >
                  <ThemedText type="linkPrimary">Editar</ThemedText>
                </Pressable>
                <Pressable onPress={() => borrar(c)} hitSlop={8} disabled={saving}>
                  <ThemedText type="small" style={{ color: theme.danger }}>
                    Borrar
                  </ThemedText>
                </Pressable>
              </View>
            </View>
          ))}
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
});
