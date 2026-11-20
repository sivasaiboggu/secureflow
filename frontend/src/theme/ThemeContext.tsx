import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { ThemeProvider } from '@mui/material';
import { buildNexusTheme, type NexusMode } from './nexusTheme';

const STORAGE_KEY = 'secureflow-theme';

interface NexusThemeContextValue {
  mode: NexusMode;
  toggleMode: () => void;
}

const NexusThemeContext = createContext<NexusThemeContextValue>({ mode: 'dark', toggleMode: () => {} });

const readStoredMode = (): NexusMode => {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'light' ? 'light' : 'dark';
  } catch {
    return 'dark';
  }
};

/**
 * Owns the light/dark mode: persisted in localStorage, mirrored onto
 * <html data-theme="…"> so the CSS tokens in index.css switch with it,
 * and fed into the MUI theme so MUI components switch too.
 */
export const NexusThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mode, setMode] = useState<NexusMode>(readStoredMode);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode);
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch {
      // Private mode / blocked storage: theme still applies for the session.
    }
  }, [mode]);

  const toggleMode = useCallback(() => {
    setMode((m) => (m === 'dark' ? 'light' : 'dark'));
  }, []);

  const theme = useMemo(() => buildNexusTheme(mode), [mode]);
  const value = useMemo(() => ({ mode, toggleMode }), [mode, toggleMode]);

  return (
    <NexusThemeContext.Provider value={value}>
      <ThemeProvider theme={theme}>{children}</ThemeProvider>
    </NexusThemeContext.Provider>
  );
};

export const useNexusTheme = (): NexusThemeContextValue => useContext(NexusThemeContext);
