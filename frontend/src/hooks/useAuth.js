import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

/**
 * Hook to access authentication state and methods from AuthContext.
 *
 * Must be used inside <AuthProvider>.
 *
 * @returns {{
 *   user: object|null,
 *   token: string|null,
 *   isAuthenticated: boolean,
 *   loading: boolean,
 *   login: (email: string, password: string) => Promise<{success: boolean, error?: string}>,
 *   logout: () => void,
 *   refreshUser: () => Promise<void>
 * }}
 */
const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default useAuth;
