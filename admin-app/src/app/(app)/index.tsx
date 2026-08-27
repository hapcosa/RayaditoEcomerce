import { Link } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { useAuth } from '@/auth/auth-context';
import { useTheme } from '@/hooks/use-theme';

export default function DashboardScreen() {
  const { user, signOut } = useAuth();
  const theme = useTheme();

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: theme.background }]}>
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

      <View style={styles.cards}>
        <Link href="/(app)/products" asChild>
          <Pressable style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
            <ThemedText type="default">Productos</ThemedText>
            <ThemedText type="small" themeColor="textSecondary">
              Cargar joyas con fotos y ver el catálogo
            </ThemedText>
          </Pressable>
        </Link>
        <View style={[styles.card, { backgroundColor: theme.backgroundElement }]}>
          <ThemedText type="default">Pedidos</ThemedText>
          <ThemedText type="small" themeColor="textSecondary">
            Ver y cambiar estados (próximamente)
          </ThemedText>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingTop: 12,
  },
  headerText: { flexShrink: 1, gap: 2 },
  cards: { padding: 24, gap: 16 },
  card: {
    borderRadius: 12,
    padding: 20,
    gap: 6,
  },
});
