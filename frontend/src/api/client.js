import axios from 'axios';
import { getToken, removeToken } from '../utils/tokenStorage';

/**
 * Axios instance pre-configured with the backend API base URL.
 *
 * - baseURL from VITE_API_BASE_URL env var (falls back to '/api' for Vite dev proxy)
 * - Automatically attaches JWT Bearer token on every request
 * - Handles 401 globally: clears token and redirects to /login
 * - Guards against infinite redirect loops on the login route itself
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// ── Request Interceptor ──────────────────────────────────────────────────────
// Attach JWT to every outgoing request if one is stored.
apiClient.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response Interceptor ─────────────────────────────────────────────────────
// On 401: clear token and redirect to /login.
// Skips redirect if the failing request IS the /auth/login endpoint itself
// (wrong credentials should show an error, not redirect).
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const requestUrl = error.config?.url || '';

    const isLoginRequest =
      requestUrl.includes('/auth/login') ||
      requestUrl.includes('/auth/register');

    if (status === 401 && !isLoginRequest) {
      removeToken();
      if (window.location.pathname !== '/login') {
        window.location.replace('/login');
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
