import { Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './components/auth/Login';
import { Dashboard } from './components/dashboard/Dashboard';
import { ScanList } from './components/scans/ScanList';
import { VulnerabilityDetails } from './components/vulnerabilities/VulnerabilityDetails';
import { PredictiveAnalytics } from './components/analytics/PredictiveAnalytics';
import { CloudAccounts } from './components/settings/CloudAccounts';
import { NotificationSettings } from './components/settings/NotificationSettings';
import { UserManagement } from './components/settings/UserManagement';

export const AppRoutes = () => {
  const isAuthenticated = () => {
    return !!localStorage.getItem('token');
  };

  const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
    return isAuthenticated() ? children : <Navigate to="/login" replace />;
  };

  return (
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
  );
};
