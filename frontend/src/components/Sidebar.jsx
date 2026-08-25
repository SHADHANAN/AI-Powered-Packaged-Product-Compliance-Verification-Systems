import { NavLink, useLocation } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { Badge } from './ui';

const navItems = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    alternatePaths: ['/', '/dashboard'],
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
      </svg>
    ),
  },
  {
    label: 'Upload Product',
    path: '/upload',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
      </svg>
    ),
  },
  {
    label: 'Compliance Verification',
    path: '/verification',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z" />
      </svg>
    ),
  },
  {
    label: 'Audit Reports',
    path: '/reports',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
      </svg>
    ),
  },
  {
    label: 'Verification History',
    path: '/history',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
      </svg>
    ),
  },
];

const ROLE_VARIANTS = {
  ADMIN: 'danger',
  INSPECTOR: 'accent',
  VIEWER: 'neutral',
};

/**
 * Premium Deep Navy Glass Sidebar with glowing active navigation indicators.
 */
const Sidebar = ({ isOpen, onClose }) => {
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();

  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : user?.email?.[0]?.toUpperCase() || 'U';

  const displayName = user?.name || user?.email || 'Authorized Officer';
  const role = user?.role || 'INSPECTOR';

  const handleLogout = () => {
    onClose?.();
    logout();
  };

  const isNavActive = (item) => {
    if (item.alternatePaths) {
      return item.alternatePaths.includes(location.pathname);
    }
    return location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);
  };

  return (
    <>
      {/* Mobile backdrop overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-navy-950/60 backdrop-blur-sm lg:hidden animate-fade-in"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Panel */}
      <aside
        className={`
          fixed top-16 left-0 z-40 h-[calc(100vh-4rem)] w-64
          glass-sidebar text-slate-200
          transition-transform duration-300 ease-out
          lg:translate-x-0 lg:static lg:shadow-none
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <nav className="flex flex-col gap-1 p-4 h-full custom-scrollbar overflow-y-auto justify-between">
          <div className="space-y-1">
            <div className="mb-3 px-3">
              <p className="text-[10px] font-extrabold uppercase tracking-widest text-slate-400">
                Compliance Modules
              </p>
            </div>

            {navItems.map((item) => {
              const active = isNavActive(item);
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onClose}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 group
                    ${
                      active
                        ? 'bg-gradient-to-r from-primary-600/90 to-indigo-600/80 text-white shadow-glow-primary border border-indigo-400/30'
                        : 'text-slate-300 hover:bg-white/5 hover:text-white'
                    }`}
                >
                  <span
                    className={`transition-colors ${
                      active ? 'text-cyan-300' : 'text-slate-400 group-hover:text-cyan-300'
                    }`}
                  >
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                  {active && (
                    <span className="ml-auto w-2 h-2 rounded-full bg-cyan-400 shadow-glow-accent animate-pulse-soft" />
                  )}
                </NavLink>
              );
            })}
          </div>

          {/* Bottom: Inspector Card & Logout */}
          <div className="pt-4 border-t border-white/10 space-y-3">
            {isAuthenticated && user && (
              <div className="p-3 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center shrink-0 shadow-sm">
                    <span className="text-xs font-bold text-white">{initials}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-bold text-white truncate">{displayName}</p>
                    <p className="text-[10px] text-slate-400 truncate">{user.email || 'Inspector'}</p>
                    <div className="mt-1">
                      <Badge variant={ROLE_VARIANTS[role] || 'accent'} size="xs">
                        {role}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <button
              id="sidebar-logout-button"
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold
                text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-all border border-transparent hover:border-rose-500/20"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9"
                />
              </svg>
              Sign Out
            </button>
          </div>
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;
