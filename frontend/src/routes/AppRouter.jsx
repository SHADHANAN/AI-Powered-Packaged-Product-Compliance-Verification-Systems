import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { MainLayout, AuthLayout } from '../layouts';

// Pages
import Dashboard from '../pages/Dashboard';
import Upload from '../pages/Upload';
import Verification from '../pages/Verification';
import Reports from '../pages/Reports';
import History from '../pages/History';
import Login from '../pages/Login';
import NotFound from '../pages/NotFound';

/**
 * Application route definitions.
 *
 * - MainLayout wraps all dashboard/app pages (sidebar + navbar).
 * - AuthLayout wraps login/register pages (centered card).
 * - 404 catch-all at the root level.
 */
const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'upload', element: <Upload /> },
      { path: 'verification', element: <Verification /> },
      { path: 'reports', element: <Reports /> },
      { path: 'history', element: <History /> },
    ],
  },
  {
    path: '/',
    element: <AuthLayout />,
    children: [
      { path: 'login', element: <Login /> },
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
]);

/**
 * Router component to be mounted in App.
 */
const AppRouter = () => <RouterProvider router={router} />;

export default AppRouter;
