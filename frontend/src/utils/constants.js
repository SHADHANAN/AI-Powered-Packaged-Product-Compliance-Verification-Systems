/**
 * Application-wide constants.
 * Keep business/compliance logic out — this is structural only.
 */

export const APP_NAME = 'ComplianceAI';

export const ROUTES = {
  HOME:         '/',
  LOGIN:        '/login',
  DASHBOARD:    '/dashboard',
  UPLOAD:       '/upload',
  VERIFICATION: '/verification',
  REPORTS:      '/reports',
  HISTORY:      '/history',
};

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN:    '/auth/login',
    REGISTER: '/auth/register',
    ME:       '/auth/me',
  },
  PRODUCTS:         '/products',
  PRODUCTS_UPLOAD:  '/products/upload',
  COMPLIANCE:       '/compliance',
  EXTRACTION:       '/extraction',
  OCR:              '/ocr',
  REPORTS:          '/reports',
  VERIFICATIONS:    '/verifications',
};

/**
 * Supported user roles (must match backend enum).
 */
export const ROLES = {
  ADMIN:     'ADMIN',
  INSPECTOR: 'INSPECTOR',
  VIEWER:    'VIEWER',
};

/**
 * Upload validation configuration
 */
export const UPLOAD_CONFIG = {
  MAX_FILE_SIZE_BYTES: 10 * 1024 * 1024, // 10 MB
  MAX_FILE_SIZE_MB: 10,
  ALLOWED_MIME_TYPES: ['image/jpeg', 'image/png', 'image/webp'],
  ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.webp'],
  ACCEPTED_FORMATS_STRING: 'JPG, JPEG, PNG, WEBP',
};
