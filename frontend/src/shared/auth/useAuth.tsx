import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react';
import { getToken, setToken } from '@/api/client';
import { loginApi, registerApi, logoutApi } from '@/api/auth';

interface AuthContextValue {
  isLoggedIn: boolean;
  isHydrated: boolean;
  isLoading: boolean;
  authExpired: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [authExpired, setAuthExpired] = useState(false);

  useEffect(() => {
    setIsLoggedIn(!!getToken());
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    function handleExpired() {
      setIsLoggedIn(false);
      setAuthExpired(true);
      setToken(null);
    }
    window.addEventListener('auth:expired', handleExpired);
    return () => window.removeEventListener('auth:expired', handleExpired);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const result = await loginApi(username, password);
      if (result.success) {
        setIsLoggedIn(true);
        setAuthExpired(false);
        return { success: true };
      }
      return { success: false, error: result.error };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const result = await registerApi(username, password);
      if (result.success) {
        setIsLoggedIn(true);
        setAuthExpired(false);
        return { success: true };
      }
      return { success: false, error: result.error };
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    logoutApi();
    setIsLoggedIn(false);
    setAuthExpired(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isLoggedIn,
        isHydrated,
        isLoading,
        authExpired,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
