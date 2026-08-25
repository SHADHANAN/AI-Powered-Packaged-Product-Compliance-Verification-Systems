/**
 * General-purpose utility functions.
 */

/**
 * Concatenate CSS class names, filtering falsy values.
 * @param  {...string} classes
 * @returns {string}
 */
export const cn = (...classes) => classes.filter(Boolean).join(' ');

/**
 * Format a date string into a human-readable locale string.
 * @param {string|Date} date
 * @param {object} options — Intl.DateTimeFormat options
 * @returns {string}
 */
export const formatDate = (date, options = {}) => {
  const defaults = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options,
  };
  return new Date(date).toLocaleDateString('en-US', defaults);
};

/**
 * Format bytes into human-readable size string (e.g. 2.4 MB, 450 KB).
 * @param {number} bytes
 * @param {number} decimals
 * @returns {string}
 */
export const formatFileSize = (bytes, decimals = 1) => {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
};

/**
 * Truncate a string to a maximum length, appending an ellipsis.
 * @param {string} str
 * @param {number} maxLen
 * @returns {string}
 */
export const truncate = (str, maxLen = 50) => {
  if (!str) return '';
  return str.length > maxLen ? `${str.slice(0, maxLen)}…` : str;
};

/**
 * Basic debounce function.
 * @param {Function} fn
 * @param {number} delay — milliseconds
 * @returns {Function}
 */
export const debounce = (fn, delay = 300) => {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
};

/**
 * Extract a user-friendly error message from an Axios error response.
 * Maps status codes (400, 401, 403, 404, 413, 422, 500) to clear messages.
 * Never surfaces raw stack traces or internal backend errors.
 * @param {Error} error
 * @returns {string}
 */
export const getErrorMessage = (error) => {
  if (!error?.response) {
    return 'Unable to connect to the server. Please check your network connection.';
  }

  const status = error.response.status;
  const detail = error.response.data?.detail;

  switch (status) {
    case 400:
      return typeof detail === 'string'
        ? detail
        : 'Invalid upload request. Please check the selected file.';
    case 401:
      return 'Your session has expired. Please log in again.';
    case 403:
      return 'You do not have permission to perform this inspection upload.';
    case 404:
      return 'Upload endpoint not found. Please contact system administration.';
    case 413:
      return 'The uploaded file is too large. Maximum permitted file size is 10 MB.';
    case 422:
      if (Array.isArray(detail)) {
        return detail.map((d) => d.msg || d.message).join(' ');
      }
      return typeof detail === 'string'
        ? detail
        : 'Validation error: The uploaded package image format is unsupported.';
    case 500:
    case 502:
    case 503:
      return 'Server error occurred while processing package upload. Please try again.';
    default:
      return typeof detail === 'string'
        ? detail
        : 'Unable to complete product upload. Please try again.';
  }
};
