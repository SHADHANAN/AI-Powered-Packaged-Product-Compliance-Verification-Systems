import { useState } from 'react';
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { Card, Badge, Button, Loading } from '../components/ui';
import { ROUTES } from '../utils/constants';

const ROLE_BADGE_MAP = {
  ADMIN: 'danger',
  INSPECTOR: 'accent',
  VIEWER: 'neutral',
};

/**
 * Modern Bento-Grid Dashboard for AI-Powered Packaged Product Compliance Verification.
 */
const Dashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Statistics Tiles
  const statCards = [
    {
      id: 'total-products',
      label: 'Total Inspected',
      value: '—',
      badgeText: 'Awaiting data',
      badgeVariant: 'info',
      description: 'Packaged items registered in audit pool',
      icon: (
        <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z" />
        </svg>
      ),
      glow: 'shadow-glow-primary',
    },
    {
      id: 'compliant-products',
      label: 'Certified Compliant',
      value: '—',
      badgeText: 'Awaiting data',
      badgeVariant: 'success',
      description: '100% statutory declarations satisfied',
      icon: (
        <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
        </svg>
      ),
      glow: 'shadow-glow-success',
    },
    {
      id: 'non-compliant-products',
      label: 'Flagged Violations',
      value: '—',
      badgeText: 'Awaiting data',
      badgeVariant: 'danger',
      description: 'Deficiencies under Legal Metrology Rules',
      icon: (
        <svg className="w-5 h-5 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
        </svg>
      ),
      glow: 'shadow-glow-danger',
    },
    {
      id: 'pending-review',
      label: 'Pending Inspections',
      value: '—',
      badgeText: 'Awaiting data',
      badgeVariant: 'warning',
      description: 'Awaiting OCR verification verification',
      icon: (
        <svg className="w-5 h-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
        </svg>
      ),
      glow: '',
    },
  ];

  // Quick Action Navigation Items
  const quickActions = [
    {
      title: 'Scan & Upload Product',
      description: 'Submit product packaging for automated PaddleOCR extraction and statutory verification.',
      to: ROUTES.UPLOAD,
      variant: 'primary',
      buttonText: 'Start Inspection',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
        </svg>
      ),
    },
    {
      title: 'Verification Workspace',
      description: 'Review rule-by-rule evaluation results, detected violations, and statutory references.',
      to: ROUTES.VERIFICATION,
      variant: 'secondary',
      buttonText: 'View Workspace',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
        </svg>
      ),
    },
    {
      title: 'Statutory Reports',
      description: 'Generate and export formal compliance certificates and audit reports in PDF format.',
      to: ROUTES.REPORTS,
      variant: 'secondary',
      buttonText: 'Audit Reports',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
        </svg>
      ),
    },
    {
      title: 'Historical Repository',
      description: 'Browse complete audit logs, timestamps, inspector signatures, and historical records.',
      to: ROUTES.HISTORY,
      variant: 'secondary',
      buttonText: 'Inspection Logs',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
        </svg>
      ),
    },
  ];

  // Regulatory Standards Scope
  const complianceStandards = [
    { label: 'MRP & Pricing Declaration', rule: 'Legal Metrology Rules 2011, R.6(1)(e)', status: 'Active' },
    { label: 'Unit Sale Price (USP)', rule: 'Packaged Commodities Amendment R.6(11)', status: 'Active' },
    { label: 'Net Quantity Standard', rule: 'Legal Metrology Rules 2011, R.12 & Sch. 2', status: 'Active' },
    { label: 'Manufacturer & Country of Origin', rule: 'Consumer Protection / Metrology R.6(1)(a)', status: 'Active' },
    { label: 'FSSAI License & Dates', rule: 'Food Safety and Standards Regulations', status: 'Active' },
  ];

  if (loading) {
    return (
      <div className="py-20 flex justify-center">
        <Loading variant="spinner" size="lg" text="Loading compliance dashboard..." />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ── Top Bento Row: Hero Overview Banner (2 Cols) + Circular Score Widget (1 Col) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bento Tile 1: Hero Compliance Overview (Large 2 Cols) */}
        <div className="lg:col-span-2 rounded-3xl gradient-hero-navy text-white p-7 sm:p-9 relative overflow-hidden shadow-glass-lg border border-white/15 flex flex-col justify-between">
          {/* Ambient Glow background */}
          <div className="absolute -top-16 -right-16 w-80 h-80 rounded-full bg-primary-500/20 blur-3xl pointer-events-none" />
          <div className="absolute -bottom-16 -left-16 w-80 h-80 rounded-full bg-cyan-500/15 blur-3xl pointer-events-none" />

          <div className="relative z-10 space-y-4 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/15 backdrop-blur-md text-xs font-semibold text-cyan-300">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse-soft" />
              Automated Statutory Verification Engine Active
            </div>

            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white leading-tight">
              AI Packaged Product <span className="gradient-text-primary">Compliance System</span>
            </h1>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
              Execute comprehensive Legal Metrology and FSSAI packaging verification across 11 statutory declarations with automated optical character extraction and violation detection.
            </p>
          </div>

          <div className="relative z-10 pt-6 mt-6 border-t border-white/10 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/10 border border-white/15 flex items-center justify-center text-cyan-300">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
                </svg>
              </div>
              <div>
                <p className="text-xs font-bold text-white">Rule 6(1) Standards</p>
                <p className="text-[11px] text-slate-400">11 mandatory packaging checks</p>
              </div>
            </div>

            <Link to={ROUTES.UPLOAD}>
              <Button
                variant="accent"
                size="md"
                leftIcon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                  </svg>
                }
              >
                Scan New Package
              </Button>
            </Link>
          </div>
        </div>

        {/* Bento Tile 2: Overall Compliance Score Circular Widget (1 Col) */}
        <Card variant="bento" className="flex flex-col justify-between p-6 sm:p-7 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-navy-900 uppercase tracking-wider">Overall Health</h2>
              <p className="text-xs text-slate-500">System conformity score</p>
            </div>
            <Badge variant="accent" size="sm" dot pulse>
              Live Monitor
            </Badge>
          </div>

          {/* Radial Circular Graphic */}
          <div className="my-6 flex flex-col items-center justify-center relative">
            <div className="relative w-36 h-36 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle
                  className="text-slate-100"
                  strokeWidth="9"
                  stroke="currentColor"
                  fill="transparent"
                  r="40"
                  cx="50"
                  cy="50"
                />
                <circle
                  className="text-primary-600 transition-all duration-1000 ease-out"
                  strokeWidth="9"
                  strokeDasharray="251.2"
                  strokeDashoffset="62.8"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="transparent"
                  r="40"
                  cx="50"
                  cy="50"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="text-3xl font-black text-navy-900 tracking-tight">100%</span>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Target</span>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500 font-medium">Status</span>
            <span className="font-bold text-emerald-700">Standards Compliant</span>
          </div>
        </Card>
      </div>

      {/* ── Row 2: KPI Metrics Bento Grid (4 Columns) ─────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((card) => (
          <Card
            key={card.id}
            variant="glass"
            hoverable
            className="p-5 flex flex-col justify-between"
          >
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  {card.label}
                </p>
                <p className="text-3xl font-black text-navy-900 tracking-tight">
                  {card.value}
                </p>
              </div>
              <div className={`p-2.5 rounded-2xl bg-slate-100/80 border border-slate-200/80 shadow-sm ${card.glow}`}>
                {card.icon}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100/90 flex items-center justify-between text-xs">
              <Badge variant={card.badgeVariant} size="sm" dot>
                {card.badgeText}
              </Badge>
              <span className="text-slate-400 font-medium truncate max-w-[130px]" title={card.description}>
                {card.description}
              </span>
            </div>
          </Card>
        ))}
      </div>

      {/* ── Row 3: Quick Actions ──────────────────────────────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-black text-navy-900 tracking-tight">
              Compliance Workflows
            </h2>
            <p className="text-xs text-slate-500">Quick action shortcuts for inspection officers</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => (
            <Card
              key={action.title}
              variant="glass"
              hoverable
              className="flex flex-col justify-between p-5"
            >
              <div className="space-y-2.5">
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-primary-600 to-indigo-600 flex items-center justify-center text-white shadow-sm mb-2">
                  {action.icon}
                </div>
                <h3 className="text-base font-bold text-navy-900 tracking-tight">
                  {action.title}
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed font-normal">
                  {action.description}
                </p>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-100">
                <Link to={action.to} className="block w-full">
                  <Button variant={action.variant} size="sm" fullWidth>
                    {action.buttonText}
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* ── Row 4: Recent Activity Feed + Statutory Rules Scope ───────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Inspection Stream (2 Cols) */}
        <div className="lg:col-span-2">
          <Card
            variant="bento"
            header={
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-navy-900">
                    Recent Inspection Activity
                  </h2>
                  <p className="text-xs text-slate-500">
                    Latest packaged commodity verification records
                  </p>
                </div>
                <Badge variant="neutral" size="sm">
                  0 Records
                </Badge>
              </div>
            }
          >
            {/* Empty State */}
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <div className="w-14 h-14 rounded-2xl bg-slate-100/90 border border-slate-200/80 flex items-center justify-center mb-3.5 text-slate-400">
                <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                </svg>
              </div>

              <h3 className="text-sm font-bold text-navy-900 mb-1">
                No recent inspections yet
              </h3>
              <p className="text-xs text-slate-500 max-w-sm mb-5">
                Upload a packaged commodity image to initiate automated Legal Metrology rule verification.
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

        {/* Statutory Rules Scope (1 Col) */}
        <div>
          <Card
            variant="bento"
            header={
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-navy-900">
                    Statutory Scope
                  </h2>
                  <p className="text-xs text-slate-500">
                    Active compliance standards
                  </p>
                </div>
                <Badge variant="success" size="sm" dot pulse>
                  Enforcing
                </Badge>
              </div>
            }
          >
            <div className="space-y-2.5">
              {complianceStandards.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-2xl bg-white/70 border border-slate-100 flex items-start justify-between gap-2 shadow-sm"
                >
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-navy-900">
                      {item.label}
                    </p>
                    <p className="text-[10px] text-slate-500">
                      {item.rule}
                    </p>
                  </div>
                  <Badge variant="success" size="xs">
                    {item.status}
                  </Badge>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
              <span>Legal Metrology & FSSAI</span>
              <span className="font-bold text-primary-600">v1.0 Ruleset</span>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
