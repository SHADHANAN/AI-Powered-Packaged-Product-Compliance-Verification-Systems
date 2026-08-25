import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { Card, Button, Input, Badge, Loading } from '../components/ui';
import { getVerificationHistory } from '../api/history';
import { ROUTES } from '../utils/constants';
import { getErrorMessage } from '../utils/helpers';

/**
 * Status badging helper for history records
 */
const getComplianceBadge = (status) => {
  const norm = (status || 'PENDING').toUpperCase();
  switch (norm) {
    case 'COMPLIANT':
    case 'PASS':
    case 'PASSED':
      return <Badge variant="success" size="sm" dot>COMPLIANT</Badge>;
    case 'NON_COMPLIANT':
    case 'NON-COMPLIANT':
    case 'FAIL':
    case 'FAILED':
      return <Badge variant="danger" size="sm" dot>NON-COMPLIANT</Badge>;
    case 'WARNING':
      return <Badge variant="warning" size="sm" dot>WARNING</Badge>;
    case 'PENDING':
    case 'PROCESSING':
      return <Badge variant="neutral" size="sm" dot>PENDING</Badge>;
    default:
      return <Badge variant="neutral" size="sm">{norm}</Badge>;
  }
};

const ITEMS_PER_PAGE = 8;

/**
 * History Page — Central repository of scanned products and compliance verification records.
 * Provides search, multi-criteria filtering, sorting, pagination, and direct workflow navigation.
 */
