'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface LocalCartItem {
  product_id: number;
  count: number;
}

interface CartStore {
  items: LocalCartItem[];
  addItem: (product_id: number) => void;
  removeItem: (product_id: number) => void;
  updateCount: (product_id: number, count: number) => void;
  clear: () => void;
}

export const useCartStore = create<CartStore>()(
  persist(
    (set) => ({
      items: [],

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

      clear: () => set({ items: [] }),
    }),
    { name: 'rayadito-cart' },
  ),
);

/** Total de unidades en el carrito (para badge del header). */
export function selectTotalItems(s: CartStore) {
  return s.items.reduce((sum, i) => sum + i.count, 0);
}
