import { Navigate, Outlet, useLocation } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { Loading } from '../components/ui';
import { ROUTES } from '../utils/constants';

/**
 * ProtectedRoute — wraps routes that require authentication.
 *
 * Behaviour:
 * - While auth is loading (initial /me check): show full-screen spinner.
 * - If not authenticated: redirect to /login, preserving the intended URL.
 * - If authenticated: render children via <Outlet />.
 *
 * @param {string[]} [allowedRoles] — if provided, only these roles may access the route.
 */
export const ProtectedRoute = ({ allowedRoles }) => {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();

  // Wait for session restore before making any routing decision.
  // This prevents the protected page from briefly flashing before redirect.
  if (loading) {
    return (
      <Loading
        variant="spinner"
        size="lg"
        fullScreen
        text="Verifying session…"
      />
    );
  }

  if (!isAuthenticated) {
    // Preserve the intended destination so we can redirect back after login.
    return (
      <Navigate
        to={ROUTES.LOGIN}
        state={{ from: location }}
        replace
      />
    );
  }

  // Role-based access (foundation for future phases)
  if (allowedRoles && user?.role && !allowedRoles.includes(user.role)) {
    return (
      <Navigate
        to={ROUTES.DASHBOARD}
        replace
      />
    );
  }

  return <Outlet />;
};

/**
 * PublicRoute — wraps routes that authenticated users should NOT access
 * (e.g. /login). Redirects authenticated users to the dashboard.
 */
export const PublicRoute = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <Loading
        variant="spinner"
        size="lg"
        fullScreen
        text="Loading…"
      />
    );
  }

  if (isAuthenticated) {
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  return <Outlet />;
};
