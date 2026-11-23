import axios, { type InternalAxiosRequestConfig } from 'axios';

const configuredUrl = (import.meta.env.VITE_API_URL as string | undefined) || undefined;
const isLocalMachine = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);

// In local development the API runs on the same machine. A deployed build
// must be given VITE_API_URL explicitly - falling back to 127.0.0.1 there
// would call the visitor's own computer and fail misleadingly.
export const apiBaseUrl: string | null =
  configuredUrl ?? (isLocalMachine ? 'http://127.0.0.1:8000/api/v1' : null);

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

type SessionRequest = InternalAxiosRequestConfig & { session?: number; sessionToken?: string | null; retried?: boolean };
type SessionTokens = { access_token: string; refresh_token?: string; user?: unknown };

let sessionVersion = 0;
let refresh: { version: number; token: string; result: Promise<void> } | undefined;

api.interceptors.request.use((config: SessionRequest) => {
  if (apiBaseUrl === null) {
    return Promise.reject(new Error(apiUnavailableReason as string));
  }
  config.session = sessionVersion;
  config.sessionToken = localStorage.getItem('refresh_token');
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export function clearAuthKeys(): void {
  sessionVersion++;
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
}

export function storeSession(tokens: SessionTokens): void {
  clearAuthKeys();
  localStorage.setItem('token', tokens.access_token);
  if (tokens.refresh_token) localStorage.setItem('refresh_token', tokens.refresh_token);
  if (tokens.user) localStorage.setItem('user', JSON.stringify(tokens.user));
}

export function safeReturnTo(path: string | null): string {
  if (!path?.startsWith('/') || path.startsWith('//') || path.includes('\\')) return '/dashboard';
  try {
    const target = new URL(path, window.location.origin);
    const page = decodeURI(target.pathname).replace(/\/+$/, '').toLowerCase();
    if (target.origin !== window.location.origin || page === '/login') return '/dashboard';
    return target.pathname + target.search + target.hash;
  } catch {
    return '/dashboard';
  }
}

export function signInUrl(path: string, expired = false): string {
  const query = new URLSearchParams({ returnTo: safeReturnTo(path) });
  if (expired) query.set('expired', '1');
  return '/login?' + query;
}

function expireSession() {
  clearAuthKeys();
  const { pathname, search, hash } = window.location;
  if (pathname !== '/login') window.location.replace(signInUrl(pathname + search + hash, true));
}

function refreshSession(token: string, version: number): Promise<void> {
  if (refresh?.token === token && refresh.version === version) return refresh.result;

  const result = api.post<SessionTokens>('/auth/refresh', { refresh_token: token }).then(({ data }) => {
    if (sessionVersion !== version || localStorage.getItem('refresh_token') !== token) return;
    localStorage.setItem('token', data.access_token);
    if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
  }).finally(() => {
    if (refresh?.result === result) refresh = undefined;
  });
  refresh = { version, token, result };
  return result;
}

api.interceptors.response.use(response => response, async error => {
  const request = error.config as SessionRequest | undefined;
  if (error.response?.status !== 401 || !request || request.session !== sessionVersion ||
      request.url?.startsWith('/auth/') || request.signal?.aborted) throw error;

  const accessToken = localStorage.getItem('token');
  const sentToken = request.headers.get('Authorization');
  // A response from before a manual sign-out must never refresh that session.
  const refreshToken = localStorage.getItem('refresh_token');
  if (!accessToken || !sentToken || request.sessionToken !== refreshToken) throw error;
  const version = sessionVersion;

  if (sentToken === `Bearer ${accessToken}`) {
    if (request.retried || !refreshToken) {
      expireSession();
      throw error;
    }
    try {
      await refreshSession(refreshToken, version);
    } catch (refreshError) {
      if (sessionVersion === version && localStorage.getItem('refresh_token') === refreshToken &&
          axios.isAxiosError(refreshError) && [400, 401, 403].includes(refreshError.response?.status ?? 0)) {
        expireSession();
      }
      throw refreshError;
    }
  }
  if (request.retried || sessionVersion !== version || request.signal?.aborted || !localStorage.getItem('token')) throw error;
  request.retried = true;
  return api(request);
});
