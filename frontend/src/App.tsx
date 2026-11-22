import { Component, useEffect, useRef, useState, type ReactNode } from 'react';
import { BrowserRouter, Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Activity, Bell, Cloud, ListChecks, LayoutDashboard, LogOut, ScanLine, Search, ShieldAlert, Users } from 'lucide-react';
import { AppRoutes } from './routes';
import { ApiUnavailableBanner } from './components/common/ApiUnavailableBanner';
import { BrandMark, PageHeader, Sheet } from './components/common/Workspace';
import { ThemeButton } from './components/common/ThemeButton';
import { clearAuthKeys } from './services/api';
import { ThemeProvider, useTheme } from './theme/ThemeContext';
import { ToastProvider } from './components/common/ToastContext';
import '@fontsource-variable/jetbrains-mono/wght.css';
import './index.css';

const groups = [
  { label: 'Workspace', links: [
    { label: 'Overview', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Scans', path: '/scans', icon: ScanLine },
    { label: 'Findings', path: '/vulnerabilities', icon: ShieldAlert },
    { label: 'Policy checks', path: '/policies', icon: ListChecks },
    { label: 'Analytics', path: '/analytics', icon: Activity },
  ] },
  { label: 'Settings', links: [
    { label: 'Cloud accounts', path: '/settings/accounts', icon: Cloud },
    { label: 'Notifications', path: '/settings/notifications', icon: Bell },
    { label: 'Users', path: '/settings/users', icon: Users },
  ] },
];

function ViewPicker({ close }: { close: () => void }) {
  const [query, setQuery] = useState('');
  const matches = groups.flatMap(group => group.links).filter(link =>
    link.label.toLowerCase().includes(query.trim().toLowerCase())
  );
  return <Sheet title="Go to view" closeLabel="Close view picker" onClose={close}>
    <div className="field">
      <label htmlFor="view-picker">Find a view</label>
      <input id="view-picker" type="search" value={query} onChange={event => setQuery(event.target.value)} autoFocus />
    </div>
    {matches.length ? <ul className="view-picker-results">{matches.map(({ label, path, icon: Icon }) => <li key={path}>
      <Link className="side-link" to={path} onClick={close}><Icon size={16} aria-hidden="true" />{label}</Link>
    </li>)}</ul> : <p className="muted" role="status">No matching views.</p>}
  </Sheet>;
}

function ConsoleHeader() {
  const navigate = useNavigate();
  const [picker, setPicker] = useState(false);
  useEffect(() => {
    function shortcut(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setPicker(true);
      }
    }
    window.addEventListener('keydown', shortcut);
    return () => window.removeEventListener('keydown', shortcut);
  }, []);
  return <header className="console-header">
    <div className="console-top">
      <Link className="brand" to="/dashboard"><BrandMark /><span>SecureFlow</span></Link>
      <div className="bar-actions">
        <button type="button" className="button view-picker-button" aria-label="Go to view" aria-haspopup="dialog" onClick={() => setPicker(true)}>
          <Search size={16} aria-hidden="true" /><span>Go to</span>
        </button>
        <ThemeButton />
        <button type="button" className="button sign-out" aria-label="Sign out" onClick={() => { clearAuthKeys(); navigate('/login', { replace: true }); }}>
          <LogOut size={16} aria-hidden="true" /><span>Sign out</span>
        </button>
      </div>
    </div>
    <nav aria-label="Main navigation" className="side-navigation">
      {groups.map(({ label, links }) => <div className="nav-group" key={label}>
        {links.map(({ label: name, path, icon: Icon }) =>
          <NavLink key={path} to={path} className="side-link"><Icon size={16} aria-hidden="true" /><span>{name}</span></NavLink>
        )}
      </div>)}
    </nav>
    {picker && <ViewPicker close={() => setPicker(false)} />}
  </header>;
}

class ViewBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return <div className="page">
        <PageHeader title="This page could not open" description="Reload the page to try again." />
        <button type="button" className="button primary" onClick={() => window.location.reload()}>Reload page</button>
      </div>;
    }
    return this.props.children;
  }
}

function AppShell() {
  const { pathname } = useLocation();
  const { mode } = useTheme();
  const showNav = pathname !== '/login' && !!localStorage.getItem('token');
  const main = useRef<HTMLElement>(null);
  const previousPath = useRef(pathname);

  useEffect(() => {
    if (previousPath.current === pathname) return;
    previousPath.current = pathname;
    window.scrollTo(0, 0);
    main.current?.focus({ preventScroll: true });
  }, [pathname]);

  return <>
    <a className="skip-link" href="#main">Skip to content</a>
    <div className={showNav ? 'workspace' : 'public-shell'} data-theme={mode}>
      {showNav && <ConsoleHeader />}
      <div className="workspace-content">
        <ApiUnavailableBanner />
        <main id="main" tabIndex={-1} ref={main}>
          <ViewBoundary key={pathname}><AppRoutes /></ViewBoundary>
        </main>
      </div>
    </div>
  </>;
}

export default function App() {
  return <ThemeProvider><ToastProvider><BrowserRouter useTransitions={false}><AppShell /></BrowserRouter></ToastProvider></ThemeProvider>;
}
