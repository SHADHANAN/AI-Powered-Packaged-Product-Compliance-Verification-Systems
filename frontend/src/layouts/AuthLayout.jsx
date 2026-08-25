import { Outlet, Link } from 'react-router-dom';

/**
 * Premium Split-Screen Authentication Layout.
 * Left: AI Enforcement Platform Visual Branding with Floating Glass Badges.
 * Right: Glassmorphic Authentication Card.
 */
const AuthLayout = () => {
  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-slate-950 text-white font-sans selection:bg-primary-500 selection:text-white">
      {/* ── Left Hero Visual Branding Area ──────────────────────────────── */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-navy-950 via-slate-900 to-indigo-950 p-12 lg:p-16 flex-col justify-between border-r border-white/10">
        {/* Ambient Glow Orbs */}
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-primary-600/20 blur-3xl pointer-events-none" />
        <div className="absolute top-1/2 right-0 w-80 h-80 rounded-full bg-cyan-500/15 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-20 left-1/3 w-80 h-80 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />

        {/* Brand Header */}
        <div className="relative z-10">
          <Link to="/" className="inline-flex items-center gap-3 group">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-primary-500 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-glow-primary group-hover:scale-105 transition-transform">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z"
                />
              </svg>
            </div>
            <div>
              <span className="text-xl font-extrabold text-white tracking-tight block">
                Compliance<span className="text-cyan-400">AI</span>
              </span>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest block">
                National Enforcement System
              </span>
            </div>
          </Link>
        </div>

        {/* Hero Value Statement */}
        <div className="relative z-10 my-auto space-y-6 max-w-lg">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/15 backdrop-blur-md text-xs font-semibold text-cyan-300 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse-soft" />
            Statutory Legal Metrology & FSSAI Verification
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight leading-[1.15]">
            AI-Powered Packaged Product <span className="gradient-text-primary">Compliance System</span>
          </h1>

          <p className="text-sm sm:text-base text-slate-300 leading-relaxed font-normal">
            Automated Legal Metrology inspection and food safety labeling analysis powered by optical character recognition, statutory rule validation, and instant audit generation.
          </p>

          {/* Floating Glass Feature Badges */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md space-y-1">
              <div className="flex items-center gap-2 text-cyan-400">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
                <span className="text-xs font-bold text-white">Rule 6(1) Declarations</span>
              </div>
              <p className="text-[11px] text-slate-400">
                MRP, USP, Net Qty, Dates, Batch & Manufacturer auto-checks
              </p>
            </div>

            <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md space-y-1">
              <div className="flex items-center gap-2 text-emerald-400">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
                <span className="text-xs font-bold text-white">Official Audit Reports</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Instant statutory certificates & certified PDF / Excel exports
              </p>
            </div>
          </div>
        </div>

        {/* Footer Security Watermark */}
        <div className="relative z-10 flex items-center justify-between text-xs text-slate-400 border-t border-white/10 pt-4">
          <span>Official Inspection Portal</span>
          <span>&copy; {new Date().getFullYear()} Ministry / Dept Enforcement</span>
        </div>
      </div>

      {/* ── Right Authentication Area ────────────────────────────────────── */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 sm:p-12 lg:p-16 relative bg-slate-50 text-navy-900">
        {/* Mobile Header Brand */}
        <div className="lg:hidden mb-8 text-center">
          <Link to="/" className="inline-flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary-600 to-cyan-500 flex items-center justify-center shadow-glow-primary">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
              </svg>
            </div>
            <span className="text-xl font-extrabold text-navy-900">
              Compliance<span className="text-primary-600">AI</span>
            </span>
          </Link>
        </div>

        {/* Auth Card */}
        <div className="w-full max-w-md">
          <div className="glass-panel p-7 sm:p-9 shadow-glass-lg border border-white/90 animate-slide-up">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
