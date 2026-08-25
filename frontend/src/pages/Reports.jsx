import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { Card, Button, Input, Badge, Loading, Modal } from '../components/ui';
import { getReports, getReport, generateReport, downloadReport } from '../api/reports';
import { ROUTES } from '../utils/constants';
import { getErrorMessage } from '../utils/helpers';

/**
 * Visual badge mapper for compliance and report statuses
 */
const getStatusBadge = (status) => {
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
      return <Badge variant="warning" size="sm" dot>PROCESSING</Badge>;
    default:
      return <Badge variant="neutral" size="sm">{norm}</Badge>;
  }
};

/**
 * Reports Page — Comprehensive interface for listing, previewing, and downloading
 * official Legal Metrology & FSSAI audit compliance reports (PDF & Excel).
 */
const Reports = () => {
  const { id: urlReportId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  // State
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Active downloads tracker: Set of string keys like "1049-pdf"
  const [downloadingKeys, setDownloadingKeys] = useState(new Set());

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'COMPLIANT' | 'NON_COMPLIANT' | 'PENDING'

  // Report Details Drawer / Modal
  const [selectedReport, setSelectedReport] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  // Generate Report Modal
  const [isGenerateOpen, setIsGenerateOpen] = useState(false);
  const [generateForm, setGenerateForm] = useState({
    verification_id: '',
    format: 'PDF',
    include_evidence: true,
  });
  const [generating, setGenerating] = useState(false);

  // ── Load Reports List ─────────────────────────────────────────────────────
  const loadReportsList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getReports();
      if (Array.isArray(data)) {
        setReports(data);
      } else if (data && Array.isArray(data.items)) {
        setReports(data.items);
      } else {
        setReports([]);
      }
    } catch (err) {
      if (err?.response?.status === 404) {
        setReports([]);
      } else if (err?.response?.status === 403) {
        setError('You do not have permission to view compliance reports. Contact your administrator.');
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReportsList();
  }, [loadReportsList]);

  // ── Load Specific Report (if URL param present) ───────────────────────────
  const openReportDetails = useCallback(async (reportId) => {
    setDetailsLoading(true);
    setIsDetailsOpen(true);
    try {
      const data = await getReport(reportId);
      setSelectedReport(data || { id: reportId });
    } catch {
      // If backend details not yet populated, fallback to item from state
      const fallback = reports.find((r) => String(r.id) === String(reportId));
      setSelectedReport(fallback || { id: reportId, status: 'COMPLETED' });
    } finally {
      setDetailsLoading(false);
    }
  }, [reports]);

  useEffect(() => {
    if (urlReportId) {
      openReportDetails(urlReportId);
    }
  }, [urlReportId, openReportDetails]);

  // ── Handle Download ───────────────────────────────────────────────────────
  const handleDownload = async (reportId, format = 'pdf') => {
    const key = `${reportId}-${format}`;
    if (downloadingKeys.has(key)) return;

    setDownloadingKeys((prev) => new Set(prev).add(key));
    setError(null);

    try {
      await downloadReport(reportId, format);
      setSuccessMessage(`Report #${reportId} (${format.toUpperCase()}) downloaded successfully.`);
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err) {
      if (err?.response?.status === 404) {
        setError(`Report #${reportId} is still being compiled. Please try again in a moment.`);
      } else if (err?.response?.status === 403) {
        setError('Permission denied to download this report.');
      } else {
        setError('Unable to download report. Please check your network connection.');
      }
    } finally {
      setDownloadingKeys((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  };

  // ── Handle Generate Report ────────────────────────────────────────────────
  const handleGenerateSubmit = async (e) => {
    e.preventDefault();
    if (!generateForm.verification_id.trim() || generating) return;

    setGenerating(true);
    setError(null);
    try {
      const newReport = await generateReport({
        verification_id: generateForm.verification_id.trim(),
        format: generateForm.format,
        include_evidence: generateForm.include_evidence,
      });

      setIsGenerateOpen(false);
      setGenerateForm({ verification_id: '', format: 'PDF', include_evidence: true });
      setSuccessMessage('Report generation initiated successfully.');
      setTimeout(() => setSuccessMessage(null), 4000);

      // Refresh list
      await loadReportsList();

      if (newReport?.id) {
        openReportDetails(newReport.id);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  };

  // ── Filtered Reports List ─────────────────────────────────────────────────
  const filteredReports = useMemo(() => {
    return reports.filter((rep) => {
      const status = (rep.compliance_status || rep.status || 'COMPLETED').toUpperCase();
      const matchesStatus =
        statusFilter === 'ALL' ||
        (statusFilter === 'COMPLIANT' && (status === 'COMPLIANT' || status === 'PASS')) ||
        (statusFilter === 'NON_COMPLIANT' && (status === 'NON_COMPLIANT' || status === 'FAIL')) ||
        (statusFilter === 'PENDING' && (status === 'PENDING' || status === 'PROCESSING'));

      const query = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !query ||
        String(rep.id).toLowerCase().includes(query) ||
        (rep.product_name && rep.product_name.toLowerCase().includes(query)) ||
        (rep.category && rep.category.toLowerCase().includes(query)) ||
        (rep.generated_by && rep.generated_by.toLowerCase().includes(query));

      return matchesStatus && matchesSearch;
    });
  }, [reports, statusFilter, searchQuery]);

  // Statistics calculation
  const totalReports = reports.length;
  const compliantCount = reports.filter(
    (r) => (r.compliance_status || r.status || '').toUpperCase() === 'COMPLIANT' || (r.compliance_status || '').toUpperCase() === 'PASS'
  ).length;
  const nonCompliantCount = reports.filter(
    (r) => (r.compliance_status || r.status || '').toUpperCase() === 'NON_COMPLIANT' || (r.compliance_status || '').toUpperCase() === 'FAIL'
  ).length;

  if (loading) {
    return (
      <div className="py-20">
        <Loading variant="spinner" size="lg" text="Loading compliance audit reports..." />
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
            <span>Reports</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-surface-900 tracking-tight">
            Compliance Audit Reports
          </h1>
          <p className="mt-1 text-sm sm:text-base text-surface-600">
            Official Legal Metrology & food labeling statutory inspection records and certificates.
          </p>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadReportsList}
            leftIcon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
            }
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsGenerateOpen(true)}
            leftIcon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            }
          >
            Generate Report
          </Button>
        </div>
      </div>

      {/* ── Success / Error Alerts ───────────────────────────────────────── */}
      {successMessage && (
        <div className="p-4 rounded-xl bg-accent-50 border border-accent-200 text-accent-800 text-sm flex items-center gap-3 animate-slide-down">
          <svg className="w-5 h-5 text-accent-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
          <span>{successMessage}</span>
        </div>
      )}

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
      <section aria-labelledby="stats-heading" className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <h2 id="stats-heading" className="sr-only">
          Report Statistics
        </h2>

        {/* Total Reports */}
        <Card variant="elevated" className="border-surface-200 p-5 space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-surface-500">
            Total Reports
          </span>
          <p className="text-3xl font-extrabold text-surface-900">{totalReports}</p>
          <p className="text-xs text-surface-400">Archived compliance inspections</p>
        </Card>

        {/* Compliant Certifications */}
        <Card variant="elevated" className="border-surface-200 p-5 space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-surface-500">
            Certified Compliant
          </span>
          <p className="text-3xl font-extrabold text-accent-700">{compliantCount}</p>
          <p className="text-xs text-surface-400">Ready for regulatory issuance</p>
        </Card>

        {/* Non-Compliant Reports */}
        <Card variant="elevated" className="border-surface-200 p-5 space-y-1">
          <span className="text-xs font-bold uppercase tracking-wider text-surface-500">
            Violation Reports
          </span>
          <p className={`text-3xl font-extrabold ${nonCompliantCount > 0 ? 'text-danger-600' : 'text-surface-900'}`}>
            {nonCompliantCount}
          </p>
          <p className="text-xs text-surface-400">Requiring corrective packaging updates</p>
        </Card>
      </section>

      {/* ── Search & Filter Controls ─────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Status Filter Tabs */}
        <div className="inline-flex rounded-xl bg-surface-100 p-1 text-xs font-medium text-surface-600 self-start md:self-auto">
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'ALL' ? 'bg-white text-surface-900 shadow-sm font-semibold' : 'hover:text-surface-900'
            }`}
          >
            All ({totalReports})
          </button>
          <button
            onClick={() => setStatusFilter('COMPLIANT')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'COMPLIANT' ? 'bg-white text-accent-700 shadow-sm font-semibold' : 'hover:text-surface-900'
            }`}
          >
            Compliant ({compliantCount})
          </button>
          <button
            onClick={() => setStatusFilter('NON_COMPLIANT')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'NON_COMPLIANT' ? 'bg-white text-danger-700 shadow-sm font-semibold' : 'hover:text-surface-900'
            }`}
          >
            Non-Compliant ({nonCompliantCount})
          </button>
        </div>

        {/* Search Bar */}
        <div className="relative w-full md:w-64">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search reports or products..."
            aria-label="Search reports"
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl bg-white border border-surface-200 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
          <svg className="w-4 h-4 text-surface-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
        </div>
      </div>

      {/* ── Reports List Section ─────────────────────────────────────────── */}
      {filteredReports.length > 0 ? (
        <div className="space-y-4">
          {/* Desktop Table View */}
          <Card variant="default" className="p-0 overflow-hidden hidden md:block">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-surface-50 border-b border-surface-200 text-surface-500 uppercase tracking-wider font-semibold">
                  <th className="py-3.5 px-4">Report Reference</th>
                  <th className="py-3.5 px-4">Product Name</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4">Compliance Status</th>
                  <th className="py-3.5 px-4">Generated By</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-100">
                {filteredReports.map((report) => {
                  const pdfKey = `${report.id}-pdf`;
                  const excelKey = `${report.id}-excel`;
                  const isPdfDownloading = downloadingKeys.has(pdfKey);
                  const isExcelDownloading = downloadingKeys.has(excelKey);

                  return (
                    <tr key={report.id} className="hover:bg-surface-50/60 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-surface-900">
                        #{report.id}
                      </td>
                      <td className="py-3 px-4 font-semibold text-surface-800">
                        {report.product_name || 'Packaged Commodity'}
                      </td>
                      <td className="py-3 px-4 text-surface-500">
                        {report.category || 'General Foods'}
                      </td>
                      <td className="py-3 px-4">
                        {getStatusBadge(report.compliance_status || report.status)}
                      </td>
                      <td className="py-3 px-4 text-surface-600">
                        {report.generated_by || user?.name || user?.email || 'System'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            variant="ghost"
                            size="xs"
                            onClick={() => openReportDetails(report.id)}
                          >
                            View
                          </Button>

                          <Button
                            variant="outline"
                            size="xs"
                            loading={isPdfDownloading}
                            disabled={isPdfDownloading || isExcelDownloading}
                            onClick={() => handleDownload(report.id, 'pdf')}
                            leftIcon={
                              <svg className="w-3.5 h-3.5 text-danger-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                              </svg>
                            }
                          >
                            PDF
                          </Button>

                          <Button
                            variant="outline"
                            size="xs"
                            loading={isExcelDownloading}
                            disabled={isPdfDownloading || isExcelDownloading}
                            onClick={() => handleDownload(report.id, 'excel')}
                            leftIcon={
                              <svg className="w-3.5 h-3.5 text-accent-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M5 4a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3V7a3 3 0 00-3-3H5zm-1 9v-1h5v2H5a1 1 0 01-1-1zm7 1h4a1 1 0 001-1v-1h-5v2zm0-4h5V8h-5v2zM9 8H4v2h5V8z" clipRule="evenodd" />
                              </svg>
                            }
                          >
                            Excel
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>

          {/* Mobile Cards View */}
          <div className="grid grid-cols-1 gap-3 md:hidden">
            {filteredReports.map((report) => (
              <Card key={report.id} variant="default" className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-surface-900">
                    #{report.id}
                  </span>
                  {getStatusBadge(report.compliance_status || report.status)}
                </div>

                <div>
                  <h3 className="text-sm font-bold text-surface-900">
                    {report.product_name || 'Packaged Commodity'}
                  </h3>
                  <p className="text-xs text-surface-500 mt-0.5">
                    {report.category || 'General Foods'}
                  </p>
                </div>

                <div className="pt-2 border-t border-surface-100 flex items-center justify-between gap-2">
                  <Button variant="ghost" size="xs" onClick={() => openReportDetails(report.id)}>
                    View Details
                  </Button>

                  <div className="flex items-center gap-1.5">
                    <Button
                      variant="outline"
                      size="xs"
                      onClick={() => handleDownload(report.id, 'pdf')}
                    >
                      PDF
                    </Button>
                    <Button
                      variant="outline"
                      size="xs"
                      onClick={() => handleDownload(report.id, 'excel')}
                    >
                      Excel
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      ) : (
        /* Empty State */
        <Card variant="default" className="py-16 text-center text-surface-500">
          <div className="w-14 h-14 rounded-2xl bg-surface-100 text-surface-400 mx-auto flex items-center justify-center mb-3">
            <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
            </svg>
          </div>
          <h2 className="text-base font-bold text-surface-800">
            No compliance reports available
          </h2>
          <p className="text-xs text-surface-400 mt-1 max-w-sm mx-auto">
            {reports.length === 0
              ? 'Complete a product inspection and verification to generate official statutory audit reports.'
              : 'No reports match your current filter and search criteria.'}
          </p>
          <div className="mt-5 flex items-center justify-center gap-3">
            <Link to={ROUTES.UPLOAD}>
              <Button variant="primary" size="sm">
                Upload New Product
              </Button>
            </Link>
            <Link to={ROUTES.VERIFICATION}>
              <Button variant="secondary" size="sm">
                Open Verifications
              </Button>
            </Link>
          </div>
        </Card>
      )}

      {/* ── Report Details Modal ─────────────────────────────────────────── */}
      <Modal
        isOpen={isDetailsOpen}
        onClose={() => {
          setIsDetailsOpen(false);
          setSelectedReport(null);
        }}
        title={`Audit Report #${selectedReport?.id || ''}`}
        size="lg"
      >
        {detailsLoading ? (
          <div className="py-12">
            <Loading variant="spinner" size="md" text="Loading report audit details..." />
          </div>
        ) : selectedReport ? (
          <div className="space-y-5 text-xs text-surface-700">
            {/* Header Status & Overview */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-surface-50 border border-surface-200">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-surface-400">
                  Product Item
                </p>
                <h3 className="text-base font-bold text-surface-900 mt-0.5">
                  {selectedReport.product_name || 'Packaged Commodity Item'}
                </h3>
                <p className="text-xs text-surface-500">
                  Category: {selectedReport.category || 'General Foods'}
                </p>
              </div>

              <div className="flex items-center gap-2">
                {getStatusBadge(selectedReport.compliance_status || selectedReport.status)}
              </div>
            </div>

            {/* Executive Summary */}
            <div className="space-y-1">
              <h4 className="font-bold text-surface-900 uppercase tracking-wider text-[11px]">
                Executive Audit Summary
              </h4>
              <p className="text-surface-600 leading-relaxed bg-white p-3 rounded-xl border border-surface-200">
                {selectedReport.summary ||
                  'Automated verification evaluated packaging mandatory declarations according to the Legal Metrology (Packaged Commodities) Rules, 2011 and FSSAI Packaging Guidelines. Certified inspection records reflect optical scan and OCR extraction accuracy.'}
              </p>
            </div>

            {/* Findings List (if rules provided) */}
            {Array.isArray(selectedReport.rules) && selectedReport.rules.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-bold text-surface-900 uppercase tracking-wider text-[11px]">
                  Statutory Rule Findings ({selectedReport.rules.length})
                </h4>
                <div className="space-y-2 max-h-52 overflow-y-auto custom-scrollbar pr-1">
                  {selectedReport.rules.map((rule, idx) => (
                    <div
                      key={rule.id || idx}
                      className="p-2.5 rounded-lg border border-surface-200 bg-white flex items-center justify-between gap-2"
                    >
                      <div>
                        <span className="font-semibold text-surface-900 block">
                          {rule.rule_name}
                        </span>
                        <span className="text-[11px] text-surface-400 font-mono">
                          {rule.rule_identifier || 'Statutory mandate'}
                        </span>
                      </div>
                      <Badge
                        variant={(rule.status || '').toUpperCase() === 'PASS' ? 'success' : 'danger'}
                        size="xs"
                      >
                        {rule.status || 'PASS'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Download Buttons Bar */}
            <div className="pt-4 border-t border-surface-200 flex items-center justify-between gap-3">
              <span className="text-surface-400 text-[11px]">
                Generated by {selectedReport.generated_by || user?.name || 'Inspector'}
              </span>

              <div className="flex items-center gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleDownload(selectedReport.id, 'pdf')}
                  leftIcon={
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                    </svg>
                  }
                >
                  Download PDF
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleDownload(selectedReport.id, 'excel')}
                >
                  Excel Report
                </Button>
              </div>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* ── Generate Report Modal ────────────────────────────────────────── */}
      <Modal
        isOpen={isGenerateOpen}
        onClose={() => setIsGenerateOpen(false)}
        title="Generate Compliance Report"
        size="md"
      >
        <form onSubmit={handleGenerateSubmit} className="space-y-4 text-xs">
          <p className="text-surface-600">
            Select a verified inspection reference to generate an official statutory compliance audit certificate.
          </p>

          <div>
            <label htmlFor="gen-ref-id" className="block text-xs font-bold text-surface-700 mb-1">
              Verification Reference ID <span className="text-danger-500">*</span>
            </label>
            <Input
              id="gen-ref-id"
              placeholder="e.g. 1049"
              value={generateForm.verification_id}
              onChange={(e) =>
                setGenerateForm((prev) => ({ ...prev, verification_id: e.target.value }))
              }
              required
            />
          </div>

          <div>
            <label htmlFor="gen-format" className="block text-xs font-bold text-surface-700 mb-1">
              Report Format
            </label>
            <select
              id="gen-format"
              value={generateForm.format}
              onChange={(e) =>
                setGenerateForm((prev) => ({ ...prev, format: e.target.value }))
              }
              className="w-full px-3 py-2 text-xs rounded-xl bg-white border border-surface-200 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              <option value="PDF">PDF Document (Official Certificate)</option>
              <option value="EXCEL">Excel Spreadsheet (.xlsx)</option>
              <option value="CSV">CSV Data Export</option>
            </select>
          </div>

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="gen-evidence"
              checked={generateForm.include_evidence}
              onChange={(e) =>
                setGenerateForm((prev) => ({ ...prev, include_evidence: e.target.checked }))
              }
              className="rounded text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="gen-evidence" className="text-surface-700 font-medium cursor-pointer">
              Include OCR bounding boxes and raw extracted evidence
            </label>
          </div>

          <div className="pt-4 border-t border-surface-200 flex items-center justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => setIsGenerateOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" loading={generating}>
              Generate Report
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Reports;
