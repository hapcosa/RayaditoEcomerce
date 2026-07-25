'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UserInfo } from '@/lib/auth';

interface AuthStore {
  access: string | null;
  refresh: string | null;
  user: UserInfo | null;
  login: (access: string, refresh: string, user: UserInfo) => void;
  logout: () => void;
  setAccess: (access: string) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      access: null,
      refresh: null,
      user: null,
      login: (access, refresh, user) => set({ access, refresh, user }),
      logout: () => set({ access: null, refresh: null, user: null }),
      setAccess: (access) => set({ access }),
    }),
    {
      name: 'rayadito-auth',
      // Evita el mismatch SSR/cliente — el cliente rehidrata manualmente.
      skipHydration: true,
    },
  ),
);
