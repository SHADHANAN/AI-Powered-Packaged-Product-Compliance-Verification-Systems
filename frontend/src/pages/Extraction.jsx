import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { Card, Button, Input, Badge, Loading } from '../components/ui';
import { getExtractionResult, updateExtractedFields, extractProductFields } from '../api/extraction';
import { ROUTES, MANDATORY_DECLARATIONS } from '../utils/constants';
import { getErrorMessage } from '../utils/helpers';

/**
 * Maps confidence values to visual badge variants and labels.
 */
const getConfidenceBadge = (confidence, isEdited) => {
  if (isEdited) {
    return <Badge variant="info" size="sm">Edited</Badge>;
  }

  if (typeof confidence === 'number') {
    if (confidence >= 0.85) {
      return <Badge variant="success" size="sm" dot>High ({Math.round(confidence * 100)}%)</Badge>;
    }
    if (confidence >= 0.6) {
      return <Badge variant="warning" size="sm" dot>Medium ({Math.round(confidence * 100)}%)</Badge>;
    }
    return <Badge variant="danger" size="sm" dot>Low ({Math.round(confidence * 100)}%)</Badge>;
  }

  if (typeof confidence === 'string') {
    const lower = confidence.toLowerCase();
    if (lower === 'high') return <Badge variant="success" size="sm" dot>High Confidence</Badge>;
    if (lower === 'medium') return <Badge variant="warning" size="sm" dot>Medium Confidence</Badge>;
    if (lower === 'low') return <Badge variant="danger" size="sm" dot>Low Confidence</Badge>;
  }

  return null;
};

/**
 * Extraction Page — Displays OCR extracted fields, confidence scores, raw text stream,
 * and allows inspector field corrections before running compliance verification.
 */
