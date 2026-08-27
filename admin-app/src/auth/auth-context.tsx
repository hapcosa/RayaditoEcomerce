/**
 * Estado de autenticación staff. Login vía djoser JWT (`/auth/jwt/create`) y
 * verificación de `is_staff` con `/auth/users/me/`. Solo staff puede entrar.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';

import { apiFetch } from '@/api/client';
import { API_URL } from '@/api/config';
import { clearTokens, getAccess, saveTokens } from '@/api/tokens';

export type StaffUser = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
};

type AuthState = {
  user: StaffUser | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthState | undefined>(undefined);

async function fetchMe(): Promise<StaffUser | null> {
  const res = await apiFetch('/auth/users/me/');
  if (!res.ok) return null;
  return (await res.json()) as StaffUser;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<StaffUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const access = await getAccess();
        if (access) {
          const me = await fetchMe();
          if (me?.is_staff) setUser(me);
          else await clearTokens();
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/auth/jwt/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      throw new Error('Email o contraseña incorrectos.');
    }
    const data = (await res.json()) as { access: string; refresh: string };
    await saveTokens(data.access, data.refresh);

    const me = await fetchMe();
    if (!me) {
      await clearTokens();
      throw new Error('No se pudo obtener el perfil.');
    }
    if (!me.is_staff) {
      await clearTokens();
      throw new Error('Tu cuenta no tiene permisos de administrador.');
    }
    setUser(me);
  }, []);

  const signOut = useCallback(async () => {
    await clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>');
  return ctx;
}
