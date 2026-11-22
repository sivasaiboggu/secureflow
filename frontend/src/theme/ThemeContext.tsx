import { createContext, useCallback, useContext, useLayoutEffect, useState, type ReactNode } from 'react';

type ThemeMode = 'light' | 'dark';
const STORAGE_KEY = 'secureflow-theme';
const ThemeContext = createContext<{ mode: ThemeMode; toggleMode: () => void }>({
  mode: 'dark', toggleMode: () => {},
});

export function readThemeMode(): ThemeMode {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'light' ? 'light' : 'dark';
  } catch {
    return 'dark';
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState(readThemeMode);
  const toggleMode = useCallback(() => setMode(current => current === 'dark' ? 'light' : 'dark'), []);

  useLayoutEffect(() => {
    document.documentElement.dataset.theme = mode;
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch {
      // The current tab can still change theme when storage is unavailable.
    }
  }, [mode]);

  return <ThemeContext.Provider value={{ mode, toggleMode }}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);
