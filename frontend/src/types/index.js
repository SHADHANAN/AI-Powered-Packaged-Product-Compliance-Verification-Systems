/**
 * Shared TypeScript-style type definitions (JSDoc).
 * These serve as documentation for data shapes used across the frontend.
 */

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} email
 * @property {string} name
 * @property {boolean} authenticated
 */

/**
 * @typedef {Object} Product
 * @property {number} id
 * @property {string} name
 * @property {string} barcode
 * @property {string} category
 * @property {string} created_at
 */

/**
 * @typedef {'compliant'|'non_compliant'|'pending'|'error'} ComplianceStatus
 */

/**
 * @typedef {Object} VerificationResult
 * @property {number} id
 * @property {number} product_id
 * @property {ComplianceStatus} status
 * @property {number} score
 * @property {Array} issues
 * @property {string} created_at
 */

/**
 * @typedef {Object} ApiError
 * @property {string} detail
 * @property {number} status_code
 */

export {};
