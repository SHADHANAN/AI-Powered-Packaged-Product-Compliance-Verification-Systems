import { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import FileUpload from '../components/FileUpload';
import { Card, Button, Input, Badge, Loading } from '../components/ui';
import { uploadProductImage } from '../api/products';
import { ROUTES } from '../utils/constants';
import { formatFileSize, getErrorMessage } from '../utils/helpers';

/**
 * Upload Page — Packaged product image submission for compliance verification.
 *
 * Implements:
 * - Drag-and-drop & native file picker
 * - Format & size validation (JPG/PNG/WEBP, Max 10MB)
 * - Safe object URL image preview with automatic cleanup
 * - Optional inspection metadata (Product Name, Category, Batch Number)
 * - Multipart/form-data upload to backend API
 * - Duplicate submission prevention
 * - Comprehensive state transitions (Initial, Selected, Uploading, Success, Error)
 */
const Upload = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // State management
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [metadata, setMetadata] = useState({
    name: '',
    category: '',
    batch_number: '',
  });

  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [successResult, setSuccessResult] = useState(null);
  const [error, setError] = useState(null);

  // Ref lock to prevent duplicate concurrent submissions
  const submittingRef = useRef(false);

  // Clean up object URL when component unmounts or preview changes
  const cleanupPreview = useCallback(() => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
  }, [previewUrl]);

  useEffect(() => {
    return () => {
      // Unmount cleanup
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleFileSelect = (file) => {
    cleanupPreview();
    setError(null);
    setSuccessResult(null);
    setSelectedFile(file);

    // Create safe object URL for preview
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleValidationError = (errorMessage) => {
    setError(errorMessage);
    handleRemoveFile();
  };

  const handleRemoveFile = () => {
    cleanupPreview();
    setSelectedFile(null);
    setUploadProgress(0);
    setError(null);
  };

  const handleMetadataChange = (e) => {
    const { name, value } = e.target;
    setMetadata((prev) => ({ ...prev, [name]: value }));
  };

  const handleUpload = async (e) => {
    e?.preventDefault();

    if (!selectedFile) {
      setError('Please select a product packaging image to upload.');
      return;
    }

    if (submittingRef.current || uploading) return;

    submittingRef.current = true;
    setUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const response = await uploadProductImage(
        selectedFile,
        metadata,
        (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percent);
          }
        }
      );

      setSuccessResult(response || { message: 'Product uploaded successfully.' });
      handleRemoveFile();
    } catch (err) {
      const friendlyMessage = getErrorMessage(err);
      setError(friendlyMessage);
    } finally {
      submittingRef.current = false;
      setUploading(false);
    }
  };

  const handleResetForm = () => {
    handleRemoveFile();
    setSuccessResult(null);
    setError(null);
    setMetadata({ name: '', category: '', batch_number: '' });
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
      {/* ── Page Header ──────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-surface-200">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-primary-600 uppercase tracking-wider mb-1">
            <Link to={ROUTES.DASHBOARD} className="hover:underline">
              Dashboard
            </Link>
            <span>/</span>
            <span>Inspection Upload</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-surface-900 tracking-tight">
            Upload Product
          </h1>
          <p className="mt-1 text-sm sm:text-base text-surface-600">
            Upload packaged product images or packaging labels for automated OCR text extraction and compliance verification.
          </p>
        </div>

        {/* Action shortcut */}
        <div className="self-start sm:self-auto">
          <Link to={ROUTES.DASHBOARD}>
            <Button variant="secondary" size="sm">
              Back to Dashboard
            </Button>
          </Link>
        </div>
      </div>

      {/* ── Error Banner ─────────────────────────────────────────────────── */}
      {error && (
        <div
          role="alert"
          aria-live="assertive"
          className="flex items-start justify-between p-4 rounded-2xl bg-danger-50 border border-danger-200 text-danger-800 text-sm animate-slide-down shadow-sm"
        >
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-danger-500 shrink-0 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
              />
            </svg>
            <div>
              <p className="font-semibold">Upload Notice</p>
              <p className="mt-0.5 text-danger-700">{error}</p>
            </div>
          </div>
          <button
            onClick={() => setError(null)}
            className="p-1 rounded-lg text-danger-400 hover:text-danger-700 hover:bg-danger-100 transition-colors"
            aria-label="Dismiss error"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* ── Success State Card ───────────────────────────────────────────── */}
      {successResult && (
        <Card variant="elevated" className="border-accent-200 bg-accent-50/40 p-6 sm:p-8 animate-scale-in">
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-accent-100 text-accent-700 flex items-center justify-center shadow-sm">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
            </div>

            <div className="space-y-1">
              <h2 className="text-xl font-bold text-surface-900">
                Product Uploaded Successfully
              </h2>
              <p className="text-sm text-surface-600 max-w-md">
                {successResult.message || 'The packaging image was accepted and sent to the compliance verification engine.'}
              </p>
            </div>

            {/* If backend returns a product or verification identifier */}
            {(successResult.product_id || successResult.verification_id || successResult.id) && (
              <div className="p-3 rounded-xl bg-white border border-accent-200 text-xs text-surface-700 font-mono">
                Verification Reference ID:{' '}
                <span className="font-bold text-accent-800">
                  #{successResult.verification_id || successResult.product_id || successResult.id}
                </span>
              </div>
            )}

            <div className="pt-4 flex flex-wrap items-center justify-center gap-3">
              <Button
                variant="primary"
                size="md"
                onClick={() => {
                  const refId = successResult.product_id || successResult.verification_id || successResult.id;
                  navigate(refId ? `/extraction/${refId}` : ROUTES.EXTRACTION);
                }}
                rightIcon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                  </svg>
                }
              >
                Review Extracted Declarations
              </Button>

              <Button
                variant="outline"
                size="md"
                onClick={() => navigate(ROUTES.VERIFICATION)}
              >
                View Verifications
              </Button>

              <Button variant="secondary" size="md" onClick={handleResetForm}>
                Upload Another Product
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* ── Main Upload Form Layout ──────────────────────────────────────── */}
      {!successResult && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left / Center: Upload Zone + Preview (2 Cols) */}
          <div className="lg:col-span-2 space-y-6">
            <Card variant="default" className="space-y-6">
              <div>
                <h2 className="text-lg font-bold text-surface-900">
                  Product Packaging Image
                </h2>
                <p className="text-xs text-surface-500 mt-0.5">
                  Select or drag the front/back panel packaging photograph to inspect
                </p>
              </div>

              {/* Upload Input / Drop Zone (when no file selected) */}
              {!selectedFile ? (
                <FileUpload
                  onFileSelect={handleFileSelect}
                  onError={handleValidationError}
                  disabled={uploading}
                />
              ) : (
                /* Selected File Preview Card */
                <div className="space-y-4 rounded-2xl border border-surface-200 bg-surface-50/50 p-4 sm:p-5 animate-scale-in">
                  <div className="flex items-center justify-between pb-3 border-b border-surface-200">
                    <div className="flex items-center gap-2">
                      <Badge variant="success" size="sm" dot>
                        Image Selected
                      </Badge>
                      <span className="text-xs text-surface-500">Ready for inspection</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={handleRemoveFile}
                        disabled={uploading}
                        className="text-danger-600 hover:text-danger-700 hover:bg-danger-50"
                      >
                        Remove
                      </Button>
                    </div>
                  </div>

                  {/* Image Preview Container */}
                  <div className="relative rounded-xl overflow-hidden bg-surface-900/5 border border-surface-200 flex items-center justify-center min-h-[220px] max-h-[360px]">
                    <img
                      src={previewUrl}
                      alt="Selected packaging label preview"
                      className="max-h-[340px] w-auto max-w-full object-contain rounded-lg"
                    />
                  </div>

                  {/* File Metadata Details */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-white border border-surface-200">
                      <span className="text-surface-400 font-medium block">File Name</span>
                      <span className="font-semibold text-surface-800 truncate block mt-0.5" title={selectedFile.name}>
                        {selectedFile.name}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-white border border-surface-200">
                      <span className="text-surface-400 font-medium block">File Size</span>
                      <span className="font-semibold text-surface-800 block mt-0.5">
                        {formatFileSize(selectedFile.size)}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-white border border-surface-200">
                      <span className="text-surface-400 font-medium block">File Type</span>
                      <span className="font-semibold text-surface-800 uppercase block mt-0.5">
                        {selectedFile.type || selectedFile.name.split('.').pop()}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Upload Progress Bar (when uploading) */}
              {uploading && (
                <div className="space-y-2 pt-2 animate-fade-in">
                  <div className="flex items-center justify-between text-xs font-semibold text-surface-700">
                    <span className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-primary-500 animate-ping" />
                      Uploading & initializing OCR engine...
                    </span>
                    <span>{uploadProgress > 0 ? `${uploadProgress}%` : 'Processing...'}</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-surface-200 overflow-hidden">
                    <div
                      className="h-full bg-primary-600 rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${Math.max(uploadProgress, 15)}%` }}
                    />
                  </div>
                </div>
              )}
            </Card>

            {/* Optional Inspection Details Metadata Card */}
            <Card variant="default" className="space-y-4">
              <div>
                <h2 className="text-base font-bold text-surface-900">
                  Inspection Details <span className="text-xs text-surface-400 font-normal">(Optional)</span>
                </h2>
                <p className="text-xs text-surface-500 mt-0.5">
                  Provide supplementary product packaging information for faster metadata tagging
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  id="product-name"
                  label="Product / Commodity Name"
                  name="name"
                  value={metadata.name}
                  onChange={handleMetadataChange}
                  placeholder="e.g. Premium Basmati Rice 1kg"
                  disabled={uploading}
                  size="sm"
                />

                <Input
                  id="product-category"
                  label="Product Category"
                  name="category"
                  value={metadata.category}
                  onChange={handleMetadataChange}
                  placeholder="e.g. Food & Beverages, Cosmetics, FMCG"
                  disabled={uploading}
                  size="sm"
                />

                <div className="sm:col-span-2">
                  <Input
                    id="product-batch"
                    label="Batch / Lot Number"
                    name="batch_number"
                    value={metadata.batch_number}
                    onChange={handleMetadataChange}
                    placeholder="e.g. BATCH-2026-X99"
                    disabled={uploading}
                    size="sm"
                  />
                </div>
              </div>
            </Card>

            {/* Submit & Cancel Action Bar */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                variant="secondary"
                size="md"
                onClick={handleResetForm}
                disabled={uploading || (!selectedFile && !metadata.name)}
              >
                Reset
              </Button>

              <Button
                id="start-verification-button"
                variant="primary"
                size="md"
                onClick={handleUpload}
                loading={uploading}
                disabled={!selectedFile || uploading}
                rightIcon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                  </svg>
                }
              >
                {uploading ? 'Processing Image...' : 'Start Verification'}
              </Button>
            </div>
          </div>

          {/* Right Column: Inspection Guidelines & Legal Standards (1 Col) */}
          <div className="space-y-6">
            {/* Guidelines Card */}
            <Card variant="default" className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a3 3 0 1 0-3-3m3 3h3" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm font-bold text-surface-900">
                    Inspection Guidelines
                  </h3>
                  <p className="text-[11px] text-surface-500">For optimal OCR verification</p>
                </div>
              </div>

              <ul className="space-y-2.5 text-xs text-surface-600">
                <li className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-accent-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  <span><strong>Clear Lighting:</strong> Ensure the label text is sharp, glare-free, and not obscured by shadows.</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-accent-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  <span><strong>Mandatory Declarations:</strong> Capture MRP, Net Quantity, Best Before date, and Manufacturer details clearly.</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-accent-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  <span><strong>Orientation:</strong> Upload images in upright orientation for accurate font size and layout ratio analysis.</span>
                </li>
              </ul>
            </Card>

            {/* Standards Checked Card */}
            <Card variant="default" className="space-y-3 bg-surface-50/50">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-surface-700 uppercase tracking-wider">
                  Automated Checks
                </h3>
                <Badge variant="info" size="sm">
                  5 Rules
                </Badge>
              </div>

              <div className="space-y-2 text-xs">
                <div className="p-2 rounded-lg bg-white border border-surface-200 flex items-center justify-between">
                  <span className="font-medium text-surface-700">MRP Declaration</span>
                  <span className="text-[11px] text-surface-400">Rule 6(1)(e)</span>
                </div>
                <div className="p-2 rounded-lg bg-white border border-surface-200 flex items-center justify-between">
                  <span className="font-medium text-surface-700">Net Quantity / USP</span>
                  <span className="text-[11px] text-surface-400">Rule 6(1)(c)</span>
                </div>
                <div className="p-2 rounded-lg bg-white border border-surface-200 flex items-center justify-between">
                  <span className="font-medium text-surface-700">Mfg / Expiry Date</span>
                  <span className="text-[11px] text-surface-400">Rule 6(1)(d)</span>
                </div>
                <div className="p-2 rounded-lg bg-white border border-surface-200 flex items-center justify-between">
                  <span className="font-medium text-surface-700">Manufacturer Info</span>
                  <span className="text-[11px] text-surface-400">Rule 6(1)(a)</span>
                </div>
                <div className="p-2 rounded-lg bg-white border border-surface-200 flex items-center justify-between">
                  <span className="font-medium text-surface-700">Consumer Care Contact</span>
                  <span className="text-[11px] text-surface-400">Rule 6(1)(f)</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default Upload;
