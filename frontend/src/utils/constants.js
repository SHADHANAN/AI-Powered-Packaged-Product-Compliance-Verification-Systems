/**
 * Application-wide constants.
 * Keep business/compliance logic out — this is structural only.
 */

export const APP_NAME = 'ComplianceAI';

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DASHBOARD: '/',
  UPLOAD: '/upload',
  VERIFICATION: '/verification',
  REPORTS: '/reports',
  HISTORY: '/history',
};

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    ME: '/auth/me',
  },
  PRODUCTS: '/products',
  COMPLIANCE: '/compliance',
  EXTRACTION: '/extraction',
  OCR: '/ocr',
  REPORTS: '/reports',
  VERIFICATIONS: '/verifications',
};
