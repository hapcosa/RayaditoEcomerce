import { Link } from 'expo-router';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { DispatchSummary } from '@/components/dispatch-summary';
import { SalesSummary } from '@/components/sales-summary';
import { ThemedText } from '@/components/themed-text';
import { useAuth } from '@/auth/auth-context';
import { useAdminStats } from '@/hooks/use-admin-stats';
import { useTheme } from '@/hooks/use-theme';

export default function DashboardScreen() {
  const { user, signOut } = useAuth();
  const theme = useTheme();
  // Si los números fallan, los accesos de abajo siguen funcionando: el home no
  // puede quedar inutilizable porque el endpoint de stats se caiga.
  const { stats, loading, refreshing, error, forbidden, refresh } = useAdminStats();

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.background }]}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}
      >
        <View style={styles.header}>
          <View style={styles.headerText}>
            <ThemedText type="subtitle">Hola{user ? `, ${user.first_name}` : ''}</ThemedText>
            <ThemedText type="small" themeColor="textSecondary">
              {user?.email}
            </ThemedText>
          </View>
          <Pressable onPress={signOut} hitSlop={8}>
            <ThemedText type="linkPrimary">Salir</ThemedText>
          </Pressable>
        </View>

        {!forbidden && (
          <View style={styles.summary}>
            {loading ? (
              <ActivityIndicator color={theme.accent} />
            ) : error ? (
              <ThemedText type="small" themeColor="textSecondary">
                {error}
              </ThemedText>
            ) : stats ? (
              <>
                <DispatchSummary pending={stats.pending} />
                <SalesSummary
                  days={stats.period.days}
                  totals={stats.totals}
                  previous={stats.previous}
                />
              </>
            ) : null}
          </View>
        )}

        <View style={styles.cards}>
          <Link href="/(app)/products" asChild>
            <Pressable style={StyleSheet.flatten([styles.card, { backgroundColor: theme.backgroundElement }])}>
              <ThemedText type="default">Productos</ThemedText>
              <ThemedText type="small" themeColor="textSecondary">
                Cargar joyas con fotos y ver el catálogo
              </ThemedText>
            </Pressable>
          </Link>
          <Link href="/(app)/categories" asChild>
            <Pressable style={StyleSheet.flatten([styles.card, { backgroundColor: theme.backgroundElement }])}>
              <ThemedText type="default">Categorías</ThemedText>
              <ThemedText type="small" themeColor="textSecondary">
                Sin categorías no se puede cargar un producto
              </ThemedText>
            </Pressable>
          </Link>
          <Link href="/(app)/attributes" asChild>
            <Pressable style={StyleSheet.flatten([styles.card, { backgroundColor: theme.backgroundElement }])}>
              <ThemedText type="default">Atributos</ThemedText>
              <ThemedText type="small" themeColor="textSecondary">
                Tallas, colores y medidas que usan las categorías
              </ThemedText>
            </Pressable>
          </Link>
          <Link href="/(app)/portada" asChild>
            <Pressable style={StyleSheet.flatten([styles.card, { backgroundColor: theme.backgroundElement }])}>
              <ThemedText type="default">Portada</ThemedText>
              <ThemedText type="small" themeColor="textSecondary">
                Cambiar las fotos que abren el sitio
              </ThemedText>
            </Pressable>
          </Link>
          <Link href="/(app)/orders" asChild>
            <Pressable style={StyleSheet.flatten([styles.card, { backgroundColor: theme.backgroundElement }])}>
              <ThemedText type="default">Pedidos</ThemedText>
              <ThemedText type="small" themeColor="textSecondary">
                Ver pedidos y cambiar sus estados
              </ThemedText>
            </Pressable>
          </Link>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  scroll: { paddingBottom: 24 },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingTop: 12,
  },
  headerText: { flexShrink: 1, gap: 2 },
  summary: { paddingHorizontal: 24, paddingTop: 24, gap: 16 },
  cards: { padding: 24, gap: 16 },
  card: {
    borderRadius: 12,
    padding: 20,
    gap: 6,
  },
});
