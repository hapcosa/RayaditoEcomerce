/**
 * Carga el resumen de ventas del home y lo mantiene fresco.
 *
 * Recarga al enfocar la pantalla (p. ej. al volver de marcar un pedido como
 * enviado) y expone `refresh` para el pull-to-refresh.
 *
 * Un 403 no es un error que mostrar: significa que la cuenta no es staff, y
 * entonces el home simplemente no enseña números. Se distingue con `forbidden`.
 */
import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';

import { ApiError } from '@/api/client';
import { getAdminStats, SUMMARY_DAYS, type AdminStats } from '@/api/stats';

export type AdminStatsState = {
  stats: AdminStats | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  forbidden: boolean;
  refresh: () => void;
};

export function useAdminStats(days: number = SUMMARY_DAYS): AdminStatsState {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const load = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      setError(null);
      try {
        setStats(await getAdminStats(days));
        setForbidden(false);
      } catch (e) {
        if (e instanceof ApiError && e.status === 403) {
          setForbidden(true);
        } else {
          setError('No se pudieron cargar los números.');
        }
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [days],
  );

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  return {
    stats,
    loading,
    refreshing,
    error,
    forbidden,
    refresh: () => load(true),
  };
}
