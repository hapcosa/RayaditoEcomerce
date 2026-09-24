'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface LocalCartItem {
  product_id: number;
  count: number;
}

interface CartStore {
  items: LocalCartItem[];
  /**
   * Opcion de envio elegida en el carrito, para que el checkout no la vuelva
   * a preguntar. Es solo una preferencia: el checkout la valida contra las
   * opciones vigentes y el precio real lo calcula el backend.
   */
  shippingId: number | null;
  addItem: (product_id: number) => void;
  removeItem: (product_id: number) => void;
  updateCount: (product_id: number, count: number) => void;
  setShippingId: (shippingId: number | null) => void;
  clear: () => void;
}

export const useCartStore = create<CartStore>()(
  persist(
    (set) => ({
      items: [],
      shippingId: null,

      addItem: (product_id) =>
        set((s) => {
          if (s.items.some((i) => i.product_id === product_id)) return s;
          return { items: [...s.items, { product_id, count: 1 }] };
        }),

      removeItem: (product_id) =>
        set((s) => ({ items: s.items.filter((i) => i.product_id !== product_id) })),

      updateCount: (product_id, count) =>
        set((s) => ({
          items: s.items.map((i) =>
            i.product_id === product_id ? { ...i, count: Math.max(1, count) } : i,
          ),
        })),

      setShippingId: (shippingId) => set({ shippingId }),

      clear: () => set({ items: [], shippingId: null }),
    }),
    { name: 'rayadito-cart' },
  ),
);

/** Total de unidades en el carrito (para badge del header). */
export function selectTotalItems(s: CartStore) {
  return s.items.reduce((sum, i) => sum + i.count, 0);
}
