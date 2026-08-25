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
  PRODUCTS:      '/products',
  COMPLIANCE:    '/compliance',
  EXTRACTION:    '/extraction',
  OCR:           '/ocr',
  REPORTS:       '/reports',
  VERIFICATIONS: '/verifications',
};

/**
 * Supported user roles (must match backend enum).
 */
export const ROLES = {
  ADMIN:     'ADMIN',
  INSPECTOR: 'INSPECTOR',
  VIEWER:    'VIEWER',
};
