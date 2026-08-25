import { createContext, useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { loginRequest, getMeRequest } from '../api/auth';
import { getToken, setToken, removeToken, hasToken } from '../utils/tokenStorage';
import { ROUTES } from '../utils/constants';

export const AuthContext = createContext(null);

/**
 * AuthProvider — manages the full authentication lifecycle:
 *
 *  LOGIN         → POST /auth/login → store token → GET /auth/me → redirect to dashboard
 *  PAGE REFRESH  → read token → GET /auth/me → restore session (or clear + redirect)
 *  LOGOUT        → remove token → clear user → redirect to /login
 *  EXPIRED TOKEN → 401 interceptor removes token → window.location.replace('/login')
 *
 * Exposes: user, token, isAuthenticated, loading, login(), logout(), refreshUser()
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true); // true while initial auth check runs

  // ── Restore session on mount ───────────────────────────────────────────────
  useEffect(() => {
    const restore = async () => {
      if (!hasToken()) {
        setLoading(false);
        return;
      }
      try {
        const { data } = await getMeRequest();
        setUser(data);
      } catch {
        // Token invalid / expired — clean up silently
        removeToken();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    restore();
  }, []); // runs once on mount

  // ── refreshUser — re-fetch /auth/me and update context ────────────────────
  const refreshUser = useCallback(async () => {
    if (!hasToken()) return;
    try {
      const { data } = await getMeRequest();
      setUser(data);
    } catch {
      removeToken();
      setUser(null);
    }
  }, []);

  // ── login ─────────────────────────────────────────────────────────────────
  // Called by Login page with raw credentials.
  // Returns { success, error } so the page can display inline errors.
  const login = useCallback(async (email, password) => {
    try {
      const { data } = await loginRequest(email, password);

      // Backend returns access_token (FastAPI / OAuth2 convention)
      const token = data.access_token || data.token;
      if (!token) throw new Error('No access token in response');

      setToken(token);

      // Fetch user profile immediately after storing token
      const { data: me } = await getMeRequest();
      setUser(me);

      return { success: true };
    } catch (err) {
      // Never expose raw errors to the UI
      removeToken();
      setUser(null);
      return { success: false, error: _friendlyError(err) };
    }
  }, []);

  // ── logout ────────────────────────────────────────────────────────────────
  const logout = useCallback(() => {
    removeToken();
    setUser(null);
    // Use window.location.replace so the back-button doesn't return to the
    // protected page without re-authentication.
    window.location.replace(ROUTES.LOGIN);
  }, []);

  // ── context value (memoised to avoid unnecessary re-renders) ──────────────
  const value = useMemo(
    () => ({
      user,
      token: getToken(),          // always reads live from storage
      isAuthenticated: !!user,
      loading,
      login,
      logout,
      refreshUser,
    }),
    [user, loading, login, logout, refreshUser]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// ── Private helpers ──────────────────────────────────────────────────────────

/**
 * Convert an Axios error into a user-friendly message.
 * Never surfaces stack traces or raw backend errors.
 */
function _friendlyError(err) {
  const status = err?.response?.status;

  if (!err.response) {
    return 'Unable to reach the server. Please check your connection.';
  }

  switch (status) {
    case 400:
      return err.response.data?.detail || 'Invalid request. Please check your input.';
    case 401:
      return 'Invalid email or password.';
    case 403:
      return 'You do not have permission to access this resource.';
    case 422: {
      // FastAPI validation errors come back as { detail: [{msg, loc}, ...] }
      const detail = err.response.data?.detail;
      if (Array.isArray(detail)) {
        return detail.map((d) => d.msg).join(' ');
      }
      return 'Validation error. Please check your input.';
    }
    case 500:
    case 502:
    case 503:
      return 'Server error. Please try again later.';
    default:
      return 'An unexpected error occurred. Please try again.';
  }
}
