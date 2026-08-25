import { useState, useRef, useCallback } from 'react';
import { UPLOAD_CONFIG } from '../utils/constants';

/**
 * FileUpload — Reusable Drag & Drop image upload component.
 *
 * Supports:
 * - Drag-and-drop with active drag-over indicator
 * - Keyboard accessible file picker
 * - Client-side validation (MIME type, size limit, non-empty)
 * - Clean user-friendly error callback
 *
 * @param {Function} onFileSelect - Called with valid File object
 * @param {Function} onError - Called with error message string
 * @param {boolean} disabled - Disables interaction during upload
 * @param {string} className - Optional container styling
 */
const FileUpload = ({
  onFileSelect,
  onError,
  disabled = false,
  className = '',
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  // Validate selected file against requirements
  const validateFile = useCallback((file) => {
    if (!file) return false;

    // Check empty file
    if (file.size === 0) {
      onError?.('The selected file is empty. Please choose a valid image.');
      return false;
    }

    // Check file type
    const isAllowedType = UPLOAD_CONFIG.ALLOWED_MIME_TYPES.includes(file.type.toLowerCase()) ||
      /\.(jpe?g|png|webp)$/i.test(file.name);

    if (!isAllowedType) {
      onError?.('Please upload a valid JPG, JPEG, PNG, or WEBP image.');
      return false;
    }

    // Check file size (10 MB maximum)
    if (file.size > UPLOAD_CONFIG.MAX_FILE_SIZE_BYTES) {
      onError?.(`Image size exceeds the ${UPLOAD_CONFIG.MAX_FILE_SIZE_MB} MB limit. Please select a smaller file.`);
      return false;
    }

    return true;
  }, [onError]);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (validateFile(file)) {
        onFileSelect?.(file);
      }
    }
    // Reset file input value so selecting the same file again triggers onChange
    e.target.value = '';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragOver(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (disabled) return;

    const file = e.dataTransfer.files?.[0];
    if (file) {
      if (validateFile(file)) {
        onFileSelect?.(file);
      }
    }
  };

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  const handleKeyDown = (e) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  };

  return (
    <div className={`w-full ${className}`}>
      {/* Hidden native file input */}
      <input
        ref={fileInputRef}
        type="file"
        id="packaged-product-file-input"
        accept={UPLOAD_CONFIG.ALLOWED_EXTENSIONS.join(',')}
        onChange={handleFileChange}
        disabled={disabled}
        className="sr-only"
        aria-label="Upload packaged product image"
      />

      {/* Drag and Drop Zone */}
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onDragOver={handleDragOver}
        onDragEnter={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        aria-disabled={disabled}
        aria-controls="packaged-product-file-input"
        className={`
          relative border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center
          transition-all duration-200 cursor-pointer select-none
          ${
            disabled
              ? 'opacity-60 cursor-not-allowed bg-surface-50 border-surface-200'
              : isDragOver
              ? 'border-primary-500 bg-primary-50/60 shadow-glow scale-[1.005]'
              : 'border-surface-300 bg-white hover:border-primary-400 hover:bg-surface-50/60 hover:shadow-sm'
          }
        `}
      >
        <div className="flex flex-col items-center justify-center space-y-4">
          {/* Upload Icon */}
          <div
            className={`
              w-16 h-16 rounded-2xl flex items-center justify-center transition-transform duration-200
              ${
                isDragOver
                  ? 'scale-110 gradient-primary text-white shadow-glow'
                  : 'bg-primary-50 text-primary-600'
              }
            `}
          >
            <svg
              className="w-8 h-8"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.75}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z"
              />
            </svg>
          </div>

          {/* Prompt Copy */}
          <div className="space-y-1">
            <p className="text-base font-semibold text-surface-800">
              {isDragOver ? (
                <span className="text-primary-600">Drop the packaging image here</span>
              ) : (
                <>
                  Drag & drop packaging image, or{' '}
                  <span className="text-primary-600 underline underline-offset-4 hover:text-primary-700">
                    browse files
                  </span>
                </>
              )}
            </p>
            <p className="text-xs text-surface-500 max-w-sm mx-auto">
              Upload high-resolution label photos showing Legal Metrology declarations, MRP, Batch, & Expiry
            </p>
          </div>

          {/* Format Constraints Badge */}
          <div className="pt-2 flex flex-wrap items-center justify-center gap-2 text-xs text-surface-400">
            <span className="px-2.5 py-1 rounded-lg bg-surface-100 font-medium text-surface-600">
              JPG, PNG, WEBP
            </span>
            <span>•</span>
            <span>Max {UPLOAD_CONFIG.MAX_FILE_SIZE_MB} MB</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
