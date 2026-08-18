'use client';

import { create } from 'zustand';
import {
  addToWishlist,
  fetchWishlist,
  removeFromWishlist,
  type WishlistItem,
} from '@/lib/wishlist';

interface WishlistStore {
  items: WishlistItem[];
  ids: number[];
  loaded: boolean;
  load: (access: string) => Promise<void>;
  add: (access: string, productId: number) => Promise<void>;
  remove: (access: string, productId: number) => Promise<void>;
  reset: () => void;
}

/**
 * Estado de la lista de deseos. No se persiste en localStorage: la fuente de
 * verdad es el backend; se carga al montar con el token de acceso.
 */
export const useWishlistStore = create<WishlistStore>((set, get) => ({
  items: [],
  ids: [],
  loaded: false,

  load: async (access) => {
    try {
      const items = await fetchWishlist(access);
      set({ items, ids: items.map((i) => i.product.id), loaded: true });
    } catch {
      set({ loaded: true });
    }
  },

  add: async (access, productId) => {
    // Optimista: reflejar de inmediato y revertir si falla.
    if (!get().ids.includes(productId)) {
      set((s) => ({ ids: [...s.ids, productId] }));
    }
    try {
      await addToWishlist(access, productId);
      await get().load(access);
    } catch {
      set((s) => ({ ids: s.ids.filter((id) => id !== productId) }));
    }
  },

  remove: async (access, productId) => {
    const prev = get().ids;
    set((s) => ({
      ids: s.ids.filter((id) => id !== productId),
      items: s.items.filter((i) => i.product.id !== productId),
    }));
    try {
      await removeFromWishlist(access, productId);
    } catch {
      set({ ids: prev });
    }
  },

  reset: () => set({ items: [], ids: [], loaded: false }),
}));
