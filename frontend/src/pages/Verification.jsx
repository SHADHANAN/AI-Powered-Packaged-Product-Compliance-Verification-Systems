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
      return <Badge variant="success" size="xs">✓ PASS</Badge>;
    case 'FAIL':
    case 'FAILED':
    case 'NON_COMPLIANT':
      return <Badge variant="danger" size="xs">✕ FAIL</Badge>;
    case 'WARNING':
      return <Badge variant="warning" size="xs">⚠ WARNING</Badge>;
    default:
      return <Badge variant="neutral" size="xs">N/A</Badge>;
  }
};

const getSeverityBadge = (severity) => {
  const norm = (severity || 'INFO').toUpperCase();
  switch (norm) {
    case 'HIGH':
    case 'CRITICAL':
      return <Badge variant="danger" size="xs">HIGH SEVERITY</Badge>;
    case 'MEDIUM':
      return <Badge variant="warning" size="xs">MEDIUM</Badge>;
    case 'LOW':
      return <Badge variant="info" size="xs">LOW</Badge>;
    default:
      return <Badge variant="neutral" size="xs">INFO</Badge>;
  }
};

/**
 * Command Center Verification Page.
 */
const Verification = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [reEvaluating, setReEvaluating] = useState(false);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const [result, setResult] = useState({
    id: id || null,
    product_id: id || null,
    product_name: '',
    batch_number: '',
    status: 'PENDING',
    score: null,
    rules: [],
    violations: [],
    extracted_fields: {},
    inspected_at: null,
  });

  const loadVerificationData = useCallback(async (targetId) => {
    setLoading(true);
    setError(null);
    try {
      if (targetId) {
        const data = await getVerificationResult(targetId);
        if (data) {
          setResult({
            id: data.id || data.verification_id || targetId,
            product_id: data.product_id || targetId,
            product_name: data.product_name || data.name || 'Packaged Commodity Item',
            batch_number: data.batch_number || data.batch || '—',
            status: data.status || data.overall_status || 'PENDING',
            score: typeof data.score === 'number' ? data.score : typeof data.compliance_score === 'number' ? data.compliance_score : null,
            rules: Array.isArray(data.rules) ? data.rules : Array.isArray(data.rule_results) ? data.rule_results : [],
            violations: Array.isArray(data.violations) ? data.violations : [],
            extracted_fields: data.extracted_fields || data.declarations || {},
            inspected_at: data.inspected_at || data.created_at || data.timestamp || null,
          });
        }
      } else {
        setResult((prev) => ({
          ...prev,
          product_name: 'Packaged Commodity Verification Workspace',
          status: 'PENDING',
          score: null,
          rules: [],
          violations: [],
        }));
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadVerificationData(id);
  }, [id, loadVerificationData]);

  const handleReEvaluate = async () => {
    if (!id || reEvaluating) return;
    setReEvaluating(true);
    setError(null);
    try {
      const updated = await verifyProductCompliance(id);
      if (updated) {
        setResult((prev) => ({
          ...prev,
          status: updated.status || updated.overall_status || prev.status,
          score: typeof updated.score === 'number' ? updated.score : typeof updated.compliance_score === 'number' ? updated.compliance_score : prev.score,
          rules: Array.isArray(updated.rules) ? updated.rules : Array.isArray(updated.rule_results) ? updated.rule_results : prev.rules,
          violations: Array.isArray(updated.violations) ? updated.violations : prev.violations,
        }));
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setReEvaluating(false);
    }
  };

  const rulesList = result.rules || [];
  const violationsList = result.violations || [];

  const passCount = rulesList.filter(
    (r) => (r.status || '').toUpperCase() === 'PASS' || (r.status || '').toUpperCase() === 'PASSED'
  ).length;

  const failCount = rulesList.filter(
    (r) => (r.status || '').toUpperCase() === 'FAIL' || (r.status || '').toUpperCase() === 'FAILED'
  ).length;

  const warnCount = rulesList.filter(
    (r) => (r.status || '').toUpperCase() === 'WARNING'
  ).length;

  const totalCount = rulesList.length;

  const filteredRules = useMemo(() => {
    return rulesList.filter((rule) => {
      const status = (rule.status || 'PASS').toUpperCase();
      let matchesFilter = true;

      if (activeFilter === 'PASS') {
        matchesFilter = status === 'PASS' || status === 'PASSED';
      } else if (activeFilter === 'FAIL') {
        matchesFilter = status === 'FAIL' || status === 'FAILED';
      } else if (activeFilter === 'WARNING') {
        matchesFilter = status === 'WARNING';
      }

      if (!matchesFilter) return false;

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const ruleName = (rule.rule_name || rule.name || '').toLowerCase();
        const ruleId = (rule.rule_identifier || rule.id || '').toLowerCase();
        const desc = (rule.description || '').toLowerCase();
        return ruleName.includes(q) || ruleId.includes(q) || desc.includes(q);
      }

      return true;
    });
  }, [rulesList, activeFilter, searchQuery]);

  if (loading) {
    return (
      <div className="py-20 flex justify-center">
        <Loading variant="spinner" size="lg" text="Evaluating compliance verification rules..." />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── Page Header Banner ────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-bold text-primary-600 uppercase tracking-widest mb-1 font-mono">
            <Link to={ROUTES.DASHBOARD} className="hover:underline">
              COMMAND CENTER
            </Link>
            <span>/</span>
            <span>VERIFICATION</span>
            {id && <span>/ #{id}</span>}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-black text-command-900 tracking-tight uppercase">
              Product Verified
            </h1>
            {getOverallStatusBadge(result.status)}
          </div>
          <p className="mt-0.5 text-xs sm:text-sm text-slate-500 font-normal">
            Legal Metrology (Packaged Commodities) & FSSAI statutory rule evaluation.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {id && (
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
          )}

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
          className="flex items-center justify-between p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold animate-slide-down"
        >
          <div className="flex items-center gap-2.5">
            <svg className="w-4 h-4 text-rose-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
            <span>{error}</span>
          </div>
          <Button variant="ghost" size="xs" onClick={() => setError(null)}>
            Dismiss
          </Button>
        </div>
      )}

      {/* ── Top Bento KPI Overview ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card variant="default" className="p-5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Compliance Score
            </span>
            <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-xs">
              %
            </div>
          </div>
          <p className="text-3xl font-black text-command-900">
            {typeof result.score === 'number' ? `${Math.round(result.score)}%` : '—'}
          </p>
          <p className="text-xs text-slate-400">
            {typeof result.score === 'number'
              ? result.score >= 80 ? 'Standards satisfied' : 'Attention required'
              : 'Awaiting rule check'}
          </p>
        </Card>

        <Card variant="default" className="p-5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Rules Passed
            </span>
            <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-xs">
              ✓
            </div>
          </div>
          <p className="text-3xl font-black text-emerald-700">
            {totalCount > 0 ? passCount : '—'}
          </p>
          <p className="text-xs text-slate-400">
            {totalCount > 0 ? `Out of ${totalCount} inspected` : 'Awaiting data'}
          </p>
        </Card>

        <Card variant="default" className="p-5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Violations
            </span>
            <div className="w-7 h-7 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center font-bold text-xs">
              ✕
            </div>
          </div>
          <p className={`text-3xl font-black ${failCount > 0 ? 'text-rose-600' : 'text-command-900'}`}>
            {totalCount > 0 ? failCount : '—'}
          </p>
          <p className="text-xs text-slate-400">
            {failCount > 0 ? 'Action required' : 'No defects detected'}
          </p>
        </Card>

        <Card variant="default" className="p-5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
              Warnings
            </span>
            <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-xs">
              ⚠
            </div>
          </div>
          <p className={`text-3xl font-black ${warnCount > 0 ? 'text-amber-600' : 'text-command-900'}`}>
            {totalCount > 0 ? warnCount : '—'}
          </p>
          <p className="text-xs text-slate-400">
            {warnCount > 0 ? 'Observations' : 'None detected'}
          </p>
        </Card>
      </div>

      {/* ── Violations Panel (if any) ─────────────────────────────────────── */}
      {violationsList.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-rose-900">
                Violations Found ({violationsList.length})
              </h2>
            </div>
            <Badge variant="danger" size="xs">
              NON-COMPLIANCE DETECTED
            </Badge>
          </div>

          <div className="space-y-3">
            {violationsList.map((violation, idx) => (
              <Card
                key={violation.id || idx}
                variant="default"
                className="border-rose-200 bg-rose-50/20 p-4 sm:p-5 space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-command-900">
                      {violation.rule_name || 'Packaging Rule Violation'}
                    </h3>
                    {violation.rule_identifier && (
                      <span className="text-xs font-mono text-slate-500 font-medium">
                        ({violation.rule_identifier})
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {getSeverityBadge(violation.severity || 'HIGH')}
                    <Badge variant="danger" size="xs">✕ FAIL</Badge>
                  </div>
                </div>

                {violation.violation_message && (
                  <p className="text-xs font-semibold text-rose-800 bg-rose-100/50 p-2.5 rounded-lg">
                    {violation.violation_message}
                  </p>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-white border border-rose-200/80">
                    <span className="text-slate-400 font-bold uppercase text-[10px] block">
                      Detected on Package
                    </span>
                    <span className="font-bold text-command-900 block mt-0.5">
                      {violation.detected_value || 'Missing / Not Detected'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded-lg bg-white border border-rose-200/80">
                    <span className="text-slate-400 font-bold uppercase text-[10px] block">
                      Statutory Mandate
                    </span>
                    <span className="font-bold text-command-900 block mt-0.5">
                      {violation.expected_requirement || 'Mandatory declaration per Legal Metrology rules'}
                    </span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* ── Rule-by-Rule Inspection Log ───────────────────────────────────── */}
      <Card
        variant="default"
        header={
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 w-full">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-primary-600" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-command-900">
                Rule-by-Rule Inspection Log
              </h2>
            </div>

            {/* Filter Tabs & Search */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="inline-flex rounded-lg bg-slate-100 p-0.5 text-xs font-bold text-slate-600">
                <button
                  onClick={() => setActiveFilter('ALL')}
                  className={`px-2.5 py-1 rounded-md transition-colors ${
                    activeFilter === 'ALL' ? 'bg-white text-command-900 shadow-sm' : 'hover:text-command-900'
                  }`}
                >
                  All ({rulesList.length})
                </button>
                <button
                  onClick={() => setActiveFilter('PASS')}
                  className={`px-2.5 py-1 rounded-md transition-colors ${
                    activeFilter === 'PASS' ? 'bg-white text-emerald-700 shadow-sm' : 'hover:text-command-900'
                  }`}
                >
                  Pass ({passCount})
                </button>
                <button
                  onClick={() => setActiveFilter('FAIL')}
                  className={`px-2.5 py-1 rounded-md transition-colors ${
                    activeFilter === 'FAIL' ? 'bg-white text-rose-700 shadow-sm' : 'hover:text-command-900'
                  }`}
                >
                  Fail ({failCount})
                </button>
              </div>

              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter rules..."
                className="px-2.5 py-1 text-xs rounded-lg bg-slate-50 border border-slate-200 focus:outline-none focus:ring-1 focus:ring-primary-500 w-32 sm:w-40 font-medium"
              />
            </div>
          </div>
        }
      >
        {filteredRules.length > 0 ? (
          <div className="space-y-3">
            {filteredRules.map((rule, idx) => {
              const ruleStatus = (rule.status || 'PASS').toUpperCase();
              const isPass = ruleStatus === 'PASS' || ruleStatus === 'PASSED';

              return (
                <div
                  key={rule.id || idx}
                  className={`p-4 rounded-xl border transition-all ${
                    !isPass ? 'border-rose-200 bg-rose-50/20' : 'border-slate-200 bg-white'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
                    <div>
                      <h3 className="text-xs font-bold text-command-900 uppercase">
                        {rule.rule_name || 'Regulatory Rule Check'}
                      </h3>
                      {rule.rule_identifier && (
                        <p className="text-[10px] font-mono text-slate-400">
                          {rule.rule_identifier}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {getRuleStatusBadge(rule.status)}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                    <div>
                      <span className="text-slate-400 font-bold uppercase text-[10px] block">Detected Field</span>
                      <span className="font-bold text-command-900 block mt-0.5 font-mono">
                        {rule.detected_value || rule.extracted_value || 'Present / Valid'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-bold uppercase text-[10px] block">Statutory Mandate</span>
                      <span className="text-slate-600 block mt-0.5">
                        {rule.statutory_reference || rule.mandate || 'Packaged Commodities Rule 6(1)'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 text-xs text-slate-400 font-medium">
            No compliance rules match the selected criteria.
          </div>
        )}
      </Card>
    </div>
  );
};

export default Verification;
