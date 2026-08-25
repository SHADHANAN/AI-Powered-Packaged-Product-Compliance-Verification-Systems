import ErrorBoundary from './components/ErrorBoundary';
import { AuthProvider } from './context/AuthContext';
import { AppRouter } from './routes';

/**
 * Root application component.
 * Wraps everything in ErrorBoundary and AuthProvider.
 */
const App = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;
