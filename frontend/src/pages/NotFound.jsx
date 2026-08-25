import { Link } from 'react-router-dom';
import { Button } from '../components/ui';

/**
 * 404 Not Found page.
 */
const NotFound = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-50 px-4">
      <div className="text-center animate-fade-in">
        <p className="text-8xl font-bold text-primary-200">404</p>
        <h1 className="mt-4 text-2xl font-bold text-surface-900">
          Page not found
        </h1>
        <p className="mt-2 text-surface-500 max-w-sm mx-auto">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-8">
          <Link to="/">
            <Button variant="primary">Back to Dashboard</Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
