import { createTheme, type Theme } from '@mui/material';

export type NexusMode = 'dark' | 'light';

/**
 * Nexus MUI theme, built per colour mode. The lime accent (#E7FF72) is the
 * brand in both modes: it stays the filled-button colour (dark ink on lime
 * reads on light and dark alike), while `primary.main` — used for text,
 * icons and spinners — is a deeper lime in light mode so it stays readable.
 * Solid surfaces are expressed through the CSS tokens in index.css so plain
 * inline styles and MUI overrides share one source of truth. No surface
 * uses backdrop blur: the playbook bans frosted glass.
 */
export const buildNexusTheme = (mode: NexusMode): Theme => {
  const dark = mode === 'dark';
  return createTheme({
    palette: {
      mode,
      primary: dark
        ? { main: '#E7FF72', contrastText: '#080b12' }
        : { main: '#65A30D', contrastText: '#FFFFFF' },
      secondary: dark ? { main: '#06B6D4' } : { main: '#0891B2' },
      error: dark ? { main: '#f87171' } : { main: '#DC2626' },
      warning: dark ? { main: '#fb923c' } : { main: '#D97706' },
      success: dark ? { main: '#4ade80' } : { main: '#16A34A' },
      background: {
        default: dark ? '#080b12' : '#F4F1E9',
        paper: dark ? '#0e121b' : '#FFFFFF',
      },
      text: {
        primary: dark ? '#F4F0E8' : '#171B22',
        secondary: dark ? '#9EA3A0' : '#5A615C',
      },
    },
    typography: {
      fontFamily: '"Geist", "Inter", "Roboto", sans-serif',
      h1: { letterSpacing: '-0.05em' },
      h2: { letterSpacing: '-0.04em' },
      h3: { letterSpacing: '-0.03em' },
      h4: { letterSpacing: '-0.025em' },
      h5: { letterSpacing: '-0.02em' },
      h6: { letterSpacing: '-0.015em' },
    },
    shape: { borderRadius: 12 },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            backgroundColor: 'var(--nexus-surface)',
            border: '0.8px solid var(--nexus-border)',
            boxShadow: 'var(--nexus-shadow)',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 600,
            borderRadius: 10,
            fontFamily: '"Geist", sans-serif',
          },
          contained: {
            background: '#E7FF72',
            color: '#080b12',
            '&:hover': { background: '#d4ec5a', boxShadow: '0 8px 24px rgba(231,255,114,0.3)' },
          },
          disabled: {
            opacity: 0.45,
          },
        },
      },
      MuiSwitch: {
        styleOverrides: {
          root: { padding: 8 },
          track: {
            backgroundColor: 'var(--nexus-elevated-bg)',
            border: '0.8px solid var(--nexus-border-strong)',
            borderRadius: 12,
            opacity: 1,
          },
          thumb: { backgroundColor: 'var(--nexus-text-muted)' },
          switchBase: {
            '&.Mui-checked': {
              color: '#080b12',
              '& + .MuiSwitch-track': { backgroundColor: '#E7FF72', borderColor: '#E7FF72', opacity: 1 },
              '& .MuiSwitch-thumb': { backgroundColor: '#080b12' },
            },
          },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            fontFamily: '"Geist", sans-serif',
            border: '0.8px solid var(--nexus-border)',
            backgroundColor: 'var(--nexus-surface)',
          },
        },
      },
      MuiTableRow: {
        styleOverrides: {
          root: {
            '&:hover': { backgroundColor: 'rgba(231,255,114,0.04)' },
          },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: 'var(--nexus-surface-strong)',
            color: 'var(--nexus-text-primary)',
            border: '0.8px solid var(--nexus-border-strong)',
            borderRadius: 8,
            fontFamily: '"Geist Mono", monospace',
            fontSize: 11,
            letterSpacing: '0.04em',
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          root: {
            borderBottom: '0.8px solid var(--nexus-border-soft)',
            color: 'var(--nexus-text-primary)',
          },
          head: {
            fontFamily: '"Geist Mono", monospace',
            fontSize: 10,
            fontWeight: 600,
            letterSpacing: '0.16em',
            textTransform: 'uppercase',
            color: 'var(--nexus-text-muted)',
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 10,
              background: 'var(--nexus-input-bg)',
              '& fieldset': { borderColor: 'var(--nexus-border-strong)', borderWidth: '0.8px' },
              '&:hover fieldset': { borderColor: 'var(--nexus-text-muted)' },
              '&.Mui-focused fieldset': { borderColor: 'rgba(231,255,114,0.5)', borderWidth: '1px' },
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: { borderRadius: 6, fontFamily: '"Geist Mono", monospace', fontSize: 10, letterSpacing: '0.08em' },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: { borderRadius: 4, background: 'var(--nexus-elevated-bg)' },
          bar: { borderRadius: 4, background: 'var(--nexus-accent-bar)' },
        },
      },
      MuiCircularProgress: {
        styleOverrides: { circle: { stroke: 'var(--nexus-accent-bar)' } },
      },
      MuiSkeleton: {
        styleOverrides: {
          root: { backgroundColor: 'var(--nexus-elevated-bg)' },
        },
      },
    },
  });
};