const History = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Records state
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Search, Filter & Sort state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'COMPLIANT' | 'NON_COMPLIANT' | 'PENDING'
  const [sortBy, setSortBy] = useState('newest'); // 'newest' | 'oldest' | 'name_asc' | 'score_desc' | 'score_asc'
  const [currentPage, setCurrentPage] = useState(1);

  // ── Load History Records ──────────────────────────────────────────────────
  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getVerificationHistory();
      if (Array.isArray(data)) {
        setRecords(data);
      } else if (data && Array.isArray(data.items)) {
        setRecords(data.items);
      } else {
        setRecords([]);
      }
    } catch (err) {
      if (err?.response?.status === 404) {
        setRecords([]);
      } else if (err?.response?.status === 403) {
        setError('You do not have permission to view verification history records.');
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  // ── Filtering & Sorting Logic ─────────────────────────────────────────────
  const processedRecords = useMemo(() => {
    let result = [...records];

    // 1. Filter by Status
    if (statusFilter !== 'ALL') {
      result = result.filter((item) => {
        const s = (item.compliance_status || item.status || '').toUpperCase();
        if (statusFilter === 'COMPLIANT') return s === 'COMPLIANT' || s === 'PASS' || s === 'PASSED';
        if (statusFilter === 'NON_COMPLIANT') return s === 'NON_COMPLIANT' || s === 'FAIL' || s === 'FAILED';
        if (statusFilter === 'PENDING') return s === 'PENDING' || s === 'PROCESSING';
        return true;
      });
    }

    // 2. Filter by Search Query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      result = result.filter((item) => {
        return (
          String(item.id).toLowerCase().includes(q) ||
          (item.product_name && item.product_name.toLowerCase().includes(q)) ||
          (item.category && item.category.toLowerCase().includes(q)) ||
          (item.batch_number && item.batch_number.toLowerCase().includes(q)) ||
          (item.inspector && item.inspector.toLowerCase().includes(q))
        );
      });
    }

    // 3. Sorting
    result.sort((a, b) => {
      if (sortBy === 'newest') {
        return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      }
      if (sortBy === 'oldest') {
        return new Date(a.created_at || 0) - new Date(b.created_at || 0);
      }
      if (sortBy === 'name_asc') {
        return (a.product_name || '').localeCompare(b.product_name || '');
      }
      if (sortBy === 'score_desc') {
        return (b.score ?? -1) - (a.score ?? -1);
      }
      if (sortBy === 'score_asc') {
        return (a.score ?? 101) - (b.score ?? 101);
      }
      return 0;
    });

    return result;
  }, [records, statusFilter, searchQuery, sortBy]);

  // Pagination calculation
  const totalPages = Math.ceil(processedRecords.length / ITEMS_PER_PAGE) || 1;
  const paginatedRecords = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return processedRecords.slice(start, start + ITEMS_PER_PAGE);
  }, [processedRecords, currentPage]);

  // Adjust page if search reduces total
  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(1);
    }
  }, [currentPage, totalPages]);

  // Statistics calculation
  const totalCount = records.length;
  const compliantCount = records.filter((r) => {
    const s = (r.compliance_status || r.status || '').toUpperCase();
    return s === 'COMPLIANT' || s === 'PASS' || s === 'PASSED';
  }).length;
  const nonCompliantCount = records.filter((r) => {
    const s = (r.compliance_status || r.status || '').toUpperCase();
    return s === 'NON_COMPLIANT' || s === 'FAIL' || s === 'FAILED';
  }).length;

  const avgScore = useMemo(() => {
    const scored = records.filter((r) => typeof r.score === 'number');
    if (scored.length === 0) return null;
    const total = scored.reduce((acc, curr) => acc + curr.score, 0);
    return Math.round(total / scored.length);
  }, [records]);

  if (loading) {
    return (
      <div className="py-20">
        <Loading variant="spinner" size="lg" text="Loading verification history repository..." />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      {/* ── Page Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-surface-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-primary-600 uppercase tracking-wider mb-1">
            <Link to={ROUTES.DASHBOARD} className="hover:underline">
              Dashboard
            </Link>
            <span>/</span>
            <span>History</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-surface-900 tracking-tight">
            Verification History
          </h1>
          <p className="mt-1 text-sm sm:text-base text-surface-600">
            Search and review previously inspected packaged commodities and statutory audit records.
          </p>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadHistory}
            leftIcon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
            }
          >
            Refresh
          </Button>

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
              New Inspection
            </Button>
          </Link>
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

      {/* ── Summary Statistics Cards ─────────────────────────────────────── */}
      <section aria-labelledby="history-stats-heading" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <h2 id="history-stats-heading" className="sr-only">
          History Statistics
        </h2>

        {/* Total Scanned */}
        <Card variant="elevated" className="border-surface-200 p-5 space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-surface-500">
            Total Inspections
          </span>
          <p className="text-3xl font-extrabold text-surface-900">{totalCount}</p>
          <p className="text-xs text-surface-400">All registered package scans</p>
        </Card>

        {/* Compliant Scans */}
        <Card variant="elevated" className="border-surface-200 p-5 space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-surface-500">
            Compliant Packages
          </span>
          <p className="text-3xl font-extrabold text-accent-700">{compliantCount}</p>
          <p className="text-xs text-surface-400">
            {totalCount > 0 ? `${Math.round((compliantCount / totalCount) * 100)}% conformity rate` : 'Awaiting data'}
          </p>
        </Card>

        {/* Violation Records */}
        <Card variant="elevated" className="border-surface-200 p-5 space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-surface-500">
            Violations Flagged
          </span>
          <p className={`text-3xl font-extrabold ${nonCompliantCount > 0 ? 'text-danger-600' : 'text-surface-900'}`}>
            {nonCompliantCount}
          </p>
          <p className="text-xs text-surface-400">Packaged items with defects</p>
        </Card>

        {/* Average Score */}
        <Card variant="elevated" className="border-surface-200 p-5 space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-surface-500">
            Avg Compliance Score
          </span>
          <p className="text-3xl font-extrabold text-primary-600">
            {avgScore !== null ? `${avgScore}%` : '—'}
          </p>
          <p className="text-xs text-surface-400">Average statutory alignment</p>
        </Card>
      </section>

      {/* ── Search, Filter & Sorting Bar ─────────────────────────────────── */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Status Tabs */}
        <div className="inline-flex rounded-xl bg-surface-100 p-1 text-xs font-medium text-surface-600 self-start lg:self-auto">
          <button
            onClick={() => { setStatusFilter('ALL'); setCurrentPage(1); }}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'ALL' ? 'bg-white text-surface-900 shadow-sm font-semibold' : 'hover:text-surface-900'
            }`}
          >
            All ({totalCount})
          </button>
          <button
            onClick={() => { setStatusFilter('COMPLIANT'); setCurrentPage(1); }}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'COMPLIANT' ? 'bg-white text-accent-700 shadow-sm font-semibold' : 'hover:text-surface-900'
            }`}
          >
            Compliant ({compliantCount})
          </button>
          <button
            onClick={() => { setStatusFilter('NON_COMPLIANT'); setCurrentPage(1); }}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'NON_COMPLIANT' ? 'bg-white text-danger-700 shadow-sm font-semibold' : 'hover:text-surface-900'
            }`}
          >
            Non-Compliant ({nonCompliantCount})
          </button>
        </div>

        {/* Search & Sort Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
              placeholder="Search product, ID, batch..."
              aria-label="Search verification history"
              className="w-full pl-9 pr-8 py-1.5 text-xs rounded-xl bg-white border border-surface-200 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
            <svg className="w-4 h-4 text-surface-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600"
                aria-label="Clear search"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-1.5 text-xs text-surface-500">
            <span className="shrink-0 font-medium">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-2.5 py-1.5 rounded-xl bg-white border border-surface-200 text-surface-800 text-xs focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="name_asc">Product Name (A-Z)</option>
              <option value="score_desc">Score (High-Low)</option>
              <option value="score_asc">Score (Low-High)</option>
            </select>
          </div>
        </div>
      </div>

      {/* ── Inspection Records Grid ──────────────────────────────────────── */}
      {paginatedRecords.length > 0 ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {paginatedRecords.map((item) => {
              const complianceStatus = item.compliance_status || item.status;
              const hasScore = typeof item.score === 'number';

              return (
                <Card
                  key={item.id}
                  variant="default"
                  className="p-4 sm:p-5 border-surface-200 hover:border-surface-300 transition-all flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-3">
                    {/* Top Status & ID Bar */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-surface-900 bg-surface-100 px-2 py-0.5 rounded-md">
                          #{item.id}
                        </span>
                        {item.batch_number && (
                          <span className="text-[11px] text-surface-500 font-mono">
                            Batch: {item.batch_number}
                          </span>
                        )}
                      </div>
                      {getComplianceBadge(complianceStatus)}
                    </div>

                    {/* Product & Thumbnail Split */}
                    <div className="flex items-start gap-3.5">
                      {item.image_url ? (
                        <div className="w-16 h-16 rounded-xl bg-surface-50 border border-surface-200 shrink-0 overflow-hidden flex items-center justify-center">
                          <img
                            src={item.image_url}
                            alt={item.product_name || 'Inspected item'}
                            className="w-full h-full object-contain"
                          />
                        </div>
                      ) : (
                        <div className="w-16 h-16 rounded-xl bg-surface-100 border border-surface-200 shrink-0 flex items-center justify-center text-surface-400">
                          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                          </svg>
                        </div>
                      )}

                      <div className="space-y-1 min-w-0 flex-1">
                        <h3 className="text-sm font-bold text-surface-900 truncate">
                          {item.product_name || 'Packaged Commodity Item'}
                        </h3>
                        <p className="text-xs text-surface-500 truncate">
                          {item.category || 'General Packaged Goods'}
                        </p>
                        <div className="flex items-center gap-3 text-[11px] text-surface-400 pt-0.5">
                          <span>
                            {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Recent'}
                          </span>
                          <span>•</span>
                          <span>{item.inspector || user?.name || 'Inspector'}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Bottom Metrics & Actions */}
                  <div className="pt-3 border-t border-surface-100 flex items-center justify-between gap-2">
                    <div className="text-xs">
                      <span className="text-[10px] uppercase font-bold text-surface-400 block">
                        Score
                      </span>
                      <span className="font-extrabold text-surface-900">
                        {hasScore ? `${Math.round(item.score)}%` : '—'}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={() => navigate(`/extraction/${item.id}`)}
                      >
                        OCR Scan
                      </Button>

                      <Button
                        variant="primary"
                        size="xs"
                        onClick={() => navigate(`/verification/${item.id}`)}
                        rightIcon={
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                          </svg>
                        }
                      >
                        Verification
                      </Button>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-surface-200 text-xs text-surface-600">
              <span>
                Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1} to{' '}
                {Math.min(currentPage * ITEMS_PER_PAGE, processedRecords.length)} of{' '}
                {processedRecords.length} records
              </span>

              <div className="flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="xs"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <span className="px-2 font-semibold text-surface-900">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="xs"
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Empty State */
        <Card variant="default" className="py-16 text-center text-surface-500">
          <div className="w-14 h-14 rounded-2xl bg-surface-100 text-surface-400 mx-auto flex items-center justify-center mb-3">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>
          </div>
          <h2 className="text-base font-bold text-surface-800">
            No verification records found
          </h2>
          <p className="text-xs text-surface-400 mt-1 max-w-sm mx-auto">
            {records.length === 0
              ? 'Start by uploading a packaged product for automated Legal Metrology compliance inspection.'
              : 'No records matched your search query and filter criteria.'}
          </p>
          <div className="mt-5 flex items-center justify-center gap-3">
            <Link to={ROUTES.UPLOAD}>
              <Button variant="primary" size="sm">
                Upload Product
              </Button>
            </Link>
            {searchQuery && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => { setSearchQuery(''); setStatusFilter('ALL'); }}
              >
                Clear Search
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default History;