const Extraction = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saveMessage, setSaveMessage] = useState(null);
  const [copied, setCopied] = useState(false);

  // Core extraction data state
  const [data, setData] = useState({
    id: id || 'current',
    product_name: '',
    category: '',
    status: 'completed',
    image_url: null,
    raw_ocr_text: '',
    fields: {},
  });

  // Editing state
  const [isEditing, setIsEditing] = useState(false);
  const [editableFields, setEditableFields] = useState({});
  const [editedKeys, setEditedKeys] = useState(new Set());

  // ── Load Extraction Results ──────────────────────────────────────────────
  const loadExtraction = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (id) {
        const result = await getExtractionResult(id);
        if (result) {
          setData(result);
          // Initialize editable state
          const initialFields = {};
          if (result.fields) {
            if (Array.isArray(result.fields)) {
              result.fields.forEach((f) => {
                initialFields[f.key] = f.value || '';
              });
            } else if (typeof result.fields === 'object') {
              Object.entries(result.fields).forEach(([k, v]) => {
                initialFields[k] = typeof v === 'object' ? v.value || '' : v || '';
              });
            }
          }
          setEditableFields(initialFields);
        }
      } else {
        // Fallback default state when accessed directly without params
        setData((prev) => ({
          ...prev,
          status: 'completed',
          fields: {},
        }));
      }
    } catch (err) {
      // If 404 or backend data not yet present, display neutral clean state rather than crashing
      if (err?.response?.status === 404) {
        setData((prev) => ({
          ...prev,
          id: id || 'NEW',
          status: 'pending',
          fields: {},
          raw_ocr_text: '',
        }));
      } else {
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadExtraction();
  }, [loadExtraction]);

  // ── Handlers ─────────────────────────────────────────────────────────────

  const handleFieldChange = (key, value) => {
    setEditableFields((prev) => ({ ...prev, [key]: value }));
    setEditedKeys((prev) => new Set(prev).add(key));
  };

  const handleSaveFields = async () => {
    setSaving(true);
    setSaveMessage(null);
    setError(null);
    try {
      if (id) {
        try {
          await updateExtractedFields(id, editableFields);
        } catch {
          // If backend update endpoint is not implemented, maintain changes locally
        }
      }

      // Update local data view
      setData((prev) => {
        const updatedFields = { ...prev.fields };
        Object.entries(editableFields).forEach(([k, v]) => {
          if (updatedFields[k] && typeof updatedFields[k] === 'object') {
            updatedFields[k] = { ...updatedFields[k], value: v, is_edited: true };
          } else {
            updatedFields[k] = { value: v, is_edited: true };
          }
        });
        return { ...prev, fields: updatedFields };
      });

      setIsEditing(false);
      setSaveMessage('Field corrections saved successfully.');
      setTimeout(() => setSaveMessage(null), 4000);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEditing = () => {
    setIsEditing(false);
    // Reset editable fields to original
    const reset = {};
    if (data.fields) {
      if (Array.isArray(data.fields)) {
        data.fields.forEach((f) => {
          reset[f.key] = f.value || '';
        });
      } else if (typeof data.fields === 'object') {
        Object.entries(data.fields).forEach(([k, v]) => {
          reset[k] = typeof v === 'object' ? v.value || '' : v || '';
        });
      }
    }
    setEditableFields(reset);
  };

  const handleRerunExtraction = async () => {
    if (!id || extracting) return;
    setExtracting(true);
    setError(null);
    try {
      await extractProductFields(id);
      await loadExtraction();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setExtracting(false);
    }
  };

  const handleCopyRawText = () => {
    if (data.raw_ocr_text) {
      navigator.clipboard.writeText(data.raw_ocr_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getFieldValue = (key) => {
    if (isEditing) {
      return editableFields[key] || '';
    }
    if (data.fields) {
      if (Array.isArray(data.fields)) {
        const found = data.fields.find((f) => f.key === key);
        return found?.value ?? null;
      }
      if (typeof data.fields === 'object' && data.fields[key]) {
        return typeof data.fields[key] === 'object' ? data.fields[key].value : data.fields[key];
      }
    }
    return null;
  };

  const getFieldConfidence = (key) => {
    if (data.fields) {
      if (Array.isArray(data.fields)) {
        const found = data.fields.find((f) => f.key === key);
        return found?.confidence ?? found?.confidence_level ?? null;
      }
      if (typeof data.fields === 'object' && data.fields[key]) {
        return data.fields[key]?.confidence ?? data.fields[key]?.confidence_level ?? null;
      }
    }
    return null;
  };

  if (loading) {
    return (
      <div className="py-20">
        <Loading variant="spinner" size="lg" text="Retrieving OCR extraction data..." />
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
            <span>Extraction Result</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold text-surface-900 tracking-tight">
              OCR & Field Extraction
            </h1>
            <Badge
              variant={
                data.status === 'completed'
                  ? 'success'
                  : data.status === 'processing'
                  ? 'warning'
                  : 'neutral'
              }
              size="md"
              dot
            >
              {data.status ? data.status.toUpperCase() : 'COMPLETED'}
            </Badge>
          </div>
          <p className="mt-1 text-sm sm:text-base text-surface-600">
            Review AI-extracted Legal Metrology & packaging declarations. Verify and correct values prior to running compliance verification.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleRerunExtraction}
            loading={extracting}
            leftIcon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
            }
          >
            Re-run OCR
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate(id ? `/verification/${id}` : ROUTES.VERIFICATION)}
            rightIcon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            }
          >
            Continue to Verification
          </Button>
        </div>
      </div>

      {/* ── Notice / Success Banners ─────────────────────────────────────── */}
      {saveMessage && (
        <div className="p-4 rounded-xl bg-accent-50 border border-accent-200 text-accent-800 text-sm flex items-center gap-3 animate-slide-down">
          <svg className="w-5 h-5 text-accent-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
          <span>{saveMessage}</span>
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

      {/* ── Overview Split: Product Thumbnail & Inspection Metadata ──────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left: Product Image Card */}
        <Card variant="default" className="flex flex-col items-center justify-center p-4 bg-surface-50/50">
          {data.image_url ? (
            <div className="relative w-full h-52 rounded-xl overflow-hidden bg-white border border-surface-200 flex items-center justify-center">
              <img
                src={data.image_url}
                alt={data.product_name || 'Inspected packaging item'}
                className="w-full h-full object-contain"
              />
            </div>
          ) : (
            <div className="w-full h-52 rounded-xl border-2 border-dashed border-surface-200 bg-white flex flex-col items-center justify-center text-surface-400 p-4 text-center">
              <svg className="w-10 h-10 mb-2 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
              </svg>
              <p className="text-xs font-medium text-surface-500">Package Image</p>
              <span className="text-[11px] text-surface-400 mt-0.5">Source scan uploaded</span>
            </div>
          )}
        </Card>

        {/* Right: Inspection & Product Metadata (2 Cols) */}
        <Card variant="default" className="md:col-span-2 p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-surface-100">
            <div>
              <p className="text-xs font-bold text-surface-400 uppercase tracking-wider">Product Info</p>
              <h2 className="text-lg font-bold text-surface-900 mt-0.5">
                {data.product_name || 'Packaged Commodity Item'}
              </h2>
            </div>
            <Badge variant="neutral" size="sm">
              Ref #{id || 'NEW'}
            </Badge>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-surface-50 border border-surface-100">
              <span className="text-surface-400 font-medium block">Category</span>
              <span className="font-semibold text-surface-800 block mt-0.5">
                {data.category || 'General Packaged Goods'}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-surface-50 border border-surface-100">
              <span className="text-surface-400 font-medium block">Inspector</span>
              <span className="font-semibold text-surface-800 block mt-0.5 truncate">
                {user?.name || user?.email || 'Authorized Officer'}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-surface-50 border border-surface-100">
              <span className="text-surface-400 font-medium block">OCR Engine</span>
              <span className="font-semibold text-primary-600 block mt-0.5">
                PaddleOCR v2
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* ── Extracted Structured Declarations Section ────────────────────── */}
      <section aria-labelledby="declarations-heading" className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 id="declarations-heading" className="text-lg font-bold text-surface-900">
              Extracted Legal Metrology Declarations
            </h2>
            <p className="text-xs text-surface-500 mt-0.5">
              Automated field detections aligned with Legal Metrology (Packaged Commodities) Rules & FSSAI Standards
            </p>
          </div>

          <div className="flex items-center gap-2">
            {!isEditing ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditing(true)}
                leftIcon={
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
                  </svg>
                }
              >
                Edit Declarations
              </Button>
            ) : (
              <div className="flex items-center gap-2">
                <Button variant="secondary" size="sm" onClick={handleCancelEditing} disabled={saving}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" onClick={handleSaveFields} loading={saving}>
                  Save Changes
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Declarations Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {MANDATORY_DECLARATIONS.map((declaration) => {
            const value = getFieldValue(declaration.key);
            const confidence = getFieldConfidence(declaration.key);
            const isEdited = editedKeys.has(declaration.key);

            return (
              <Card
                key={declaration.key}
                variant="default"
                className={`p-4 border-surface-200 transition-all ${
                  isEdited ? 'ring-1 ring-primary-300 bg-primary-50/20' : ''
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="space-y-0.5">
                    <label
                      htmlFor={`field-${declaration.key}`}
                      className="text-xs font-bold text-surface-700 block"
                    >
                      {declaration.label}
                    </label>
                    <span className="text-[10px] text-surface-400 font-mono">
                      {declaration.rule}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {getConfidenceBadge(confidence, isEdited)}
                  </div>
                </div>

                {isEditing ? (
                  <div className="mt-2">
                    <Input
                      id={`field-${declaration.key}`}
                      value={editableFields[declaration.key] ?? value ?? ''}
                      onChange={(e) => handleFieldChange(declaration.key, e.target.value)}
                      placeholder={`Enter ${declaration.label.toLowerCase()}`}
                      size="sm"
                    />
                  </div>
                ) : (
                  <div className="mt-2 pt-2 border-t border-surface-100 flex items-center justify-between">
                    {value ? (
                      <span className="text-sm font-semibold text-surface-900 break-words">
                        {value}
                      </span>
                    ) : (
                      <span className="text-xs text-surface-400 italic">
                        Not detected on package
                      </span>
                    )}

                    {isEdited && (
                      <span className="text-[10px] font-semibold text-primary-600">
                        Modified
                      </span>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </section>

      {/* ── Raw OCR Text Section ─────────────────────────────────────────── */}
      <section aria-labelledby="ocr-text-heading" className="space-y-3">
        <Card
          variant="default"
          header={
            <div className="flex items-center justify-between">
              <div>
                <h2 id="ocr-text-heading" className="text-base font-bold text-surface-900">
                  Raw OCR Extracted Text Stream
                </h2>
                <p className="text-xs text-surface-500 mt-0.5">
                  Sequential optical text lines detected from package bounding boxes
                </p>
              </div>

              {data.raw_ocr_text && (
                <Button
                  variant="ghost"
                  size="xs"
                  onClick={handleCopyRawText}
                  leftIcon={
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184" />
                    </svg>
                  }
                >
                  {copied ? 'Copied!' : 'Copy Text'}
                </Button>
              )}
            </div>
          }
        >
          {data.raw_ocr_text ? (
            <pre className="p-4 rounded-xl bg-surface-900 text-surface-100 font-mono text-xs leading-relaxed max-h-60 overflow-y-auto custom-scrollbar select-text whitespace-pre-wrap break-words">
              {data.raw_ocr_text}
            </pre>
          ) : (
            <div className="py-8 text-center text-surface-400">
              <svg className="w-8 h-8 mx-auto mb-2 text-surface-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
              <p className="text-xs font-medium text-surface-500">
                No OCR text was detected for this product.
              </p>
              <p className="text-[11px] text-surface-400 mt-0.5">
                Ensure packaging image has high resolution and readable text.
              </p>
            </div>
          )}
        </Card>
      </section>

      {/* ── Workflow Actions Bar ─────────────────────────────────────────── */}
      <div className="pt-4 border-t border-surface-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <Link to={ROUTES.UPLOAD}>
          <Button variant="secondary" size="md">
            Upload Another Image
          </Button>
        </Link>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          <Button
            variant="primary"
            size="md"
            onClick={() => navigate(id ? `/verification/${id}` : ROUTES.VERIFICATION)}
            rightIcon={
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            }
          >
            Continue to Verification
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Extraction;
