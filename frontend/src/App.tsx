import { Component, useEffect, useRef, type ReactNode } from 'react';
import { BrowserRouter, Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Activity, Bell, Cloud, LayoutDashboard, LogOut, ScanLine, ShieldAlert, Users } from 'lucide-react';
import { AppRoutes } from './routes';
import { ApiUnavailableBanner } from './components/common/ApiUnavailableBanner';
import { BrandMark, PageHeader } from './components/common/Workspace';
import { ThemeButton } from './components/common/ThemeButton';
import { clearAuthKeys } from './services/api';
import { ThemeProvider } from './theme/ThemeContext';
import { ToastProvider } from './components/common/ToastContext';
import '@fontsource-variable/instrument-sans/wght.css';
import './index.css';

const groups = [
  { label: 'Workspace', links: [
    { label: 'Overview', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Scans', path: '/scans', icon: ScanLine },
    { label: 'Findings', path: '/vulnerabilities', icon: ShieldAlert },
    { label: 'Analytics', path: '/analytics', icon: Activity },
  ] },
  { label: 'Settings', links: [
    { label: 'Cloud accounts', path: '/settings/accounts', icon: Cloud },
    { label: 'Notifications', path: '/settings/notifications', icon: Bell },
    { label: 'Users', path: '/settings/users', icon: Users },
  ] },
];

function Sidebar() {
  return <aside className="sidebar">
    <Link className="brand" to="/dashboard"><BrandMark /><span>SecureFlow</span></Link>
    <nav aria-label="Main navigation" className="side-navigation">
      {groups.map(({ label, links }) => <div className="nav-group" key={label}>
        <p className="nav-label">{label}</p>
        {links.map(({ label: name, path, icon: Icon }) =>
          <NavLink key={path} to={path} className="side-link"><Icon size={17} aria-hidden="true" /><span>{name}</span></NavLink>
        )}
      </div>)}
    </nav>
  </aside>;
}

function WorkspaceBar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const group = groups.find(section => section.links.some(link => link.path === pathname));
  const current = group?.links.find(link => link.path === pathname);

  return <header className="workspace-bar">
    <p className="breadcrumb"><span>{group?.label || 'Workspace'}</span>{current && <><span aria-hidden="true">/</span><strong>{current.label}</strong></>}</p>
    <div className="bar-actions">
      <ThemeButton />
      <button type="button" className="button sign-out" aria-label="Sign out" onClick={() => { clearAuthKeys(); navigate('/login'); }}>
        <LogOut size={16} aria-hidden="true" /><span>Sign out</span>
      </button>
    </div>
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
    <div className={showNav ? 'workspace' : 'public-shell'}>
      {showNav && <Sidebar />}
      <div className="workspace-content">
        {showNav && <WorkspaceBar />}
        <ApiUnavailableBanner />
        <main id="main" tabIndex={-1} ref={main}>
          <ViewBoundary key={pathname}><AppRoutes /></ViewBoundary>
        </main>
      </div>
    </div>
  </>;
}

export default function App() {
  return <ThemeProvider><ToastProvider><BrowserRouter><AppShell /></BrowserRouter></ToastProvider></ThemeProvider>;
}
