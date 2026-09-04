/**
 * Panel de la portada del sitio: hasta `MAX_FOTOS_ACTIVAS` fotos activas, que
 * el sitio muestra escalonadas en el orden de esta lista.
 *
 * Las fotos inactivas no se borran: quedan archivadas para poder rotar la
 * portada sin volver a subirlas desde el celular.
 */
import { Image } from 'expo-image';
import { Stack, useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { API_URL } from '@/api/config';
import {
  createHeroImage,
  deleteHeroImage,
  listHeroImages,
  updateHeroImage,
  MAX_FOTOS_ACTIVAS,
  type HeroImage,
} from '@/api/homepage';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import { pickFromLibrary, takePhoto } from '@/utils/pick-image';

function photoUrl(photo: string | null): string | null {
  if (!photo) return null;
  return photo.startsWith('http') ? photo : `${API_URL}${photo}`;
}

/** Ordena como el sitio: activas primero, y dentro de cada grupo por posición. */
function ordenar(fotos: HeroImage[]): HeroImage[] {
  return [...fotos].sort((a, b) => {
    if (a.is_active !== b.is_active) return a.is_active ? -1 : 1;
    return a.position - b.position || a.id - b.id;
  });
}

export default function PortadaScreen() {
  const theme = useTheme();
  const [fotos, setFotos] = useState<HeroImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activas = fotos.filter((f) => f.is_active);
  const hayCupo = activas.length < MAX_FOTOS_ACTIVAS;

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    setError(null);
    try {
      setFotos(ordenar(await listHeroImages()));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar la portada.');
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

  /** Envuelve una acción de escritura: bloquea la UI y recarga al terminar. */
  const ejecutar = useCallback(
    async (accion: () => Promise<unknown>) => {
      setSaving(true);
      try {
        await accion();
        await load();
      } catch (e) {
        Alert.alert(
          'No se pudo guardar',
          e instanceof Error ? e.message : 'Error desconocido.',
        );
      } finally {
        setSaving(false);
      }
    },
    [load],
  );

  const subir = useCallback(
    async (desde: 'camara' | 'galeria') => {
      const imagen =
        desde === 'camara' ? await takePhoto() : (await pickFromLibrary())[0];
      if (!imagen) return;
      // Va al final: la posición de las que ya están no se toca.
      const position = fotos.reduce((max, f) => Math.max(max, f.position), 0) + 1;
      await ejecutar(() =>
        createHeroImage(imagen, { alt_text: '', caption: '', position }),
      );
    },
    [ejecutar, fotos],
  );

  const agregar = useCallback(() => {
    Alert.alert('Nueva foto de portada', '¿De dónde la sacamos?', [
      { text: 'Cámara', onPress: () => void subir('camara') },
      { text: 'Galería', onPress: () => void subir('galeria') },
      { text: 'Cancelar', style: 'cancel' },
    ]);
  }, [subir]);

  const borrar = useCallback(
    (foto: HeroImage) => {
      Alert.alert('Borrar la foto', 'Se elimina para siempre del servidor.', [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Borrar',
          style: 'destructive',
          onPress: () => void ejecutar(() => deleteHeroImage(foto.id)),
        },
      ]);
    },
    [ejecutar],
  );

  /** Intercambia la posición con la foto vecina (mover arriba/abajo). */
  const mover = useCallback(
    (indice: number, delta: -1 | 1) => {
      const lista = fotos.filter((f) => f.is_active);
      const otra = lista[indice + delta];
      const esta = lista[indice];
      if (!esta || !otra) return;
      void ejecutar(async () => {
        await updateHeroImage(esta.id, { position: otra.position });
        await updateHeroImage(otra.id, { position: esta.position });
      });
    },
    [ejecutar, fotos],
  );

  const alternarActiva = useCallback(
    (foto: HeroImage) =>
      void ejecutar(() => updateHeroImage(foto.id, { is_active: !foto.is_active })),
    [ejecutar],
  );

  const inactivas = fotos.filter((f) => !f.is_active);

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.background }]}>
      <Stack.Screen options={{ title: 'Portada' }} />

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={theme.accent} />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} />
          }
        >
          <ThemedText type="subtitle">Portada del sitio</ThemedText>
          <ThemedText type="small" themeColor="textSecondary">
            Hasta {MAX_FOTOS_ACTIVAS} fotos en pantalla. El sitio las muestra
            escalonadas en este orden.
          </ThemedText>

          {error && (
            <ThemedText type="small" themeColor="textSecondary">
              {error}
            </ThemedText>
          )}

          {activas.length === 0 && (
            <ThemedText type="small" themeColor="textSecondary">
              Todavía no hay fotos en la portada. El sitio muestra su fondo de
              respaldo hasta que subas la primera.
            </ThemedText>
          )}

          {activas.map((foto, i) => (
            <FotoRow
              key={foto.id}
              foto={foto}
              disabled={saving}
              onSubir={i > 0 ? () => mover(i, -1) : undefined}
              onBajar={i < activas.length - 1 ? () => mover(i, 1) : undefined}
              onAlternar={() => alternarActiva(foto)}
              onBorrar={() => borrar(foto)}
            />
          ))}

          <Pressable
            onPress={agregar}
            disabled={!hayCupo || saving}
            style={StyleSheet.flatten([
              styles.boton,
              { backgroundColor: theme.accent, opacity: !hayCupo || saving ? 0.5 : 1 },
            ])}
          >
            <ThemedText type="smallBold" style={{ color: theme.onAccent }}>
              + Agregar foto
            </ThemedText>
          </Pressable>

          {!hayCupo && (
            <ThemedText type="small" themeColor="textSecondary">
              Ya hay {MAX_FOTOS_ACTIVAS} fotos en la portada. Sacá una de la
              portada para poder subir otra.
            </ThemedText>
          )}

          {inactivas.length > 0 && (
            <View style={styles.archivo}>
              <ThemedText type="smallBold">Archivadas</ThemedText>
              <ThemedText type="small" themeColor="textSecondary">
                No se ven en el sitio. Podés volver a ponerlas cuando quieras.
              </ThemedText>
              {inactivas.map((foto) => (
                <FotoRow
                  key={foto.id}
                  foto={foto}
                  disabled={saving || !hayCupo}
                  onAlternar={() => alternarActiva(foto)}
                  onBorrar={() => borrar(foto)}
                />
              ))}
            </View>
          )}
        </ScrollView>
      )}
    </SafeAreaView>
  );
}

