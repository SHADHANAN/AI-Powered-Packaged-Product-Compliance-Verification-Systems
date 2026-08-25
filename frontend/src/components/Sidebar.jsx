import { NavLink, useLocation, Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { Badge } from './ui';
import { ROUTES } from '../utils/constants';

const navGroups = [
  {
    heading: 'OVERVIEW',
    items: [
      {
        label: 'Dashboard',
        path: ROUTES.DASHBOARD,
        alternatePaths: ['/', ROUTES.DASHBOARD],
        icon: (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
          </svg>
        ),
      },
    ],
  },
  {
    heading: 'INSPECTION',
    items: [
      {
        label: 'New Inspection',
        path: ROUTES.UPLOAD,
        icon: (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
        ),
      },
      {
        label: 'Verification',
        path: ROUTES.VERIFICATION,
        icon: (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
        ),
      },
      {
        label: 'History',
        path: ROUTES.HISTORY,
        icon: (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
        ),
      },
    ],
  },
  {
    heading: 'COMPLIANCE',
    items: [
      {
        label: 'Reports',
        path: ROUTES.REPORTS,
        icon: (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
          </svg>
        ),
      },
    ],
  },
];

const ROLE_VARIANTS = {
  ADMIN: 'danger',
  INSPECTOR: 'accent',
  VIEWER: 'neutral',
};

/**
 * Premium Command Center Sidebar.
 */
const Sidebar = ({ isOpen, onClose }) => {
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();

  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : user?.email?.[0]?.toUpperCase() || 'O';

  const displayName = user?.name || user?.email?.split('@')[0] || 'Enforcement Officer';
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
          className="fixed inset-0 z-40 bg-command-950/70 backdrop-blur-sm lg:hidden animate-fade-in"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Panel */}
      <aside
        className={`
          fixed top-0 left-0 z-40 h-screen w-64
          cmd-sidebar text-slate-300 flex flex-col justify-between
          transition-transform duration-300 ease-out
          lg:translate-x-0 lg:static lg:h-[calc(100vh-4rem)]
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="p-4 space-y-6 overflow-y-auto custom-scrollbar">
          {/* Brand header on mobile sidebar */}
          <div className="lg:hidden pb-4 border-b border-white/10 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center text-white font-black text-sm">
                C
              </div>
              <div className="leading-tight">
                <span className="text-sm font-black text-white tracking-wider block">COMPLY.AI</span>
                <span className="text-[9px] text-cyan-400 font-bold uppercase tracking-widest block">Legal Metrology</span>
              </div>
            </Link>
            <button onClick={onClose} className="p-1 text-slate-400 hover:text-white" aria-label="Close sidebar">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Nav Groups */}
          <nav className="space-y-5">
            {navGroups.map((group) => (
              <div key={group.heading} className="space-y-1">
                <div className="px-3 pb-1">
                  <p className="text-[10px] font-extrabold uppercase tracking-widest text-slate-400">
                    {group.heading}
                  </p>
                </div>

                {group.items.map((item) => {
                  const active = isNavActive(item);
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={onClose}
                      className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-150 group
                        ${
                          active
                            ? 'bg-gradient-to-r from-primary-600/90 to-primary-700/80 text-white shadow-glow-primary border border-primary-500/40'
                            : 'text-slate-300 hover:bg-white/5 hover:text-white'
                        }`}
                    >
                      {active && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r bg-cyan-400 shadow-glow-cyan" />
                      )}
                      <span
                        className={`transition-colors ${
                          active ? 'text-cyan-300' : 'text-slate-400 group-hover:text-cyan-300'
                        }`}
                      >
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </div>
            ))}
          </nav>
        </div>

        {/* Bottom Officer Profile & Logout */}
        <div className="p-4 border-t border-white/10 space-y-3 bg-command-950/40">
          {isAuthenticated && user && (
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center shrink-0 shadow-sm text-white font-bold text-xs">
                  {initials}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold text-white truncate">{displayName}</p>
                  <div className="mt-0.5 flex items-center gap-1.5">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                      {role}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <button
            id="sidebar-logout-button"
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-semibold
              text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors border border-transparent hover:border-rose-500/20"
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
      </aside>
    </>
  );
};

export default Sidebar;
