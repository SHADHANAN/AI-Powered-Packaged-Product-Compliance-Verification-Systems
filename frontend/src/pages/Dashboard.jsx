import { useState } from 'react';
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { Card, Badge, Button, Loading } from '../components/ui';
import { ROUTES } from '../utils/constants';

/**
 * Compliance system roles badge variant mapping.
 */
const ROLE_BADGE_MAP = {
  ADMIN:     'danger',
  INSPECTOR: 'info',
  VIEWER:    'neutral',
};

/**
 * Dashboard Page — Primary landing page after login.
 *
 * Displays:
 * - Compliance summary metrics (Total Products, Compliant, Non-Compliant, Pending Review)
 * - Quick action navigation (Upload, Verification, Reports, History)
 * - Recent activity feed (with clean empty state)
 * - Regulatory standards & compliance verification pipeline status
 */
const Dashboard = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Statistics configuration
  // Note: Backend stats API will be connected in future phases. Neutral "—" / "Awaiting data" used.
  const statCards = [
    {
      id: 'total-products',
      label: 'Total Products',
      value: '—',
      badgeText: 'Awaiting data',
      badgeVariant: 'info',
      description: 'Packaged items in system',
      icon: (
        <svg className="w-6 h-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
          <path strokeLinecap="round" strokeLinejoin="round" d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z" />
        </svg>
      ),
      bgGradient: 'from-primary-50 to-primary-100/50',
    },
    {
      id: 'compliant-products',
      label: 'Compliant Products',
      value: '—',
      badgeText: 'Awaiting data',
      badgeVariant: 'success',
      description: 'Passed all regulatory checks',
      icon: (
        <svg className="w-6 h-6 text-accent-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
        </svg>
      ),
      bgGradient: 'from-accent-50 to-accent-100/50',
    },
    {
      id: 'non-compliant-products',
      label: 'Non-Compliant',
      value: '—',
      badgeText: 'Awaiting data',
      badgeVariant: 'danger',
      description: 'Violations or labeling defects',
      icon: (
        <svg className="w-6 h-6 text-danger-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
        </svg>
      ),
      bgGradient: 'from-danger-50 to-danger-100/50',
    },
    {
      id: 'pending-review',
      label: 'Pending Review',
      value: '—',
      badgeText: 'Awaiting data',
      badgeVariant: 'warning',
      description: 'Awaiting manual inspector review',
      icon: (
        <svg className="w-6 h-6 text-warning-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
        </svg>
      ),
      bgGradient: 'from-warning-50 to-warning-100/50',
    },
  ];

  // Quick Action Navigation Items
  const quickActions = [
    {
      title: 'Upload Product',
      description: 'Upload package images or packaging documents for OCR extraction and compliance verification.',
      to: ROUTES.UPLOAD,
      variant: 'primary',
      buttonText: 'Upload Package',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
        </svg>
      ),
    },
    {
      title: 'Verification Results',
      description: 'Inspect automated compliance check evaluations, detected label anomalies, and confidence scores.',
      to: ROUTES.VERIFICATION,
      variant: 'outline',
      buttonText: 'View Verifications',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z" />
        </svg>
      ),
    },
    {
      title: 'Compliance Reports',
      description: 'Generate, preview, and download formal compliance audit summaries in PDF or Excel format.',
      to: ROUTES.REPORTS,
      variant: 'outline',
      buttonText: 'View Reports',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
        </svg>
      ),
    },
    {
      title: 'Verification History',
      description: 'Browse complete historical audit logs, timestamps, and previous product inspection outcomes.',
      to: ROUTES.HISTORY,
      variant: 'outline',
      buttonText: 'Audit History',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
        </svg>
      ),
    },
  ];

  // Regulatory Standards Inspected
  const complianceStandards = [
    { label: 'MRP & Pricing Declaration', rule: 'Legal Metrology Rules', status: 'Active' },
    { label: 'Net Quantity & Unit Sale Price', rule: 'Packaged Commodities Rule 6', status: 'Active' },
    { label: 'Date of Manufacture / Expiry', rule: 'FSSAI / Regulatory Mandate', status: 'Active' },
    { label: 'Manufacturer & Country of Origin', rule: 'Consumer Protection Standard', status: 'Active' },
    { label: 'Nutritional Declaration & Allergen Info', rule: 'Food Safety & Standards', status: 'Active' },
  ];

  if (loading) {
    return (
      <div className="py-16">
        <Loading variant="spinner" size="lg" text="Loading compliance dashboard..." />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* ── Page Header / Welcome Banner ─────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-surface-200">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold text-surface-900 tracking-tight">
              Dashboard
            </h1>
            {user?.role && (
              <Badge variant={ROLE_BADGE_MAP[user.role] || 'neutral'} size="md">
                {user.role}
              </Badge>
            )}
          </div>
          <p className="mt-1 text-sm sm:text-base text-surface-600">
            Overview of packaged product compliance status, verification metrics, and system activity.
          </p>
        </div>

        {/* User Greeting / Quick Status */}
        <div className="flex items-center gap-3 self-start md:self-auto">
          <div className="text-right hidden sm:block">
            <p className="text-xs text-surface-400 font-medium">Logged in as</p>
            <p className="text-sm font-semibold text-surface-800">
              {user?.name || user?.email || 'Inspector'}
            </p>
          </div>
          <Link to={ROUTES.UPLOAD}>
            <Button
              variant="primary"
              size="md"
              leftIcon={
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
              }
            >
              New Verification
            </Button>
          </Link>
        </div>
      </div>

      {/* ── Error Banner (if any) ─────────────────────────────────────────── */}
      {error && (
        <div
          role="alert"
          className="flex items-center justify-between p-4 rounded-xl bg-danger-50 border border-danger-200 text-danger-800 text-sm"
        >
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-danger-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>{error}</span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setError(null)}>
            Dismiss
          </Button>
        </div>
      )}

      {/* ── Summary Statistics Cards Grid ─────────────────────────────────── */}
      <section aria-labelledby="stats-heading">
        <h2 id="stats-heading" className="sr-only">
          Compliance Statistics
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {statCards.map((card) => (
            <Card
              key={card.id}
              variant="elevated"
              hoverable
              className="relative overflow-hidden transition-all duration-300 border-surface-200"
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-xs font-semibold uppercase tracking-wider text-surface-500">
                    {card.label}
                  </p>
                  <p className="text-3xl font-extrabold text-surface-900 tracking-tight">
                    {card.value}
                  </p>
                </div>
                <div className={`p-2.5 rounded-xl bg-gradient-to-br ${card.bgGradient} shadow-sm`}>
                  {card.icon}
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-surface-100 flex items-center justify-between text-xs">
                <Badge variant={card.badgeVariant} size="sm" dot>
                  {card.badgeText}
                </Badge>
                <span className="text-surface-400 font-medium truncate max-w-[130px]" title={card.description}>
                  {card.description}
                </span>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Quick Actions ─────────────────────────────────────────────────── */}
      <section aria-labelledby="quick-actions-heading" className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 id="quick-actions-heading" className="text-lg font-bold text-surface-900">
            Quick Actions
          </h2>
          <span className="text-xs text-surface-500">Compliance Workflow Shortcuts</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => (
            <Card
              key={action.title}
              variant="default"
              hoverable
              className="flex flex-col justify-between p-5 border-surface-200"
            >
              <div className="space-y-2">
                <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center text-white shadow-sm mb-3">
                  {action.icon}
                </div>
                <h3 className="text-base font-semibold text-surface-900">
                  {action.title}
                </h3>
                <p className="text-xs text-surface-500 leading-relaxed">
                  {action.description}
                </p>
              </div>

              <div className="mt-5 pt-3 border-t border-surface-100">
                <Link to={action.to} className="block w-full">
                  <Button variant={action.variant} size="sm" fullWidth>
                    {action.buttonText}
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Two-Column Layout: Recent Activity + Regulatory Standards ─────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <Card
            variant="default"
            header={
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-surface-900">
                    Recent Activity
                  </h2>
                  <p className="text-xs text-surface-500 mt-0.5">
                    Latest packaging compliance verification audit logs
                  </p>
                </div>
                <Badge variant="neutral" size="sm">
                  0 Records
                </Badge>
              </div>
            }
          >
            {/* Empty State: Neutral, Clean, Informative */}
            <div className="flex flex-col items-center justify-center py-14 px-4 text-center">
              <div className="w-16 h-16 rounded-2xl bg-surface-100 flex items-center justify-center mb-4 text-surface-400">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                </svg>
              </div>

              <h3 className="text-base font-semibold text-surface-800 mb-1">
                No recent activity to display.
              </h3>
              <p className="text-xs sm:text-sm text-surface-500 max-w-sm mb-6">
                Start by uploading a product for verification.
              </p>

              <Link to={ROUTES.UPLOAD}>
                <Button
                  variant="primary"
                  size="sm"
                  leftIcon={
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
                    </svg>
                  }
                >
                  Upload First Product
                </Button>
              </Link>
            </div>
          </Card>
        </div>

        {/* Regulatory Standards & Pipeline Status (1 Col) */}
        <div className="space-y-4">
          <Card
            variant="default"
            header={
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-surface-900">
                    Compliance Rules
                  </h2>
                  <p className="text-xs text-surface-500 mt-0.5">
                    Automated rule verification scope
                  </p>
                </div>
                <Badge variant="success" size="sm" dot pulse>
                  Engine Ready
                </Badge>
              </div>
            }
          >
            <div className="space-y-3">
              {complianceStandards.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-surface-50 border border-surface-100 flex items-start justify-between gap-2"
                >
                  <div className="space-y-0.5">
                    <p className="text-xs font-semibold text-surface-800">
                      {item.label}
                    </p>
                    <p className="text-[11px] text-surface-500">
                      {item.rule}
                    </p>
                  </div>
                  <Badge variant="success" size="sm">
                    {item.status}
                  </Badge>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-3 border-t border-surface-100 flex items-center justify-between text-xs text-surface-400">
              <span>Legal Metrology & FSSAI</span>
              <span className="font-semibold text-primary-600">v1.0 Ruleset</span>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
