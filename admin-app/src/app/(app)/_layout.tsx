import { Stack } from 'expo-router';

/** Stack de pantallas protegidas (staff). El guard vive en el _layout raíz. */
export default function AppLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
