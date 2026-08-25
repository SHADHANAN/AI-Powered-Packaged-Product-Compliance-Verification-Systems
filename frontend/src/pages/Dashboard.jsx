import { useState } from 'react';
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { Card, Badge, Button, Loading } from '../components/ui';
import { ROUTES } from '../utils/constants';

/**
 * Command Center Dashboard for Legal Metrology Officers.
 */
const Dashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Statistics KPI chips
  const statCards = [
    {
      id: 'total-inspections',
      label: 'TOTAL INSPECTIONS',
      value: '—',
      badgeText: 'Awaiting data',
      badgeVariant: 'info',
      description: 'Packaged commodities registered',
      icon: (
        <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z" />
        </svg>
      ),
    },
    {
      id: 'compliant-products',
      label: 'COMPLIANT',
      value: '—',
      badgeText: 'Awaiting data',
      badgeVariant: 'success',
      description: '100% statutory declarations satisfied',
      icon: (
        <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
        </svg>
      ),
    },
    {
      id: 'violations-products',
      label: 'VIOLATIONS',
      value: '—',
      badgeText: 'Awaiting data',
      badgeVariant: 'danger',
      description: 'Labeling defects under Rule 6(1)',
      icon: (
        <svg className="w-5 h-5 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
        </svg>
      ),
    },
  ];

  // Statutory Rules Scope
  const complianceStandards = [
    { label: 'MRP & Pricing Declaration', rule: 'Legal Metrology Rules 2011, R.6(1)(e)', status: 'ACTIVE' },
    { label: 'Unit Sale Price (USP)', rule: 'Packaged Commodities Amendment R.6(11)', status: 'ACTIVE' },
    { label: 'Net Quantity Standard', rule: 'Legal Metrology Rules 2011, R.12 & Sch. 2', status: 'ACTIVE' },
    { label: 'Manufacturer & Country of Origin', rule: 'Consumer Protection / Metrology R.6(1)(a)', status: 'ACTIVE' },
    { label: 'FSSAI License & Dates', rule: 'Food Safety and Standards Regulations', status: 'ACTIVE' },
  ];

  if (loading) {
    return (
      <div className="py-20 flex justify-center">
        <Loading variant="spinner" size="lg" text="Loading Command Center..." />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── 1. Large Hero Section: COMPLIANCE COMMAND CENTER ───────────────── */}
      <div className="cmd-hero p-6 sm:p-8 lg:p-10 relative overflow-hidden">
        {/* Grid pattern overlay */}
        <div className="absolute inset-0 grid-pattern opacity-30 pointer-events-none" />
        
        {/* Glowing radial accents */}
        <div className="absolute -top-16 -right-16 w-80 h-80 rounded-full bg-primary-500/20 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-16 -left-16 w-80 h-80 rounded-full bg-cyan-500/15 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-8">
          <div className="space-y-4 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-white/10 border border-white/15 text-[11px] font-bold uppercase tracking-wider text-cyan-300">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse-soft" />
              Automated Inspection Pipeline Active
            </div>

            <div className="space-y-1">
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight text-white uppercase">
                Compliance Command Center
              </h1>
              <p className="text-sm sm:text-base text-slate-300 font-normal leading-relaxed">
                Monitor packaged product inspections and regulatory compliance in real time.
              </p>
            </div>

            <div className="pt-2 flex flex-wrap items-center gap-3">
              <Link to={ROUTES.UPLOAD}>
                <Button
                  variant="hero"
                  size="md"
                  leftIcon={
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                    </svg>
                  }
                >
                  + New Inspection
                </Button>
              </Link>

              <Link to={ROUTES.HISTORY}>
                <Button
                  variant="secondary"
                  size="md"
                  className="bg-white/10 text-white border-white/20 hover:bg-white/20 hover:text-white"
                >
                  Audit Repository
                </Button>
              </Link>
            </div>
          </div>

          {/* Right Hero Visual: Circular Score HUD */}
          <div className="glass-hud p-6 sm:p-7 flex flex-col items-center text-center self-center lg:self-auto min-w-[220px]">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-slate-400 mb-2">
              System Target Conformity
            </span>
            
            <div className="relative w-28 h-28 my-1 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle
                  className="text-white/10"
                  strokeWidth="8"
                  stroke="currentColor"
                  fill="transparent"
                  r="40"
                  cx="50"
                  cy="50"
                />
                <circle
                  className="text-cyan-400"
                  strokeWidth="8"
                  strokeDasharray="251.2"
                  strokeDashoffset="15"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="transparent"
                  r="40"
                  cx="50"
                  cy="50"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-black text-white tracking-tight">94%</span>
                <span className="text-[9px] font-bold uppercase tracking-wider text-cyan-300">Rate</span>
              </div>
            </div>

            <div className="mt-2 pt-2 border-t border-white/10 w-full">
              <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
                COMPLIANT STANDARD
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── 2. Bento Row 1: 3 Asymmetric KPI Metric Cards ─────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        {statCards.map((card) => (
          <Card
            key={card.id}
            variant="default"
            hoverable
            className="p-5 flex flex-col justify-between"
          >
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  {card.label}
                </p>
                <p className="text-3xl font-black text-command-900 tracking-tight">
                  {card.value}
                </p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                {card.icon}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
              <Badge variant={card.badgeVariant} size="xs" dot>
                {card.badgeText}
              </Badge>
              <span className="text-slate-400 font-medium truncate max-w-[140px]" title={card.description}>
                {card.description}
              </span>
            </div>
          </Card>
        ))}
      </div>

      {/* ── 3. Bento Row 2: Compliance Overview & Quick Actions ─────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Statutory Compliance Overview (2 Cols) */}
        <div className="lg:col-span-2">
          <Card
            variant="default"
            header={
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-primary-600" />
                  <h2 className="text-xs font-bold uppercase tracking-wider text-command-900">
                    Statutory Rule Scope
                  </h2>
                </div>
                <span className="text-[11px] text-slate-400 font-mono">LEGAL METROLOGY ACT</span>
              </div>
            }
          >
            <div className="space-y-2.5">
              {complianceStandards.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-slate-50/80 border border-slate-200/80 flex items-start justify-between gap-3"
                >
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-command-900">
                      {item.label}
                    </p>
                    <p className="text-[11px] text-slate-500 font-mono">
                      {item.rule}
                    </p>
                  </div>
                  <Badge variant="success" size="xs">
                    {item.status}
                  </Badge>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400 font-medium">
              <span>Legal Metrology (Packaged Commodities) Rules 2011</span>
              <span className="font-bold text-primary-600">v1.0 Standard</span>
            </div>
          </Card>
        </div>

        {/* Quick Actions (1 Col) */}
        <div>
          <Card
            variant="default"
            header={
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-cyan-500" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-command-900">
                  Quick Actions
                </h2>
              </div>
            }
          >
            <div className="space-y-3">
              <Link to={ROUTES.UPLOAD} className="block group">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 group-hover:border-primary-400 group-hover:bg-primary-50/30 transition-all flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-primary-600 text-white flex items-center justify-center font-bold text-xs">
                      +
                    </div>
                    <div>
                      <p className="text-xs font-bold text-command-900 group-hover:text-primary-700">Upload Product</p>
                      <p className="text-[10px] text-slate-500">Scan packaging image</p>
                    </div>
                  </div>
                  <svg className="w-4 h-4 text-slate-400 group-hover:text-primary-600 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                  </svg>
                </div>
              </Link>

              <Link to={ROUTES.VERIFICATION} className="block group">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 group-hover:border-primary-400 group-hover:bg-primary-50/30 transition-all flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold text-xs">
                      ✓
                    </div>
                    <div>
                      <p className="text-xs font-bold text-command-900 group-hover:text-primary-700">Verify Declarations</p>
                      <p className="text-[10px] text-slate-500">Inspect rule evaluations</p>
                    </div>
                  </div>
                  <svg className="w-4 h-4 text-slate-400 group-hover:text-primary-600 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                  </svg>
                </div>
              </Link>

              <Link to={ROUTES.REPORTS} className="block group">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 group-hover:border-primary-400 group-hover:bg-primary-50/30 transition-all flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-cyan-600 text-white flex items-center justify-center font-bold text-xs">
                      📄
                    </div>
                    <div>
                      <p className="text-xs font-bold text-command-900 group-hover:text-primary-700">Compliance Reports</p>
                      <p className="text-[10px] text-slate-500">Download certified PDFs</p>
                    </div>
                  </div>
                  <svg className="w-4 h-4 text-slate-400 group-hover:text-primary-600 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                  </svg>
                </div>
              </Link>
            </div>
          </Card>
        </div>
      </div>

      {/* ── 4. Bento Row 3: Recent Inspections Activity ─────────────────────── */}
      <Card
        variant="default"
        header={
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-slate-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-command-900">
                Recent Inspection Activity
              </h2>
            </div>
            <Badge variant="neutral" size="xs">
              0 RECORDS
            </Badge>
          </div>
        }
      >
        <div className="flex flex-col items-center justify-center py-10 px-4 text-center">
          <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center mb-3 text-slate-400">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
          </div>

          <h3 className="text-sm font-bold text-command-900 mb-1">
            No inspection logs to display
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mb-4">
            Upload a packaged commodity label to initiate automated Legal Metrology rule verification.
          </p>

          <Link to={ROUTES.UPLOAD}>
            <Button
              variant="primary"
              size="sm"
              leftIcon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
              }
            >
              Upload First Product
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;