function FotoRow({
  foto,
  disabled,
  onSubir,
  onBajar,
  onAlternar,
  onBorrar,
}: {
  foto: HeroImage;
  disabled: boolean;
  onSubir?: () => void;
  onBajar?: () => void;
  onAlternar: () => void;
  onBorrar: () => void;
}) {
  const theme = useTheme();
  const uri = photoUrl(foto.image);

  return (
    <View style={[styles.row, { backgroundColor: theme.backgroundElement }]}>
      {uri ? (
        <Image source={{ uri }} style={styles.thumb} contentFit="cover" />
      ) : (
        <View style={[styles.thumb, { backgroundColor: theme.backgroundSelected }]} />
      )}

      <View style={styles.rowText}>
        <ThemedText type="small" numberOfLines={2}>
          {foto.caption || foto.alt_text || `Foto ${foto.id}`}
        </ThemedText>
        <View style={styles.acciones}>
          {onSubir && (
            <Pressable onPress={onSubir} disabled={disabled} hitSlop={8}>
              <ThemedText type="linkPrimary">↑</ThemedText>
            </Pressable>
          )}
          {onBajar && (
            <Pressable onPress={onBajar} disabled={disabled} hitSlop={8}>
              <ThemedText type="linkPrimary">↓</ThemedText>
            </Pressable>
          )}
          <Pressable onPress={onAlternar} disabled={disabled} hitSlop={8}>
            <ThemedText type="linkPrimary">
              {foto.is_active ? 'Sacar de la portada' : 'Poner en la portada'}
            </ThemedText>
          </Pressable>
          <Pressable onPress={onBorrar} disabled={disabled} hitSlop={8}>
            <ThemedText type="small" style={{ color: theme.danger }}>
              Borrar
            </ThemedText>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  list: { padding: 16, gap: 12 },
  row: { flexDirection: 'row', gap: 12, padding: 12, borderRadius: 12 },
  rowText: { flex: 1, gap: 6 },
  acciones: { flexDirection: 'row', flexWrap: 'wrap', gap: 14, alignItems: 'center' },
  thumb: { width: 64, height: 80, borderRadius: 8 },
  boton: { borderRadius: 28, paddingVertical: 14, alignItems: 'center' },
  archivo: { gap: 10, marginTop: 12 },
});
