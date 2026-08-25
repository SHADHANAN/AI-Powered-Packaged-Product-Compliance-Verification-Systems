import { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import FileUpload from '../components/FileUpload';
import { Card, Button, Input, Badge, Loading } from '../components/ui';
import { uploadProductImage } from '../api/products';
import { ROUTES } from '../utils/constants';
import { formatFileSize, getErrorMessage } from '../utils/helpers';

/**
 * Inspection Workstation Upload Page.
 */
const Upload = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

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

  const submittingRef = useRef(false);

  const cleanupPreview = useCallback(() => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
  }, [previewUrl]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleFileSelect = (file) => {
    cleanupPreview();
    setError(null);
    setSuccessResult(null);
    setSelectedFile(file);
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
      setError('Please select a product packaging label image to upload.');
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

      setSuccessResult(response || { message: 'Product registered successfully for compliance verification.' });
      handleRemoveFile();
    } catch (err) {
      setError(getErrorMessage(err));
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
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      {/* ── Page Header ──────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-bold text-primary-600 uppercase tracking-widest mb-1 font-mono">
            <Link to={ROUTES.DASHBOARD} className="hover:underline">
              COMMAND CENTER
            </Link>
            <span>/</span>
            <span>NEW INSPECTION</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-command-900 tracking-tight uppercase">
            New Product Inspection
          </h1>
          <p className="mt-0.5 text-xs sm:text-sm text-slate-500 font-normal">
            Upload packaged commodity labels for automated OCR declaration extraction and Legal Metrology rule verification.
          </p>
        </div>

        <div className="self-start sm:self-auto">
          <Link to={ROUTES.DASHBOARD}>
            <Button variant="secondary" size="sm">
              Back to Overview
            </Button>
          </Link>
        </div>
      </div>

      {/* ── Error Banner ─────────────────────────────────────────────────── */}
      {error && (
        <div
          role="alert"
          aria-live="assertive"
          className="flex items-start justify-between p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold animate-slide-down"
        >
          <div className="flex items-start gap-2.5">
            <svg
              className="w-4 h-4 text-rose-600 shrink-0 mt-0.5"
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
              <p className="font-bold">Inspection Notice</p>
              <p className="mt-0.5 text-rose-700 font-normal">{error}</p>
            </div>
          </div>
          <button
            onClick={() => setError(null)}
            className="p-1 rounded-lg text-rose-400 hover:text-rose-700 hover:bg-rose-100 transition-colors"
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
        <Card variant="default" className="border-emerald-200 bg-emerald-50/40 p-6 sm:p-8 animate-scale-in">
          <div className="flex flex-col items-center text-center space-y-4 max-w-lg mx-auto">
            <div className="w-14 h-14 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center shadow-sm">
              <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
            </div>

            <div className="space-y-1">
              <h2 className="text-xl font-black text-command-900">
                Product Registered for Verification
              </h2>
              <p className="text-xs sm:text-sm text-slate-600">
                {successResult.message || 'Packaging image received and queued for optical character recognition and statutory checks.'}
              </p>
            </div>

            {(successResult.product_id || successResult.verification_id || successResult.id) && (
              <div className="p-3 rounded-xl bg-white border border-emerald-200 text-xs font-mono">
                Verification Reference ID:{' '}
                <span className="font-bold text-emerald-800">
                  #{successResult.verification_id || successResult.product_id || successResult.id}
                </span>
              </div>
            )}

            <div className="pt-3 flex flex-wrap items-center justify-center gap-3">
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

              <Button variant="secondary" size="md" onClick={handleResetForm}>
                Upload Another Product
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* ── Main Workstation Layout ──────────────────────────────────────── */}
      {!successResult && (
        <>
          {!selectedFile ? (
            /* Large Initial Upload Dropzone */
            <Card variant="default" className="p-6 sm:p-10 space-y-6">
              <div className="text-center max-w-lg mx-auto space-y-1 mb-2">
                <h2 className="text-base sm:text-lg font-black text-command-900 uppercase tracking-tight">
                  Packaging Label Upload
                </h2>
                <p className="text-xs text-slate-500">
                  Submit clear photographs of commodity packages to evaluate statutory compliance under Legal Metrology Rules.
                </p>
              </div>

              <FileUpload
                onFileSelect={handleFileSelect}
                onError={handleValidationError}
                disabled={uploading}
              />

              <div className="pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-3 gap-4 text-center text-xs text-slate-500">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                  <span className="font-bold text-command-900 block mb-0.5">High Clarity</span>
                  <span>Ensure MRP, dates, and declarations are legible</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                  <span className="font-bold text-command-900 block mb-0.5">All Label Sides</span>
                  <span>Front and principal display panels supported</span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                  <span className="font-bold text-command-900 block mb-0.5">Automated OCR</span>
                  <span>PaddleOCR multi-lingual text extraction pipeline</span>
                </div>
              </div>
            </Card>
          ) : (
            /* Two-Column Inspection Workstation */
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-scale-in">
              {/* Left Column (7 cols): Large Product Image Preview */}
              <div className="lg:col-span-7 space-y-4">
                <Card variant="default" className="p-5 space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <Badge variant="success" size="xs" dot>
                        LABEL LOADED
                      </Badge>
                      <span className="text-xs text-slate-500 font-medium">Ready for OCR processing</span>
                    </div>

                    <button
                      onClick={handleRemoveFile}
                      disabled={uploading}
                      className="text-xs text-rose-600 hover:text-rose-800 font-bold uppercase tracking-wider"
                    >
                      Change Image
                    </button>
                  </div>

                  {/* Large Image Frame */}
                  <div className="relative rounded-xl overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center min-h-[280px] max-h-[420px] p-2">
                    <img
                      src={previewUrl}
                      alt="Product inspection preview"
                      className="max-h-[400px] w-auto max-w-full object-contain rounded-lg shadow-sm"
                    />
                    <div className="absolute bottom-3 right-3 px-2.5 py-1 rounded-md bg-black/70 backdrop-blur-md text-[10px] font-mono text-cyan-300 border border-white/10">
                      INSPECTION VIEW
                    </div>
                  </div>

                  {/* File Metadata Details */}
                  <div className="grid grid-cols-3 gap-3 text-xs pt-1">
                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                      <span className="text-slate-400 font-bold uppercase text-[10px] block">File Name</span>
                      <span className="font-bold text-command-900 truncate block mt-0.5" title={selectedFile.name}>
                        {selectedFile.name}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                      <span className="text-slate-400 font-bold uppercase text-[10px] block">Size</span>
                      <span className="font-bold text-command-900 block mt-0.5">
                        {formatFileSize(selectedFile.size)}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                      <span className="text-slate-400 font-bold uppercase text-[10px] block">Format</span>
                      <span className="font-bold text-command-900 uppercase block mt-0.5">
                        {selectedFile.type || selectedFile.name.split('.').pop()}
                      </span>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Right Column (5 cols): Inspection Metadata & Trigger Action */}
              <div className="lg:col-span-5 space-y-4">
                <Card variant="default" className="p-5 sm:p-6 space-y-5">
                  <div>
                    <h2 className="text-sm font-black uppercase tracking-wider text-command-900">
                      Product Information
                    </h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Optional metadata to associate with this statutory inspection audit
                    </p>
                  </div>

                  <div className="space-y-3.5">
                    <Input
                      id="product-name"
                      label="Product / Commodity Name"
                      name="name"
                      value={metadata.name}
                      onChange={handleMetadataChange}
                      placeholder="e.g. Fortified Wheat Flour 5kg"
                      disabled={uploading}
                      size="sm"
                    />

                    <Input
                      id="product-category"
                      label="Product Category"
                      name="category"
                      value={metadata.category}
                      onChange={handleMetadataChange}
                      placeholder="e.g. Food & Grocery, Cosmetics"
                      disabled={uploading}
                      size="sm"
                    />

                    <Input
                      id="product-batch"
                      label="Batch / Lot Identification"
                      name="batch_number"
                      value={metadata.batch_number}
                      onChange={handleMetadataChange}
                      placeholder="e.g. LOT-2026-X01"
                      disabled={uploading}
                      size="sm"
                    />
                  </div>

                  {/* Upload Progress Bar */}
                  {uploading && (
                    <div className="space-y-2 pt-2 animate-fade-in">
                      <div className="flex items-center justify-between text-xs font-bold text-command-900">
                        <span className="flex items-center gap-1.5 text-primary-600">
                          <span className="w-2 h-2 rounded-full bg-primary-600 animate-ping" />
                          Running PaddleOCR extraction...
                        </span>
                        <span>{uploadProgress > 0 ? `${uploadProgress}%` : 'Processing...'}</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full bg-primary-600 rounded-full transition-all duration-300 ease-out"
                          style={{ width: `${Math.max(uploadProgress, 20)}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-3">
                    <Button
                      variant="secondary"
                      size="md"
                      onClick={handleResetForm}
                      disabled={uploading}
                    >
                      Cancel
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
                          <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                        </svg>
                      }
                    >
                      {uploading ? 'Processing…' : 'Start Verification'}
                    </Button>
                  </div>
                </Card>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Upload;
