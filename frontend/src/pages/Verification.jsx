import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { Card, Button, Badge, Loading } from '../components/ui';
import { getVerificationResult, verifyProductCompliance } from '../api/compliance';
import { ROUTES } from '../utils/constants';
import { getErrorMessage } from '../utils/helpers';

/**
 * Status badging helpers for overall compliance result and rule statuses.
 */
const getOverallStatusBadge = (status) => {
  const normStatus = (status || 'PENDING').toUpperCase();

  switch (normStatus) {
    case 'COMPLIANT':
    case 'PASS':
    case 'PASSED':
      return (
        <Badge variant="success" size="lg" dot pulse>
          COMPLIANT
        </Badge>
      );
    case 'NON_COMPLIANT':
    case 'NON-COMPLIANT':
    case 'FAIL':
    case 'FAILED':
      return (
        <Badge variant="danger" size="lg" dot>
          NON-COMPLIANT
        </Badge>
      );
    case 'WARNING':
    case 'PARTIAL':
      return (
        <Badge variant="warning" size="lg" dot>
          WARNING
        </Badge>
      );
    case 'PENDING':
    case 'PROCESSING':
    default:
      return (
        <Badge variant="neutral" size="lg" dot>
          PENDING EVALUATION
        </Badge>
      );
  }
};

const getRuleStatusBadge = (status) => {
  const norm = (status || 'PENDING').toUpperCase();
  switch (norm) {
    case 'PASS':
    case 'PASSED':
    case 'COMPLIANT':
      return <Badge variant="success" size="sm" dot>PASS</Badge>;
    case 'FAIL':
    case 'FAILED':
    case 'NON_COMPLIANT':
      return <Badge variant="danger" size="sm" dot>FAIL</Badge>;
    case 'WARNING':
      return <Badge variant="warning" size="sm" dot>WARNING</Badge>;
    default:
      return <Badge variant="neutral" size="sm">N/A</Badge>;
  }
};

const getSeverityBadge = (severity) => {
  const norm = (severity || 'INFO').toUpperCase();
  switch (norm) {
    case 'HIGH':
    case 'CRITICAL':
      return <Badge variant="danger" size="sm">HIGH SEVERITY</Badge>;
    case 'MEDIUM':
      return <Badge variant="warning" size="sm">MEDIUM</Badge>;
    case 'LOW':
      return <Badge variant="info" size="sm">LOW</Badge>;
    default:
      return <Badge variant="neutral" size="sm">INFO</Badge>;
  }
};

/**
 * Verification Page — Displays rule-by-rule Legal Metrology compliance results,
 * violation summaries, severity breakdowns, and evidence linking.
 */
