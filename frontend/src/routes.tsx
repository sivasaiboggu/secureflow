import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './components/auth/Login';
import { LoadingSpinner } from './components/common/LoadingSpinner';

// Route pages are lazy-loaded so the first paint only downloads the login
// shell; each protected page (with its MUI/Recharts weight) loads on demand.
const Dashboard = lazy(() => import('./components/dashboard/Dashboard').then(m => ({ default: m.Dashboard })));
const ScanList = lazy(() => import('./components/scans/ScanList').then(m => ({ default: m.ScanList })));
const VulnerabilityDetails = lazy(() => import('./components/vulnerabilities/VulnerabilityDetails').then(m => ({ default: m.VulnerabilityDetails })));
const PredictiveAnalytics = lazy(() => import('./components/analytics/PredictiveAnalytics').then(m => ({ default: m.PredictiveAnalytics })));
const CloudAccounts = lazy(() => import('./components/settings/CloudAccounts').then(m => ({ default: m.CloudAccounts })));
const NotificationSettings = lazy(() => import('./components/settings/NotificationSettings').then(m => ({ default: m.NotificationSettings })));
const UserManagement = lazy(() => import('./components/settings/UserManagement').then(m => ({ default: m.UserManagement })));

export const AppRoutes = () => {
  const isAuthenticated = () => {
    return !!localStorage.getItem('token');
  };

  const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
    return isAuthenticated() ? children : <Navigate to="/login" replace />;
  };

  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/scans" element={<ProtectedRoute><ScanList /></ProtectedRoute>} />
        <Route path="/vulnerabilities" element={<ProtectedRoute><VulnerabilityDetails /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><PredictiveAnalytics /></ProtectedRoute>} />
        <Route path="/settings/accounts" element={<ProtectedRoute><CloudAccounts /></ProtectedRoute>} />
        <Route path="/settings/notifications" element={<ProtectedRoute><NotificationSettings /></ProtectedRoute>} />
        <Route path="/settings/users" element={<ProtectedRoute><UserManagement /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Suspense>
  );
};
