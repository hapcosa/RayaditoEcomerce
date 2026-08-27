import { Stack } from 'expo-router';

/** Stack de productos, con header propio (título + volver). */
export default function ProductsLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: 'Productos' }} />
      <Stack.Screen name="new" options={{ title: 'Nuevo producto', presentation: 'modal' }} />
    </Stack>
  );
}
