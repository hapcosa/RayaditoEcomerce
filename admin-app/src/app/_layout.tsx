import { DarkTheme, ThemeProvider } from 'expo-router';
import { Stack, useRouter, useSegments } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AuthProvider, useAuth } from '@/auth/auth-context';
import { Brand, Colors } from '@/constants/theme';

/**
 * Tema de navegacion en la paleta de la marca. Sin esto React Navigation usa
 * su gris/negro por defecto y la barra de titulo desentona con las pantallas.
 * Va fijo en oscuro, como `useTheme`.
 */
const NAV_THEME = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    primary: Colors.dark.accent,
    background: Colors.dark.background,
    card: Colors.dark.background,
    text: Colors.dark.text,
    border: Brand.carbon700,
  },
} as const;

SplashScreen.preventAutoHideAsync();

function RootNavigator() {
  const { user, loading } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    SplashScreen.hideAsync();
    const inApp = segments[0] === '(app)';
    if (!user && inApp) {
      router.replace('/login');
    } else if (user && !inApp) {
      router.replace('/(app)');
    }
  }, [user, loading, segments, router]);

  if (loading) {
    return (
      <View
        style={{
          flex: 1,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: Colors.dark.background,
        }}
      >
        <ActivityIndicator size="large" color={Brand.logoNaranjo} />
      </View>
    );
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(app)" />
      <Stack.Screen name="login" />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <ThemeProvider value={NAV_THEME}>
        <AuthProvider>
          {/* Iconos claros: el fondo de la app es el negro del logo. */}
          <StatusBar style="light" />
          <RootNavigator />
        </AuthProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
