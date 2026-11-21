import React from 'react';
import { BrowserRouter, Link, useNavigate, useLocation } from 'react-router-dom';
import { CssBaseline } from '@mui/material';
import { LayoutDashboard, ScanSearch, ShieldAlert, BarChart3, Cloud, Users, Bell, Sun, Moon, LogOut } from 'lucide-react';
import { AppRoutes } from './routes';
import { WebGLBackground } from './components/common/WebGLBackground';
import { ApiUnavailableBanner } from './components/common/ApiUnavailableBanner';
import { NexusThemeProvider, useNexusTheme } from './theme/ThemeContext';
import { ToastProvider } from './components/common/ToastContext';
import './index.css';

// Nav items
const NAV_ITEMS = [
  { label: 'Dashboard', path: '/dashboard', Icon: LayoutDashboard },
  { label: 'Scans', path: '/scans', Icon: ScanSearch },
  { label: 'Vulnerabilities', path: '/vulnerabilities', Icon: ShieldAlert },
  { label: 'Analytics', path: '/analytics', Icon: BarChart3 },
  { label: 'Cloud Accounts', path: '/settings/accounts', Icon: Cloud },
  { label: 'Notifications', path: '/settings/notifications', Icon: Bell },
  { label: 'Users', path: '/settings/users', Icon: Users },
];

const NavigationHeader: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { mode, toggleMode } = useNexusTheme();
  const hasToken = !!localStorage.getItem('token');
  if (location.pathname === '/login' || !hasToken) return null;

  const handleLogout = () => { localStorage.clear(); navigate('/login'); };

  return (
    <header className="portfolio-nav" style={navStyles.header}>
      {/* Logo */}
      <div style={navStyles.logo}>
        <svg width="22" height="22" viewBox="0 0 40 40" fill="none">
          <polygon points="20,2 38,12 38,28 20,38 2,28 2,12" fill="none" stroke="#E7FF72" strokeWidth="1.5"/>
          <circle cx="20" cy="20" r="4.5" fill="#E7FF72"/>
        </svg>
        <span style={navStyles.logoText}>Nexus</span>
      </div>

      {/* Nav links */}
      <nav className="portfolio-nav-links" style={navStyles.nav}>
        {NAV_ITEMS.map(({ label, path, Icon }) => {
          const active = location.pathname === path || location.pathname.startsWith(path + '/');
          return (
            <Link key={path} to={path} style={{ textDecoration: 'none' }}>
              <span style={{ ...navStyles.navLink, ...(active ? navStyles.navLinkActive : {}) }}>
                <Icon size={14} strokeWidth={2} style={{ verticalAlign: '-2px', marginRight: 6 }} />
                {label}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Theme toggle */}
      <button
        onClick={toggleMode}
        aria-label={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        title={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        style={navStyles.iconBtn}
      >
        {mode === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
      </button>

      {/* Logout */}
      <button onClick={handleLogout} style={navStyles.logoutBtn}>
        <LogOut size={14} />
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
    background: 'var(--nexus-header-bg)',
    backdropFilter: 'blur(16px)',
    borderBottom: '0.8px solid var(--nexus-border)',
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
    color: 'var(--nexus-text-primary)',
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
    color: 'var(--nexus-text-secondary)',
    padding: '6px 12px',
    borderRadius: 8,
    transition: 'all 150ms ease',
    cursor: 'pointer',
    textDecoration: 'none',
    whiteSpace: 'nowrap',
  },
  navLinkActive: {
    color: 'var(--nexus-text-primary)',
    background: 'rgba(231,255,114,0.08)',
    fontWeight: 500,
  },
  iconBtn: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'transparent',
    border: '0.8px solid var(--nexus-border-strong)',
    borderRadius: 8,
    width: 30,
    height: 30,
    color: 'var(--nexus-text-secondary)',
    cursor: 'pointer',
    transition: 'all 150ms ease',
    flexShrink: 0,
  },
  logoutBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    background: 'transparent',
    border: '0.8px solid var(--nexus-border-strong)',
    borderRadius: 8,
    padding: '6px 12px',
    color: 'var(--nexus-text-secondary)',
    fontSize: 12,
    fontFamily: '"Geist", sans-serif',
    cursor: 'pointer',
    transition: 'all 150ms ease',
  },
};

const AppShell: React.FC = () => {
  const { mode } = useNexusTheme();
  return (
    <>
      <CssBaseline />
      <WebGLBackground dark={mode === 'dark'} />
      <BrowserRouter>
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', position: 'relative', zIndex: 1 }}>
          <NavigationHeader />
          <ApiUnavailableBanner />
          <main style={{ flex: 1 }}>
            <AppRoutes />
          </main>
        </div>
      </BrowserRouter>
    </>
  );
};

function App() {
  return (
    <NexusThemeProvider>
      <ToastProvider>
        <AppShell />
      </ToastProvider>
    </NexusThemeProvider>
  );
}

export default App;
