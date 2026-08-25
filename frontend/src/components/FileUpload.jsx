import { useState, useRef, useCallback } from 'react';
import { UPLOAD_CONFIG } from '../utils/constants';

/**
 * Premium Glassmorphic Drag & Drop image upload component.
 */
const FileUpload = ({
  onFileSelect,
  onError,
  disabled = false,
  className = '',
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const validateFile = useCallback((file) => {
    if (!file) return false;

    if (file.size === 0) {
      onError?.('The selected file is empty. Please choose a valid image.');
      return false;
    }

    const isAllowedType = UPLOAD_CONFIG.ALLOWED_MIME_TYPES.includes(file.type.toLowerCase()) ||
      /\.(jpe?g|png|webp)$/i.test(file.name);

    if (!isAllowedType) {
      onError?.('Please upload a valid JPG, JPEG, PNG, or WEBP image.');
      return false;
    }

    if (file.size > UPLOAD_CONFIG.MAX_FILE_SIZE_BYTES) {
      onError?.(`Image size exceeds the ${UPLOAD_CONFIG.MAX_FILE_SIZE_MB} MB limit. Please select a smaller file.`);
      return false;
    }

    return true;
  }, [onError]);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
      onFileSelect?.(file);
    }
    e.target.value = '';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragOver(true);
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
    if (file && validateFile(file)) {
      onFileSelect?.(file);
    }
  };

  const handleClick = () => {
    if (!disabled) fileInputRef.current?.click();
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
          glass-dropzone relative p-8 sm:p-12 text-center cursor-pointer select-none
          ${disabled ? 'opacity-60 cursor-not-allowed bg-slate-100/60' : ''}
          ${isDragOver ? 'drag-active scale-[1.005]' : ''}
        `}
      >
        <div className="flex flex-col items-center justify-center space-y-4">
          <div
            className={`
              w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-200 shadow-sm
              ${
                isDragOver
                  ? 'scale-110 bg-gradient-to-tr from-primary-600 to-cyan-500 text-white shadow-glow-primary'
                  : 'bg-primary-50 text-primary-600 border border-primary-100'
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

          <div className="space-y-1">
            <p className="text-base font-bold text-navy-900">
              {isDragOver ? (
                <span className="text-primary-600 font-extrabold">Drop the packaging label image here</span>
              ) : (
                <>
                  Drag & drop packaging label image, or{' '}
                  <span className="text-primary-600 font-bold underline underline-offset-4 hover:text-primary-700">
                    browse files
                  </span>
                </>
              )}
            </p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto font-normal">
              High-resolution photo showing statutory declarations (MRP, USP, Net Qty, Dates, Batch, Manufacturer)
            </p>
          </div>

          <div className="pt-2 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-400">
            <span className="px-3 py-1 rounded-xl bg-white/80 border border-slate-200/80 font-semibold text-slate-700 shadow-sm">
              JPG, PNG, WEBP
            </span>
            <span>•</span>
            <span className="font-medium">Max {UPLOAD_CONFIG.MAX_FILE_SIZE_MB} MB</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
