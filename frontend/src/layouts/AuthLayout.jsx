import { Outlet, Link } from 'react-router-dom';

/**
 * Minimal layout for authentication pages (Login, Register, etc.).
 * Centered card with branding.
 */
const AuthLayout = () => {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-surface-50 via-primary-50/30 to-surface-100 px-4">
      {/* Brand */}
      <Link to="/" className="flex items-center gap-2.5 mb-8 group">
        <div className="w-11 h-11 rounded-xl gradient-primary flex items-center justify-center shadow-glow group-hover:shadow-glow transition-shadow">
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
          </svg>
        </div>
        <span className="text-2xl font-bold text-surface-900">
          Compliance<span className="text-primary-600">AI</span>
        </span>
      </Link>

      {/* Auth content */}
      <div className="w-full max-w-md">
        <div className="glass-card p-8 animate-slide-up">
          <Outlet />
        </div>
      </div>

      <p className="mt-8 text-sm text-surface-400">
        &copy; {new Date().getFullYear()} ComplianceAI. All rights reserved.
      </p>
    </div>
  );
};

export default AuthLayout;
