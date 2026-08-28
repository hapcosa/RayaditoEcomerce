import { Stack } from 'expo-router';

/** Stack de pedidos, con header propio (título + volver). */
export default function OrdersLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: 'Pedidos' }} />
      <Stack.Screen name="[id]" options={{ title: 'Pedido' }} />
    </Stack>
  );
}
