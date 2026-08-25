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
 * @param {Error} error
 * @returns {string}
 */
export const getErrorMessage = (error) => {
  if (error?.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error?.response?.data?.message) {
    return error.response.data.message;
  }
  if (error?.message) {
    return error.message;
  }
  return 'An unexpected error occurred.';
};