const Verification = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [reEvaluating, setReEvaluating] = useState(false);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('ALL'); // 'ALL' | 'PASS' | 'FAIL' | 'WARNING'
  const [searchQuery, setSearchQuery] = useState('');

  // Core verification result state
  const [result, setResult] = useState({
    id: id || 'current',
    product_id: id || '',
    product_name: '',
    category: '',
    image_url: null,
    status: 'COMPLIANT',
    score: null,
    total_rules_checked: 0,
    passed_rules: 0,
    failed_rules: 0,
    warning_rules: 0,
    rules: [],
    violations: [],
  });

  // ── Load Verification Data ────────────────────────────────────────────────
  const loadVerification = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (id) {
        const data = await getVerificationResult(id);
        if (data) {
          setResult(data);
        }
      } else {
        // Direct route access fallback state
        setResult((prev) => ({
          ...prev,
          status: 'PENDING',
          rules: [],
          violations: [],
        }));
      }
    } catch (err) {
      if (err?.response?.status === 404) {
        // Fallback clean state if ID record has not been verified yet
        setResult((prev) => ({
          ...prev,
          id: id || 'NEW',
          status: 'PENDING',
          rules: [],
          violations: [],
        }));
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadVerification();
  }, [loadVerification]);

  // ── Re-evaluate / Trigger Verification ───────────────────────────────────
  const handleReEvaluate = async () => {
    if (!id || reEvaluating) return;
    setReEvaluating(true);
    setError(null);
    try {
      const data = await verifyProductCompliance(id);
      if (data) {
        setResult(data);
      } else {
        await loadVerification();
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setReEvaluating(false);
    }
  };

  // Extract rules array from backend response
  const rulesList = useMemo(() => {
    if (Array.isArray(result?.rules)) return result.rules;
    return [];
  }, [result]);

  // Extract violations array (or filter failed rules)
  const violationsList = useMemo(() => {
    if (Array.isArray(result?.violations) && result.violations.length > 0) {
      return result.violations;
    }
    return rulesList.filter(
      (r) => (r.status || '').toUpperCase() === 'FAIL' || (r.status || '').toUpperCase() === 'FAILED'
    );
  }, [result, rulesList]);

  // Filtered rules by tab & search term
  const filteredRules = useMemo(() => {
    return rulesList.filter((rule) => {
      const ruleStatus = (rule.status || 'PASS').toUpperCase();
      const matchesTab =
        activeFilter === 'ALL' ||
        (activeFilter === 'PASS' && (ruleStatus === 'PASS' || ruleStatus === 'PASSED')) ||
        (activeFilter === 'FAIL' && (ruleStatus === 'FAIL' || ruleStatus === 'FAILED')) ||
        (activeFilter === 'WARNING' && ruleStatus === 'WARNING');

      const query = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !query ||
        (rule.rule_name && rule.rule_name.toLowerCase().includes(query)) ||
        (rule.rule_identifier && rule.rule_identifier.toLowerCase().includes(query)) ||
        (rule.violation_message && rule.violation_message.toLowerCase().includes(query)) ||
        (rule.detected_value && rule.detected_value.toLowerCase().includes(query));

      return matchesTab && matchesSearch;
    });
  }, [rulesList, activeFilter, searchQuery]);

  // Computed summary counts (prefer backend values if provided)
  const totalCount = result?.total_rules_checked || rulesList.length || 0;
  const passCount =
    result?.passed_rules ??
    rulesList.filter((r) => (r.status || '').toUpperCase() === 'PASS' || (r.status || '').toUpperCase() === 'PASSED').length;
  const failCount =
    result?.failed_rules ??
    violationsList.length;
  const warnCount =
    result?.warning_rules ??
    rulesList.filter((r) => (r.status || '').toUpperCase() === 'WARNING').length;

  if (loading) {
    return (
      <div className="py-20">
        <Loading variant="spinner" size="lg" text="Evaluating compliance verification rules..." />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      {/* ── Header & Breadcrumbs ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-surface-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-primary-600 uppercase tracking-wider mb-1">
            <Link to={ROUTES.DASHBOARD} className="hover:underline">
              Dashboard
            </Link>
            <span>/</span>
            <Link to={ROUTES.UPLOAD} className="hover:underline">
              Upload
            </Link>
            <span>/</span>
            {id ? (
              <Link to={`/extraction/${id}`} className="hover:underline">
                Extraction
              </Link>
            ) : (
              <span>Extraction</span>
            )}
            <span>/</span>
            <span>Verification</span>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold text-surface-900 tracking-tight">
              Compliance Verification
            </h1>
            {getOverallStatusBadge(result.status)}
          </div>
          <p className="mt-1 text-sm sm:text-base text-surface-600">
            Legal Metrology (Packaged Commodities) & FSSAI labeling compliance rule evaluation.
          </p>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleReEvaluate}
            loading={reEvaluating}
            leftIcon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
            }
          >
            Re-evaluate
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate(ROUTES.REPORTS)}
            rightIcon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
            }
          >
            Generate Report
          </Button>
        </div>
      </div>

      {/* ── Error Banner ─────────────────────────────────────────────────── */}
      {error && (
        <div
          role="alert"
          className="flex items-center justify-between p-4 rounded-xl bg-danger-50 border border-danger-200 text-danger-800 text-sm animate-slide-down"
        >
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-danger-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>{error}</span>
          </div>
          <Button variant="ghost" size="xs" onClick={() => setError(null)}>
            Dismiss
          </Button>
        </div>
      )}

      {/* ── Key Performance / Summary Metrics Cards ──────────────────────── */}
      <section aria-labelledby="kpi-heading" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <h2 id="kpi-heading" className="sr-only">
          Compliance Metrics
        </h2>

        {/* Score Card */}
        <Card variant="elevated" className="border-surface-200 p-5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-surface-500">
              Compliance Score
            </span>
            <div className="w-8 h-8 rounded-lg bg-primary-50 text-primary-600 flex items-center justify-center">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
            </div>
          </div>
          <p className="text-3xl font-extrabold text-surface-900">
            {typeof result.score === 'number' ? `${Math.round(result.score)}%` : '—'}
          </p>
          <p className="text-xs text-surface-400">
            {typeof result.score === 'number'
              ? result.score >= 80
                ? 'High legal conformity'
                : 'Attention required'
              : 'Evaluated on rule scope'}
          </p>
        </Card>

        {/* Passed Rules Card */}
        <Card variant="elevated" className="border-surface-200 p-5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-surface-500">
              Rules Passed
            </span>
            <div className="w-8 h-8 rounded-lg bg-accent-50 text-accent-600 flex items-center justify-center">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
          </div>
          <p className="text-3xl font-extrabold text-accent-700">
            {totalCount > 0 ? passCount : '—'}
          </p>
          <p className="text-xs text-surface-400">
            {totalCount > 0 ? `Out of ${totalCount} checked` : 'Awaiting data'}
          </p>
        </Card>

        {/* Violations / Failed Rules Card */}
        <Card variant="elevated" className="border-surface-200 p-5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-surface-500">
              Violations Detected
            </span>
            <div className="w-8 h-8 rounded-lg bg-danger-50 text-danger-600 flex items-center justify-center">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
              </svg>
            </div>
          </div>
          <p className={`text-3xl font-extrabold ${failCount > 0 ? 'text-danger-600' : 'text-surface-900'}`}>
            {totalCount > 0 ? failCount : '—'}
          </p>
          <p className="text-xs text-surface-400">
            {failCount > 0 ? 'Action required' : 'No defects detected'}
          </p>
        </Card>

        {/* Warnings Card */}
        <Card variant="elevated" className="border-surface-200 p-5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-surface-500">
              Warnings
            </span>
            <div className="w-8 h-8 rounded-lg bg-warning-50 text-warning-600 flex items-center justify-center">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
            </div>
          </div>
          <p className={`text-3xl font-extrabold ${warnCount > 0 ? 'text-warning-600' : 'text-surface-900'}`}>
            {totalCount > 0 ? warnCount : '—'}
          </p>
          <p className="text-xs text-surface-400">
            {warnCount > 0 ? 'Observations' : 'None detected'}
          </p>
        </Card>
      </section>

      {/* ── Violations Summary Section (if violations exist) ─────────────── */}
      {violationsList.length > 0 && (
        <section aria-labelledby="violations-heading" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 id="violations-heading" className="text-lg font-bold text-danger-800 flex items-center gap-2">
                <svg className="w-5 h-5 text-danger-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
                Violations Found ({violationsList.length})
              </h2>
              <p className="text-xs text-surface-500 mt-0.5">
                The following mandatory packaging declarations did not satisfy Legal Metrology standards
              </p>
            </div>
            <Badge variant="danger" size="sm">
              Non-Compliance Identified
            </Badge>
          </div>

          <div className="space-y-3">
            {violationsList.map((violation, idx) => (
              <Card
                key={violation.id || violation.rule_identifier || idx}
                variant="default"
                className="border-danger-200 bg-danger-50/30 p-4 sm:p-5 space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-danger-500" />
                    <h3 className="text-sm font-bold text-surface-900">
                      {violation.rule_name || 'Packaging Rule Violation'}
                    </h3>
                    {violation.rule_identifier && (
                      <span className="text-xs font-mono text-surface-500">
                        ({violation.rule_identifier})
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {getSeverityBadge(violation.severity || 'HIGH')}
                    <Badge variant="danger" size="sm">FAIL</Badge>
                  </div>
                </div>

                {/* Violation Description */}
                {violation.violation_message && (
                  <p className="text-xs font-medium text-danger-800 bg-danger-100/60 p-2.5 rounded-xl">
                    {violation.violation_message}
                  </p>
                )}

                {/* Evidence & Expected Requirements Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded-xl bg-white border border-danger-200/60">
                    <span className="text-surface-400 font-semibold uppercase block text-[10px]">
                      Detected on Package
                    </span>
                    <span className="font-semibold text-surface-800 block mt-0.5 break-words">
                      {violation.detected_value || 'Missing / Not Detected'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded-xl bg-white border border-danger-200/60">
                    <span className="text-surface-400 font-semibold uppercase block text-[10px]">
                      Required Mandate
                    </span>
                    <span className="font-semibold text-surface-800 block mt-0.5 break-words">
                      {violation.expected_requirement || 'Mandatory declaration per Legal Metrology rules'}
                    </span>
                  </div>
                </div>

                {/* Actionable Recommendation */}
                {violation.recommendation && (
                  <div className="text-xs text-surface-600 flex items-start gap-2 pt-1">
                    <span className="font-bold text-surface-700 shrink-0">Recommendation:</span>
                    <span>{violation.recommendation}</span>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* ── Rule-by-Rule Inspection Results ───────────────────────────────── */}
      <section aria-labelledby="rule-results-heading" className="space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 id="rule-results-heading" className="text-lg font-bold text-surface-900">
              Rule-by-Rule Inspection Log
            </h2>
            <p className="text-xs text-surface-500 mt-0.5">
              Comprehensive evaluation details across all statutory rules
            </p>
          </div>

          {/* Filter Tabs & Search */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="inline-flex rounded-xl bg-surface-100 p-1 text-xs font-medium text-surface-600">
              <button
                onClick={() => setActiveFilter('ALL')}
                className={`px-3 py-1 rounded-lg transition-colors ${
                  activeFilter === 'ALL' ? 'bg-white text-surface-900 shadow-sm font-semibold' : 'hover:text-surface-900'
                }`}
              >
                All ({rulesList.length})
              </button>
              <button
                onClick={() => setActiveFilter('PASS')}
                className={`px-3 py-1 rounded-lg transition-colors ${
                  activeFilter === 'PASS' ? 'bg-white text-accent-700 shadow-sm font-semibold' : 'hover:text-surface-900'
                }`}
              >
                Pass ({passCount})
              </button>
              <button
                onClick={() => setActiveFilter('FAIL')}
                className={`px-3 py-1 rounded-lg transition-colors ${
                  activeFilter === 'FAIL' ? 'bg-white text-danger-700 shadow-sm font-semibold' : 'hover:text-surface-900'
                }`}
              >
                Fail ({failCount})
              </button>
              {warnCount > 0 && (
                <button
                  onClick={() => setActiveFilter('WARNING')}
                  className={`px-3 py-1 rounded-lg transition-colors ${
                    activeFilter === 'WARNING' ? 'bg-white text-warning-700 shadow-sm font-semibold' : 'hover:text-surface-900'
                  }`}
                >
                  Warn ({warnCount})
                </button>
              )}
            </div>

            {/* Quick Search */}
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search rules..."
                aria-label="Search rules"
                className="pl-8 pr-3 py-1 text-xs rounded-xl bg-white border border-surface-200 focus:outline-none focus:ring-1 focus:ring-primary-500 w-36 sm:w-44"
              />
              <svg className="w-3.5 h-3.5 text-surface-400 absolute left-2.5 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Rule Items List */}
        {filteredRules.length > 0 ? (
          <div className="space-y-3">
            {filteredRules.map((rule, index) => {
              const ruleStatus = (rule.status || 'PASS').toUpperCase();
              const isPass = ruleStatus === 'PASS' || ruleStatus === 'PASSED';

              return (
                <Card
                  key={rule.id || rule.rule_identifier || index}
                  variant="default"
                  className={`p-4 border-surface-200 transition-all ${
                    !isPass ? 'border-danger-200/80 bg-danger-50/10' : 'bg-white'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-surface-100">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${isPass ? 'bg-accent-500' : 'bg-danger-500'}`} />
                        <h3 className="text-sm font-bold text-surface-900">
                          {rule.rule_name || 'Regulatory Rule Check'}
                        </h3>
                      </div>
                      {rule.rule_identifier && (
                        <p className="text-[11px] font-mono text-surface-400">
                          {rule.rule_identifier}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 self-start sm:self-auto">
                      {!isPass && rule.severity && getSeverityBadge(rule.severity)}
                      {getRuleStatusBadge(rule.status)}
                    </div>
                  </div>

                  {/* Rule Details Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                    <div>
                      <span className="text-[10px] font-semibold uppercase text-surface-400 block">
                        Detected Evidence
                      </span>
                      <span className="text-surface-800 font-medium block mt-0.5 break-words">
                        {rule.detected_value || (isPass ? 'Verified on label' : 'Missing / Inconclusive')}
                      </span>
                    </div>

                    <div>
                      <span className="text-[10px] font-semibold uppercase text-surface-400 block">
                        Mandate Requirement
                      </span>
                      <span className="text-surface-600 block mt-0.5 break-words">
                        {rule.expected_requirement || 'Statutory requirement met'}
                      </span>
                    </div>
                  </div>

                  {/* Violation Message / Notes */}
                  {rule.violation_message && (
                    <div className="mt-2 p-2 rounded-lg bg-danger-50 text-danger-700 text-xs font-medium">
                      {rule.violation_message}
                    </div>
                  )}

                  {/* Recommendation */}
                  {rule.recommendation && (
                    <div className="mt-2 text-xs text-surface-500">
                      <span className="font-semibold text-surface-700">Guidance: </span>
                      {rule.recommendation}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        ) : (
          /* Empty Rules State */
          <Card variant="default" className="py-12 text-center text-surface-500">
            <svg className="w-10 h-10 mx-auto mb-2 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>
            <p className="text-sm font-semibold text-surface-700">
              No compliance verification rules to display.
            </p>
            <p className="text-xs text-surface-400 mt-0.5">
              {rulesList.length === 0
                ? 'Upload and extract a product image to evaluate statutory rules.'
                : 'No rules match the selected filter criteria.'}
            </p>
            {rulesList.length === 0 && (
              <div className="mt-4">
                <Link to={ROUTES.UPLOAD}>
                  <Button variant="primary" size="sm">
                    Upload Package Image
                  </Button>
                </Link>
              </div>
            )}
          </Card>
        )}
      </section>

      {/* ── Workflow Action Bar ─────────────────────────────────────────── */}
      <div className="pt-4 border-t border-surface-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <Button
          variant="secondary"
          size="md"
          onClick={() => navigate(id ? `/extraction/${id}` : ROUTES.EXTRACTION)}
          leftIcon={
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
            </svg>
          }
        >
          Back to Extraction
        </Button>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          <Link to={ROUTES.UPLOAD}>
            <Button variant="secondary" size="md">
              New Inspection
            </Button>
          </Link>

          <Button
            variant="primary"
            size="md"
            onClick={() => navigate(ROUTES.REPORTS)}
            rightIcon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            }
          >
            Generate Report
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Verification;
