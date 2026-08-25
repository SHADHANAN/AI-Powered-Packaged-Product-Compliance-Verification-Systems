import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { Badge } from './ui';
import { ROUTES } from '../utils/constants';

const ROLE_VARIANTS = {
  ADMIN: 'danger',
  INSPECTOR: 'accent',
  VIEWER: 'neutral',
};

/**
 * Command Center Top Navbar.
 */
const Navbar = ({ onToggleSidebar }) => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchVal, setSearchVal] = useState('');
  const menuRef = useRef(null);

  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : user?.email?.[0]?.toUpperCase() || 'O';

  const displayName = user?.name || user?.email?.split('@')[0] || 'Enforcement Officer';
  const role = user?.role || 'INSPECTOR';

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    if (menuOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [menuOpen]);

  const handleLogout = () => {
    setMenuOpen(false);
    logout();
  };

  const handleQuickSearch = (e) => {
    if (e.key === 'Enter' && searchVal.trim()) {
      navigate(ROUTES.HISTORY);
    }
  };

  return (
    <header className="sticky top-0 z-30 w-full cmd-navbar">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Left: Mobile Toggle & Brand Logo */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            className="lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
            aria-label="Toggle navigation sidebar"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>

          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-xl bg-command-900 flex items-center justify-center text-cyan-400 font-black shadow-sm border border-slate-700">
              <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z"
                />
              </svg>
            </div>
            <div className="hidden sm:block leading-tight">
              <span className="text-sm font-black text-command-900 tracking-wider block">
                COMPLY<span className="text-primary-600">.AI</span>
              </span>
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest block">
                Legal Metrology Intelligence
              </span>
            </div>
          </Link>
        </div>

        {/* Center: Global Quick Search */}
        <div className="hidden md:flex flex-1 max-w-md mx-8">
          <div className="relative w-full">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            <input
              type="search"
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
              onKeyDown={handleQuickSearch}
              placeholder="Search product, batch number, or verification ID..."
              aria-label="Global search"
              className="w-full pl-9 pr-4 py-1.5 text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-lg
                focus:outline-none focus:bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all font-medium"
            />
          </div>
        </div>

        {/* Right: Live Monitor Pill & User Profile Menu */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-[11px] font-bold text-emerald-700">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-soft" />
            SYSTEM ONLINE
          </div>

          {/* User Profile Dropdown */}
          {isAuthenticated && (
            <div className="relative" ref={menuRef}>
              <button
                id="user-menu-button"
                aria-haspopup="true"
                aria-expanded={menuOpen}
                onClick={() => setMenuOpen((v) => !v)}
                className="flex items-center gap-2 p-1 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <div className="w-8 h-8 rounded-lg bg-command-900 text-cyan-400 flex items-center justify-center font-bold text-xs border border-slate-700">
                  {initials}
                </div>
                <div className="hidden sm:block text-left">
                  <span className="text-xs font-bold text-command-900 block max-w-[120px] truncate leading-tight">
                    {displayName}
                  </span>
                  <span className="text-[10px] text-slate-500 block leading-none uppercase font-semibold">
                    {role}
                  </span>
                </div>
                <svg
                  className={`hidden sm:block w-3.5 h-3.5 text-slate-400 transition-transform duration-150 ${
                    menuOpen ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                </svg>
              </button>

              {/* Dropdown Card */}
              {menuOpen && (
                <div
                  role="menu"
                  aria-labelledby="user-menu-button"
                  className="absolute right-0 top-full mt-2 w-60 cmd-card p-2 animate-scale-in z-50 shadow-card-hover"
                >
                  <div className="px-3 py-2.5 border-b border-slate-100">
                    <p className="text-xs font-bold text-command-900 truncate">{displayName}</p>
                    <p className="text-[11px] text-slate-500 truncate">{user?.email}</p>
                    <div className="mt-2">
                      <Badge variant={ROLE_VARIANTS[role] || 'accent'} size="xs">
                        {role}
                      </Badge>
                    </div>
                  </div>

                  <div className="pt-1">
                    <button
                      id="logout-button"
                      role="menuitem"
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold
                        text-rose-600 hover:bg-rose-50 transition-colors"
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
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
