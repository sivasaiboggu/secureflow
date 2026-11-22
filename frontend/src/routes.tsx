import { lazy, Suspense } from 'react';
import { Navigate, Outlet, Route, Routes } from 'react-router-dom';
import { Login } from './components/auth/Login';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { MissingPage, ReferencePage } from './components/common/ReferencePages';

const Dashboard = lazy(() => import('./components/dashboard/Dashboard').then(module => ({ default: module.Dashboard })));
const ScanList = lazy(() => import('./components/scans/ScanList').then(module => ({ default: module.ScanList })));
const VulnerabilityDetails = lazy(() => import('./components/vulnerabilities/VulnerabilityDetails').then(module => ({ default: module.VulnerabilityDetails })));
const PredictiveAnalytics = lazy(() => import('./components/analytics/PredictiveAnalytics').then(module => ({ default: module.PredictiveAnalytics })));
const CloudAccounts = lazy(() => import('./components/settings/CloudAccounts').then(module => ({ default: module.CloudAccounts })));
const NotificationSettings = lazy(() => import('./components/settings/NotificationSettings').then(module => ({ default: module.NotificationSettings })));
const UserManagement = lazy(() => import('./components/settings/UserManagement').then(module => ({ default: module.UserManagement })));

export function AppRoutes() {
  const isAuthenticated = !!localStorage.getItem('token');
  const home = isAuthenticated ? '/dashboard' : '/login';

  return <Suspense fallback={<LoadingSpinner />}>
    <Routes>
      <Route path="/" element={<Navigate to={home} replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/privacy" element={<ReferencePage kind="privacy" returnTo={home} />} />
      <Route path="/usage" element={<ReferencePage kind="usage" returnTo={home} />} />
      <Route element={isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/scans" element={<ScanList />} />
        <Route path="/vulnerabilities" element={<VulnerabilityDetails />} />
        <Route path="/analytics" element={<PredictiveAnalytics />} />
        <Route path="/settings/accounts" element={<CloudAccounts />} />
        <Route path="/settings/notifications" element={<NotificationSettings />} />
        <Route path="/settings/users" element={<UserManagement />} />
      </Route>
      <Route path="*" element={<MissingPage returnTo={home} />} />
    </Routes>
  </Suspense>;
}
