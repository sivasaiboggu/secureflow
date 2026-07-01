import React from 'react';
import { BrowserRouter, Link, useNavigate, useLocation } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { AppRoutes } from './routes';
import { WebGLBackground } from './components/common/WebGLBackground';
import './index.css';

// MUI theme with Nexus tokens
const nexusTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#E7FF72', contrastText: '#080b12' },
    secondary: { main: '#06B6D4' },
    error: { main: '#f87171' },
    warning: { main: '#fb923c' },
    success: { main: '#4ade80' },
    background: {
      default: '#080b12',
      paper: 'rgba(14,18,27,0.85)',
    },
    text: {
      primary: '#F4F0E8',
      secondary: '#9EA3A0',
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
          backgroundColor: 'rgba(14,18,27,0.8)',
          backdropFilter: 'blur(24px)',
          border: '0.8px solid rgba(244,240,232,0.1)',
          boxShadow: 'rgba(0,0,0,0.4) 0px 16px 48px 0px, rgba(255,255,255,0.05) 0px 1px 0px 0px inset',
        }
      }
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
      }
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '0.8px solid rgba(244,240,232,0.07)',
          color: '#F4F0E8',
        },
        head: {
          fontFamily: '"Geist Mono", monospace',
          fontSize: 10,
          fontWeight: 600,
          letterSpacing: '0.16em',
          textTransform: 'uppercase',
          color: '#9EA3A0',
        }
      }
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 10,
            background: 'rgba(255,255,255,0.04)',
            '& fieldset': { borderColor: 'rgba(244,240,232,0.15)', borderWidth: '0.8px' },
            '&:hover fieldset': { borderColor: 'rgba(244,240,232,0.3)' },
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
        root: { borderRadius: 4, background: 'rgba(255,255,255,0.08)' },
        bar: { borderRadius: 4, background: '#E7FF72' },
      },
    },
    MuiCircularProgress: {
      styleOverrides: { circle: { stroke: '#E7FF72' } },
    },
  },
});

// Nav items
const NAV_ITEMS = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Scans', path: '/scans' },
  { label: 'Vulnerabilities', path: '/vulnerabilities' },
  { label: 'AI Intelligence', path: '/analytics' },
  { label: 'Cloud Accounts', path: '/settings/accounts' },
  { label: 'Users', path: '/settings/users' },
];

const NavigationHeader: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const hasToken = !!localStorage.getItem('token');
  if (location.pathname === '/login' || !hasToken) return null;

  const handleLogout = () => { localStorage.clear(); navigate('/login'); };

  return (
    <header style={navStyles.header}>
      {/* Logo */}
      <div style={navStyles.logo}>
        <svg width="22" height="22" viewBox="0 0 40 40" fill="none">
          <polygon points="20,2 38,12 38,28 20,38 2,28 2,12" fill="none" stroke="#E7FF72" strokeWidth="1.5"/>
          <circle cx="20" cy="20" r="4.5" fill="#E7FF72"/>
        </svg>
        <span style={navStyles.logoText}>Nexus</span>
      </div>

      {/* Nav links */}
      <nav style={navStyles.nav}>
        {NAV_ITEMS.map((item) => {
          const active = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
          return (
            <Link key={item.path} to={item.path} style={{ textDecoration: 'none' }}>
              <span style={{ ...navStyles.navLink, ...(active ? navStyles.navLinkActive : {}) }}>
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <button onClick={handleLogout} style={navStyles.logoutBtn}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
          <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Logout
      </button>
    </header>
  );
};

const navStyles: Record<string, React.CSSProperties> = {
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 32,
    padding: '0 32px',
    height: 56,
    background: 'rgba(8,11,18,0.85)',
    backdropFilter: 'blur(16px)',
    borderBottom: '0.8px solid rgba(244,240,232,0.08)',
    position: 'sticky',
    top: 0,
    zIndex: 100,
    flexShrink: 0,
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    textDecoration: 'none',
    marginRight: 8,
  },
  logoText: {
    fontFamily: '"Geist", sans-serif',
    fontWeight: 600,
    fontSize: 16,
    letterSpacing: '-0.03em',
    color: '#F4F0E8',
  },
  nav: {
    display: 'flex',
    gap: 2,
    flex: 1,
    alignItems: 'center',
  },
  navLink: {
    display: 'inline-block',
    fontFamily: '"Geist", sans-serif',
    fontSize: 13,
    fontWeight: 400,
    color: 'rgba(158,163,160,0.8)',
    padding: '6px 12px',
    borderRadius: 8,
    transition: 'all 150ms ease',
    cursor: 'pointer',
    textDecoration: 'none',
  },
  navLinkActive: {
    color: '#F4F0E8',
    background: 'rgba(231,255,114,0.08)',
    fontWeight: 500,
  },
  logoutBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    background: 'transparent',
    border: '0.8px solid rgba(244,240,232,0.15)',
    borderRadius: 8,
    padding: '6px 12px',
    color: 'rgba(158,163,160,0.8)',
    fontSize: 12,
    fontFamily: '"Geist", sans-serif',
    cursor: 'pointer',
    transition: 'all 150ms ease',
  },
};

function App() {
  return (
    <ThemeProvider theme={nexusTheme}>
      <CssBaseline />
      <WebGLBackground />
      <BrowserRouter>
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', position: 'relative', zIndex: 1 }}>
          <NavigationHeader />
          <main style={{ flex: 1 }}>
            <AppRoutes />
          </main>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
