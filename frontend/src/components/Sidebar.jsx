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
    label: 'Upload',
    path: '/upload',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
      </svg>
    ),
  },
  {
    label: 'Verification',
    path: '/verification',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z" />
      </svg>
    ),
  },
  {
    label: 'Reports',
    path: '/reports',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
      </svg>
    ),
  },
  {
    label: 'History',
    path: '/history',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
      </svg>
    ),
  },
];

const ROLE_VARIANTS = {
  ADMIN:     'danger',
  INSPECTOR: 'info',
  VIEWER:    'neutral',
};

/**
 * Sidebar navigation with active-state highlighting, user info panel, and logout.
 */
const Sidebar = ({ isOpen, onClose }) => {
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();

  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : user?.email?.[0]?.toUpperCase() || 'U';

  const displayName = user?.name || user?.email || 'User';
  const role = user?.role || '';

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
          className="fixed inset-0 z-40 bg-surface-950/30 backdrop-blur-sm lg:hidden animate-fade-in"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={`
          fixed top-16 left-0 z-40 h-[calc(100vh-4rem)] w-64
          bg-white border-r border-surface-100 shadow-sm
          transition-transform duration-300 ease-out
          lg:translate-x-0 lg:static lg:shadow-none
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <nav className="flex flex-col gap-1 p-4 h-full custom-scrollbar overflow-y-auto">
          <div className="mb-2 px-3">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-surface-400">
              Navigation
            </p>
          </div>

          {navItems.map((item) => {
            const active = isNavActive(item);
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group
                  ${active
                    ? 'bg-primary-50 text-primary-700 shadow-sm'
                    : 'text-surface-600 hover:bg-surface-50 hover:text-surface-900'
                  }`}
              >
                <span className={`transition-colors ${active ? 'text-primary-600' : 'text-surface-400 group-hover:text-surface-600'}`}>
                  {item.icon}
                </span>
                {item.label}
                {active && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-primary-500" />
                )}
              </NavLink>
            );
          })}

          {/* Bottom: user info + logout */}
          <div className="mt-auto pt-4 border-t border-surface-100 space-y-2">
            {isAuthenticated && user && (
              <div className="px-3 py-2.5 rounded-xl bg-surface-50 border border-surface-100">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center shrink-0">
                    <span className="text-xs font-bold text-white">{initials}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-surface-800 truncate">{displayName}</p>
                    {user.email && (
                      <p className="text-[11px] text-surface-500 truncate">{user.email}</p>
                    )}
                    {role && (
                      <Badge variant={ROLE_VARIANTS[role] || 'neutral'} size="sm" className="mt-1">
                        {role}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            )}

            <button
              id="sidebar-logout-button"
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium
                text-danger-600 hover:bg-danger-50 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" />
              </svg>
              Sign out
            </button>
          </div>
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;
