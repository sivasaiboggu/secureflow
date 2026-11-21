import axios from 'axios';

const configuredUrl = (import.meta.env.VITE_API_URL as string | undefined) || undefined;
const isLocalMachine = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);

// In local development the API runs on the same machine. A deployed build
// must be given VITE_API_URL explicitly - falling back to 127.0.0.1 there
// would call the visitor's own computer and fail misleadingly.
export const apiBaseUrl: string | null =
  configuredUrl ?? (isLocalMachine ? 'http://127.0.0.1:8080/api/v1' : null);

export const apiUnavailableReason: string | null =
  apiBaseUrl === null
    ? "SecureFlow's API is not connected to this deployment, so live data is unavailable."
    : null;

export const api = axios.create({
  baseURL: apiBaseUrl ?? undefined,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  if (apiBaseUrl === null) {
    return Promise.reject(new Error(apiUnavailableReason as string));
  }
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

/** Auth keys only — theme and notification preferences share localStorage
 * and must survive signing out or an expired session. */
export function clearAuthKeys(): void {
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

function redirectToLogin(): void {
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}

// Access tokens live 30 minutes. On a 401, exchange the stored refresh
// token once and retry the original request instead of stranding the user
// on pages that keep failing. Concurrent 401s queue behind one refresh;
// if the refresh fails the session is over and the user signs in again.
let isRefreshing = false;
let refreshQueue: Array<(token: string | null) => void> = [];

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as (typeof error.config & { _retry?: boolean }) | undefined;
    const status = error.response?.status;
    const url = typeof original?.url === 'string' ? original.url : '';
    const isAuthCall = url.includes('/auth/login') || url.includes('/auth/refresh');
    if (status !== 401 || !original || original._retry || isAuthCall) {
      return Promise.reject(error);
    }

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      clearAuthKeys();
      redirectToLogin();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push((token) => {
          if (!token) {
            reject(error);
            return;
          }
          original.headers.Authorization = `Bearer ${token}`;
          resolve(api(original));
        });
      });
    }

    original._retry = true;
    isRefreshing = true;
    try {
      const res = await api.post('/auth/refresh', { refresh_token: refreshToken });
      const newToken = res.data.access_token as string;
      localStorage.setItem('token', newToken);
      if (res.data.refresh_token) {
        localStorage.setItem('refresh_token', res.data.refresh_token);
      }
      refreshQueue.forEach((cb) => cb(newToken));
      refreshQueue = [];
      original.headers.Authorization = `Bearer ${newToken}`;
      return api(original);
    } catch (refreshError) {
      refreshQueue.forEach((cb) => cb(null));
      refreshQueue = [];
      clearAuthKeys();
      redirectToLogin();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);
