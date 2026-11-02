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
