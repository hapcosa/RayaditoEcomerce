/** Lista de productos (GET /api/admin/products/). Botón para crear uno nuevo. */
import { Image } from 'expo-image';
import { Link, useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { API_URL } from '@/api/config';
import { listProducts, type Product } from '@/api/products';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import { formatCLP } from '@/utils/money';

const STATUS_LABEL: Record<Product['status'], string> = {
  draft: 'Borrador',
  published: 'Publicado',
  archived: 'Archivado',
};

/** Las fotos vienen como ruta relativa (MEDIA_URL); las absolutizamos. */
function photoUrl(photo: string | null): string | null {
  if (!photo) return null;
  return photo.startsWith('http') ? photo : `${API_URL}${photo}`;
}

function ProductRow({ product }: { product: Product }) {
  const theme = useTheme();
  const uri = photoUrl(product.photo);
  return (
    <View style={[styles.row, { backgroundColor: theme.backgroundElement }]}>
      {uri ? (
        <Image source={{ uri }} style={styles.thumb} contentFit="cover" />
      ) : (
        <View style={[styles.thumb, { backgroundColor: theme.backgroundSelected }]} />
      )}
      <View style={styles.rowText}>
        <ThemedText type="smallBold" numberOfLines={1}>
          {product.name}
        </ThemedText>
        <ThemedText type="small">{formatCLP(product.price)}</ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          {STATUS_LABEL[product.status]}
          {product.is_featured ? ' · Destacado' : ''}
        </ThemedText>
      </View>
    </View>
  );
}

export default function ProductsListScreen() {
  const theme = useTheme();
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    setError(null);
    try {
      setProducts(await listProducts());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No se pudieron cargar los productos.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Recarga al enfocar (p. ej. tras crear un producto y volver).
  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  return (
    <SafeAreaView
      edges={['bottom']}
      style={[styles.safe, { backgroundColor: theme.background }]}
    >
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" />
        </View>
      ) : (
        <FlatList
          data={products}
          keyExtractor={(p) => String(p.id)}
          renderItem={({ item }) => <ProductRow product={item} />}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} />
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <ThemedText type="small" themeColor="textSecondary">
                {error ?? 'Todavía no hay productos. Creá el primero.'}
              </ThemedText>
            </View>
          }
          ListHeaderComponent={
            error && products.length > 0 ? (
              <ThemedText type="small" themeColor="textSecondary" style={styles.err}>
                {error}
              </ThemedText>
            ) : null
          }
        />
      )}

      <Link href="/(app)/products/new" asChild>
        <Pressable style={[styles.fab, { backgroundColor: theme.text }]} hitSlop={8}>
          <ThemedText type="smallBold" style={{ color: theme.background }}>
            + Nuevo
          </ThemedText>
        </Pressable>
      </Link>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 40 },
  list: { padding: 16, gap: 12, flexGrow: 1 },
  err: { marginBottom: 8 },
  row: {
    flexDirection: 'row',
    gap: 12,
    padding: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  thumb: { width: 56, height: 56, borderRadius: 8 },
  rowText: { flex: 1, gap: 2 },
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 28,
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderRadius: 28,
  },
});
