import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { MainLayout } from '../layouts';
import { AuthLayout } from '../layouts';
import { ProtectedRoute, PublicRoute } from './ProtectedRoute';

// Pages
import Dashboard    from '../pages/Dashboard';
import Upload       from '../pages/Upload';
import Verification from '../pages/Verification';
import Reports      from '../pages/Reports';
import History      from '../pages/History';
import Login        from '../pages/Login';
import NotFound     from '../pages/NotFound';

/**
 * Application route tree.
 *
 * Route protection layers:
 *
 *  PublicRoute    → /login                      (redirects to /dashboard if already authenticated)
 *  ProtectedRoute → / , /dashboard + sub-routes (redirects to /login if not authenticated)
 *
 * ProtectedRoute also handles the initial loading state so protected pages
 * never flash before the session is verified.
 */
const router = createBrowserRouter([
  // ── Protected routes (require auth) ─────────────────────────────────────
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <MainLayout />,
        children: [
          { path: '/',            element: <Dashboard /> },
          { path: '/dashboard',   element: <Dashboard /> },
          { path: '/upload',      element: <Upload /> },
          { path: '/verification',element: <Verification /> },
          { path: '/reports',     element: <Reports /> },
          { path: '/history',     element: <History /> },
        ],
      },
    ],
  },

  // ── Public routes (redirect to dashboard if authenticated) ───────────────
  {
    element: <PublicRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          { path: '/login', element: <Login /> },
        ],
      },
    ],
  },

  // ── 404 catch-all ────────────────────────────────────────────────────────
  { path: '*', element: <NotFound /> },
]);

const AppRouter = () => <RouterProvider router={router} />;

export default AppRouter;
