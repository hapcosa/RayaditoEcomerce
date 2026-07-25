'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/lib/store/auth';
import { useCartStore } from '@/lib/store/cart';
import { apiMe, apiRefresh, apiAddCartItem } from '@/lib/auth';

/**
 * Rehidrata el store de auth desde localStorage, valida la sesión contra
 * /auth/users/me/ y, si hay un carrito guest, lo sincroniza con el backend.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // 1. Rehidratar desde localStorage (skipHydration = true en el store).
    useAuthStore.persist.rehydrate();
  }, []);

  useEffect(() => {
    async function validateSession() {
      // Leer el store DESPUÉS de rehidratar.
      const { access, refresh, user, login, logout, setAccess } =
        useAuthStore.getState();

      if (!access) return;
      if (user) return; // ya validado en esta sesión de página

      try {
        const me = await apiMe(access);
        login(access, refresh ?? '', me);
      } catch {
        // Access expirado: intentar refresh.
        if (!refresh) { logout(); return; }
        try {
          const { access: newAccess } = await apiRefresh(refresh);
          const me = await apiMe(newAccess);
          setAccess(newAccess);
          login(newAccess, refresh, me);
        } catch {
          logout();
        }
      }
    }

    // Pequeño delay para asegurar que persist.rehydrate() terminó.
    const t = setTimeout(validateSession, 50);
    return () => clearTimeout(t);
  }, []);

  return <>{children}</>;
}

/**
 * Hook que devuelve una función para sincronizar el carrito guest al backend
 * al hacer login. Debe llamarse desde el handler de login.
 */
export function useSyncGuestCart() {
  const cartItems = useCartStore((s) => s.items);
  const clearCart = useCartStore((s) => s.clear);

  return async function syncGuestCart(access: string) {
    if (cartItems.length === 0) return;
    // Añadir cada item guest al carrito del servidor (errores individuales se ignoran).
    await Promise.allSettled(
      cartItems.map((item) => apiAddCartItem(access, item.product_id)),
    );
    clearCart();
  };
}
