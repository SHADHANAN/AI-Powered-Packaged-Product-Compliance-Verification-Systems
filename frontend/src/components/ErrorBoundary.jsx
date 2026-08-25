import { Component } from 'react';
import { Button } from './ui';

/**
 * React Error Boundary — catches render errors and displays a fallback UI.
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-surface-50 p-6">
          <div className="max-w-md w-full text-center animate-fade-in">
            {/* Icon */}
            <div className="mx-auto w-20 h-20 rounded-full bg-danger-50 flex items-center justify-center mb-6">
              <svg
                className="w-10 h-10 text-danger-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
                />
              </svg>
            </div>

            <h1 className="text-2xl font-bold text-surface-900 mb-2">
              Something went wrong
            </h1>
            <p className="text-surface-500 mb-6">
              An unexpected error occurred. Please try again or contact support
              if the problem persists.
            </p>

            {/* Error details in dev mode */}
            {import.meta.env.DEV && this.state.error && (
              <pre className="mb-6 p-4 bg-surface-900 text-danger-300 text-xs rounded-xl text-left overflow-auto max-h-40 custom-scrollbar">
                {this.state.error.toString()}
              </pre>
            )}

            <div className="flex items-center justify-center gap-3">
              <Button variant="primary" onClick={this.handleReset}>
                Try Again
              </Button>
              <Button
                variant="secondary"
                onClick={() => (window.location.href = '/')}
              >
                Go Home
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
