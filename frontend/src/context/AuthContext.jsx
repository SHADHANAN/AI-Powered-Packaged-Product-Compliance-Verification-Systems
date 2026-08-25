import { createContext, useState, useEffect, useMemo } from 'react';

export const AuthContext = createContext(null);

/**
 * Provides authentication state and methods to the component tree.
 * Stores JWT token in localStorage.
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // On mount, check if we have a stored token
    if (token) {
      // In a real implementation, validate the token with the backend
      setUser({ authenticated: true });
    }
    setLoading(false);
  }, [token]);

  const login = (accessToken, userData = {}) => {
    localStorage.setItem('access_token', accessToken);
    setToken(accessToken);
    setUser({ ...userData, authenticated: true });
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: !!token,
      loading,
      login,
      logout,
    }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
