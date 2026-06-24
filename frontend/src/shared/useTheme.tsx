import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react';

type Theme = 'dark' | 'light';

interface ThemeContextType {
  theme: Theme;
  isDark: boolean;
  isLight: boolean;
  toggleTheme: () => void;
  setDarkTheme: () => void;
  setLightTheme: () => void;
}

const STORAGE_KEY = 'theme';

const getSavedTheme = (): Theme | null => {
  if (typeof window === 'undefined') return null;
  const saved = window.localStorage.getItem(STORAGE_KEY) as Theme | null;
  return saved === 'dark' || saved === 'light' ? saved : null;
};

const getPreferredTheme = (): Theme => {
  if (typeof window === 'undefined') return 'dark';
  return getSavedTheme()
    ?? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
};

const ThemeContext = createContext<ThemeContextType>({
  theme: 'dark',
  isDark: true,
  isLight: false,
  toggleTheme: () => {},
  setDarkTheme: () => {},
  setLightTheme: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(getPreferredTheme);

  useEffect(() => {
    if (typeof document === 'undefined') return;
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => {
      if (!getSavedTheme()) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(prev => {
      const next = prev === 'dark' ? 'light' : 'dark';
      window.localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  }, []);

  const setDarkTheme = useCallback(() => {
    setTheme('dark');
    window.localStorage.setItem(STORAGE_KEY, 'dark');
  }, []);

  const setLightTheme = useCallback(() => {
    setTheme('light');
    window.localStorage.setItem(STORAGE_KEY, 'light');
  }, []);

  return (
    <ThemeContext.Provider
      value={{
        theme,
        isDark: theme === 'dark',
        isLight: theme === 'light',
        toggleTheme,
        setDarkTheme,
        setLightTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  return useContext(ThemeContext);
}
