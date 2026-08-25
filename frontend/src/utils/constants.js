/**
 * Application-wide constants.
 * Keep business/compliance logic out — this is structural only.
 */

export const APP_NAME = 'ComplianceAI';

export const ROUTES = {
  HOME:               '/',
  LOGIN:              '/login',
  DASHBOARD:          '/dashboard',
  UPLOAD:             '/upload',
  EXTRACTION:         '/extraction',
  EXTRACTION_DETAIL:  '/extraction/:id',
  VERIFICATION:       '/verification',
  VERIFICATION_DETAIL:'/verification/:id',
  REPORTS:            '/reports',
  HISTORY:            '/history',
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

/**
 * Standard Packaging Declaration Field Keys (Legal Metrology & FSSAI)
 */
export const MANDATORY_DECLARATIONS = [
  { key: 'manufacturer_name', label: 'Manufacturer / Packer Name', rule: 'Rule 6(1)(a)' },
  { key: 'manufacturer_address', label: 'Manufacturer Address', rule: 'Rule 6(1)(a)' },
  { key: 'net_quantity', label: 'Net Quantity', rule: 'Rule 6(1)(c)' },
  { key: 'unit_sale_price', label: 'Unit Sale Price (USP)', rule: 'Rule 6(1)(s)' },
  { key: 'mrp', label: 'Maximum Retail Price (MRP)', rule: 'Rule 6(1)(e)' },
  { key: 'mfg_date', label: 'Date of Manufacture / Packing', rule: 'Rule 6(1)(d)' },
  { key: 'expiry_date', label: 'Expiry / Best Before Date', rule: 'Rule 6(1)(d)' },
  { key: 'batch_number', label: 'Batch / Lot Number', rule: 'Rule 6(1)(g)' },
  { key: 'country_of_origin', label: 'Country of Origin', rule: 'Rule 6(1)(n)' },
  { key: 'consumer_care', label: 'Consumer Care Contact / Helpline', rule: 'Rule 6(1)(f)' },
  { key: 'fssai_license', label: 'FSSAI License / Registration No.', rule: 'FSSAI Mandate' },
];
