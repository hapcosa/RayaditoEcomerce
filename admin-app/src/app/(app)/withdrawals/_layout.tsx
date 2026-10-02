import { Stack } from 'expo-router';

/** Stack de solicitudes de retracto, con header propio (título + volver). */
export default function WithdrawalsLayout() {
  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: 'Retractos' }} />
      <Stack.Screen name="[id]" options={{ title: 'Retracto' }} />
    </Stack>
  );
}
