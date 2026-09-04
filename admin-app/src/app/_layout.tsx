import { DefaultTheme, ThemeProvider } from 'expo-router';
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
 * Va fijo en claro, como `useTheme`.
 */
const NAV_THEME = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: Colors.light.accent,
    background: Colors.light.background,
    card: Colors.light.background,
    text: Colors.light.text,
    border: Brand.piedra200,
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
          backgroundColor: Colors.light.background,
        }}
      >
        <ActivityIndicator size="large" color={Brand.tierra500} />
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
          {/* Iconos oscuros: el fondo es claro y por defecto Android los deja
              blancos, con la hora y la bateria ilegibles sobre la piedra. */}
          <StatusBar style="dark" />
          <RootNavigator />
        </AuthProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
