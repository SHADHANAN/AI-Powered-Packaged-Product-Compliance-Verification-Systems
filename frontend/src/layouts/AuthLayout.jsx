import { Outlet, Link } from 'react-router-dom';

/**
 * High-Impact Split-Screen Command Center Auth Layout.
 * Left 60%: Dark Navy Authority Backdrop with "VERIFY. COMPLY. PROTECT." and floating HUD inspection chips.
 * Right 40%: Crisp, clean authentication card.
 */
const AuthLayout = () => {
  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-[#F4F7FB] text-command-900 font-sans selection:bg-primary-600 selection:text-white">
      {/* ── Left 60% Authority Branding Section ───────────────────────────── */}
      <div className="hidden lg:flex lg:w-[58%] relative overflow-hidden bg-command-900 p-12 lg:p-16 flex-col justify-between text-white border-r border-slate-800">
        {/* Abstract Technical Grid Pattern */}
        <div className="absolute inset-0 grid-pattern opacity-40 pointer-events-none" />

        {/* Ambient Glow accents */}
        <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-primary-600/20 blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 right-10 w-96 h-96 rounded-full bg-cyan-500/15 blur-3xl pointer-events-none" />

        {/* Brand Header */}
        <div className="relative z-10">
          <Link to="/" className="inline-flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary-600 to-cyan-500 flex items-center justify-center text-white font-black text-base shadow-glow-primary">
              C
            </div>
            <div>
              <span className="text-lg font-black tracking-wider text-white block">
                COMPLY<span className="text-cyan-400">.AI</span>
              </span>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest block">
                Legal Metrology Intelligence
              </span>
            </div>
          </Link>
        </div>

        {/* Main Value Proposition */}
        <div className="relative z-10 my-auto space-y-7 max-w-xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-white/10 border border-white/15 text-xs font-bold uppercase tracking-wider text-cyan-300">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse-soft" />
            Statutory Inspection Command Platform
          </div>

          <div className="space-y-2">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-[1.05]">
              VERIFY.<br />
              <span className="text-primary-400">COMPLY.</span><br />
              <span className="text-cyan-400">PROTECT.</span>
            </h1>
            <p className="text-base sm:text-lg text-slate-300 pt-3 leading-relaxed font-normal">
              AI-powered packaged commodity compliance verification for modern enforcement.
            </p>
          </div>

          {/* Decorative Floating Glass HUD Status Chips */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4">
            <div className="glass-hud p-3.5 space-y-1">
              <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-xs">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
                <span>MRP CHECK</span>
              </div>
              <p className="text-[11px] font-bold text-white uppercase tracking-wider">
                COMPLIANT
              </p>
            </div>

            <div className="glass-hud p-3.5 space-y-1">
              <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-xs">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
                <span>NET QUANTITY</span>
              </div>
              <p className="text-[11px] font-bold text-white uppercase tracking-wider">
                VERIFIED
              </p>
            </div>

            <div className="glass-hud p-3.5 space-y-1">
              <div className="flex items-center gap-1.5 text-amber-400 font-bold text-xs">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
                <span>DECLARATION</span>
              </div>
              <p className="text-[11px] font-bold text-white uppercase tracking-wider">
                REVIEW
              </p>
            </div>
          </div>
        </div>

        {/* Footer Authority Bar */}
        <div className="relative z-10 flex items-center justify-between text-xs text-slate-400 border-t border-white/10 pt-4 font-mono">
          <span>LEGAL METROLOGY ACT 2009</span>
          <span>PACKAGED COMMODITIES RULES</span>
        </div>
      </div>

      {/* ── Right 40% Clean Login Form Section ───────────────────────────── */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 sm:p-12 lg:p-16">
        {/* Mobile Header Logo */}
        <div className="lg:hidden mb-8 text-center">
          <Link to="/" className="inline-flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-command-900 flex items-center justify-center text-cyan-400 font-black shadow-sm">
              C
            </div>
            <span className="text-xl font-black text-command-900">
              COMPLY<span className="text-primary-600">.AI</span>
            </span>
          </Link>
        </div>

        {/* Login Container */}
        <div className="w-full max-w-md">
          <div className="bg-white border border-slate-200 rounded-2xl p-7 sm:p-9 shadow-card">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
