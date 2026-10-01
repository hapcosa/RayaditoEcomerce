/**
 * Bloque "Instagram" de la ficha de producto: programa la publicación del
 * producto en la cuenta de la tienda con la API oficial de Meta.
 *
 * Sin selector de fecha libre a propósito: unos pocos horarios fijos cubren el
 * uso real (ahora, la tarde, el día siguiente) sin sumar una dependencia nativa.
 */
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  Pressable,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';

import {
  cancelInstagramPost,
  getInstagramDraft,
  listInstagramPosts,
  scheduleInstagramPost,
  type InstagramDraft,
  type InstagramPost,
} from '@/api/instagram';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';

type Slot = { label: string; at: Date | null };

function at(daysAhead: number, hour: number): Date {
  const d = new Date();
  d.setDate(d.getDate() + daysAhead);
  d.setHours(hour, 0, 0, 0);
  return d;
}

function slots(): Slot[] {
  const list: Slot[] = [{ label: 'Ahora', at: null }];
  const tonight = at(0, 20);
  if (tonight.getTime() > Date.now()) list.push({ label: 'Hoy 20:00', at: tonight });
  list.push({ label: 'Mañana 12:00', at: at(1, 12) });
  list.push({ label: 'Mañana 20:00', at: at(1, 20) });
  return list;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('es-CL', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function InstagramPublisher({ productId }: { productId: number }) {
  const theme = useTheme();
  const [draft, setDraft] = useState<InstagramDraft | null>(null);
  const [last, setLast] = useState<InstagramPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [caption, setCaption] = useState('');
  const [slot, setSlot] = useState(0);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [d, posts] = await Promise.all([
        getInstagramDraft(productId),
        listInstagramPosts(productId),
      ]);
      setDraft(d);
      // La lista viene de la más reciente a la más antigua.
      setLast(posts.find((p) => p.status !== 'cancelled') ?? null);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar Instagram.');
    } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => {
    load();
  }, [load]);

  function startEditing() {
    if (!draft) return;
    setCaption(draft.caption);
    setSlot(0);
    setEditing(true);
  }

  async function onSchedule() {
    const chosen = slots()[slot] ?? slots()[0];
    setBusy(true);
    try {
      const post = await scheduleInstagramPost(productId, caption.trim(), chosen.at);
      setLast(post);
      setEditing(false);
      Alert.alert(
        'Listo',
        chosen.at
          ? `Se publicará ${formatDate(post.scheduled_for)}.`
          : 'Se publicará en Instagram en los próximos minutos.',
      );
    } catch (e) {
      Alert.alert('No se pudo programar', e instanceof Error ? e.message : 'Error desconocido.');
    } finally {
      setBusy(false);
    }
  }

  function onCancel(post: InstagramPost) {
    Alert.alert('Cancelar publicación', '¿No publicar este producto en Instagram?', [
      { text: 'Volver', style: 'cancel' },
      {
        text: 'Cancelar publicación',
        style: 'destructive',
        onPress: async () => {
          try {
            await cancelInstagramPost(post.id);
          } catch (e) {
            Alert.alert('No se pudo cancelar', e instanceof Error ? e.message : 'Error desconocido.');
          }
          load();
        },
      },
    ]);
  }

  const cardStyle = [styles.card, { backgroundColor: theme.backgroundElement }];

  if (loading) {
    return (
      <View style={cardStyle}>
        <ActivityIndicator color={theme.accent} />
      </View>
    );
  }

  if (error || !draft) {
    return (
      <View style={cardStyle}>
        <ThemedText type="smallBold">Instagram</ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          {error ?? 'No disponible.'}
        </ThemedText>
      </View>
    );
  }

  const active = last && (last.status === 'scheduled' || last.status === 'publishing');
  const canPublish = draft.configured && draft.publishable && draft.photo_count > 0 && !active;

  return (
    <View style={cardStyle}>
      <ThemedText type="smallBold">Instagram</ThemedText>

      {!draft.configured && (
        <ThemedText type="small" themeColor="textSecondary">
          Instagram aún no está conectado en el servidor.
        </ThemedText>
      )}
      {draft.configured && !draft.publishable && (
        <ThemedText type="small" themeColor="textSecondary">
          Deja el producto como "Publicado" y guarda para poder compartirlo.
        </ThemedText>
      )}

      {last && (
        <View style={styles.status}>
          {last.status === 'scheduled' && (
            <>
              <ThemedText type="small">
                Programada para {formatDate(last.scheduled_for)}.
              </ThemedText>
              <Pressable onPress={() => onCancel(last)} hitSlop={8}>
                <ThemedText type="smallBold" style={{ color: theme.danger }}>
                  Cancelar
                </ThemedText>
              </Pressable>
            </>
          )}
          {last.status === 'publishing' && (
            <ThemedText type="small">Publicando en Instagram…</ThemedText>
          )}
          {last.status === 'published' && (
            <>
              <ThemedText type="small">
                Publicada {last.published_at ? formatDate(last.published_at) : ''}.
              </ThemedText>
              {!!last.permalink && (
                <Pressable onPress={() => Linking.openURL(last.permalink)} hitSlop={8}>
                  <ThemedText type="linkPrimary">Ver en Instagram</ThemedText>
                </Pressable>
              )}
            </>
          )}
          {last.status === 'failed' && (
            <ThemedText type="small" style={{ color: theme.danger }}>
              No se pudo publicar: {last.last_error}
            </ThemedText>
          )}
        </View>
      )}

      {editing ? (
        <>
          <TextInput
            style={[styles.input, { backgroundColor: theme.background, color: theme.text }]}
            value={caption}
            onChangeText={setCaption}
            multiline
            maxLength={2200}
            placeholderTextColor={theme.textSecondary}
          />
          <ThemedText type="small" themeColor="textSecondary">
            El texto sugerido usa lo último que guardaste del producto.
            {draft.photo_count > 1 ? ` Se publican ${draft.photo_count} fotos en carrusel.` : ''}
          </ThemedText>
          <View style={styles.chips}>
            {slots().map((s, i) => (
              <Pressable
                key={s.label}
                onPress={() => setSlot(i)}
                style={[
                  styles.chip,
                  { backgroundColor: i === slot ? theme.accent : theme.backgroundSelected },
                ]}
              >
                <ThemedText
                  type="smallBold"
                  style={i === slot ? { color: theme.onAccent } : undefined}
                >
                  {s.label}
                </ThemedText>
              </Pressable>
            ))}
          </View>
          <View style={styles.row}>
            <Pressable
              style={[styles.btn, { backgroundColor: theme.backgroundSelected }]}
              onPress={() => setEditing(false)}
              disabled={busy}
            >
              <ThemedText type="smallBold">Volver</ThemedText>
            </Pressable>
            <Pressable
              style={[styles.btn, styles.grow, { backgroundColor: theme.accent, opacity: busy ? 0.6 : 1 }]}
              onPress={onSchedule}
              disabled={busy || !caption.trim()}
            >
              {busy ? (
                <ActivityIndicator color={theme.onAccent} />
              ) : (
                <ThemedText type="smallBold" style={{ color: theme.onAccent }}>
                  {slot === 0 ? 'Publicar' : 'Programar'}
                </ThemedText>
              )}
            </Pressable>
          </View>
        </>
      ) : (
        canPublish && (
          <Pressable
            style={[styles.btn, { backgroundColor: theme.accent }]}
            onPress={startEditing}
          >
            <ThemedText type="smallBold" style={{ color: theme.onAccent }}>
              {last?.status === 'published' ? 'Publicar de nuevo' : 'Publicar en Instagram'}
            </ThemedText>
          </Pressable>
        )
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: 12, padding: 16, gap: 10 },
  status: { gap: 4 },
  input: {
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    minHeight: 140,
    textAlignVertical: 'top',
  },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20 },
  row: { flexDirection: 'row', gap: 10 },
  btn: { paddingVertical: 12, paddingHorizontal: 18, borderRadius: 10, alignItems: 'center' },
  grow: { flex: 1 },
});
