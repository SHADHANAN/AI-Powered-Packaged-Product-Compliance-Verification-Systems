/**
 * Shared TypeScript-style type definitions (JSDoc).
 * These serve as documentation for data shapes used across the frontend.
 */

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} email
 * @property {string} name
 * @property {string} role - 'ADMIN' | 'INSPECTOR' | 'VIEWER'
 * @property {boolean} authenticated
 */

/**
 * @typedef {Object} Product
 * @property {number|string} id
 * @property {string} name
 * @property {string} [barcode]
 * @property {string} [category]
 * @property {string} [image_url]
 * @property {string} [batch_number]
 * @property {string} [created_at]
 */

/**
 * @typedef {'high'|'medium'|'low'|'unverified'} ConfidenceLevel
 */

/**
 * @typedef {Object} ExtractedField
 * @property {string} key - Machine identifier (e.g. 'mrp', 'net_quantity', 'manufacturer')
 * @property {string} label - Human-readable label (e.g. 'Maximum Retail Price')
 * @property {string|number|null} value - Extracted text value
 * @property {string|number|null} [original_value] - Initial AI detected value before manual edit
 * @property {number} [confidence] - Numeric score (0.0 - 1.0)
 * @property {ConfidenceLevel} [confidence_level] - 'high' | 'medium' | 'low'
 * @property {string} [rule_reference] - Legal Metrology / FSSAI rule reference
 * @property {boolean} [is_edited] - Whether inspector manually altered value
 * @property {string} [status] - 'detected' | 'not_detected' | 'edited' | 'pending'
 */

/**
 * @typedef {Object} ExtractionResult
 * @property {number|string} id
 * @property {number|string} product_id
 * @property {string} [product_name]
 * @property {string} [image_url]
 * @property {string} [category]
 * @property {'pending'|'processing'|'completed'|'failed'} status
 * @property {string} [raw_ocr_text]
 * @property {Array<ExtractedField>|Object<string, ExtractedField>} fields
 * @property {string} [created_at]
 * @property {string} [updated_at]
 */

/**
 * @typedef {'COMPLIANT'|'NON_COMPLIANT'|'WARNING'|'PENDING'|'FAILED'|'compliant'|'non_compliant'|'pending'|'error'} ComplianceStatus
 */

/**
 * @typedef {'HIGH'|'MEDIUM'|'LOW'|'INFO'} RuleSeverity
 */

/**
 * @typedef {'PASS'|'FAIL'|'WARNING'|'NOT_APPLICABLE'} RuleStatus
 */

/**
 * @typedef {Object} RuleResult
 * @property {string} [id] - Rule unique identifier (e.g. 'RULE-6-1-E')
 * @property {string} rule_name - Human-readable rule title
 * @property {string} [rule_identifier] - Legal section reference
 * @property {RuleStatus} status - 'PASS' | 'FAIL' | 'WARNING'
 * @property {string} [detected_value] - Text extracted from packaging
 * @property {string} [expected_requirement] - Regulatory mandate text
 * @property {string} [violation_message] - Reason for failure if non-compliant
 * @property {RuleSeverity} [severity] - 'HIGH' | 'MEDIUM' | 'LOW'
 * @property {string} [evidence] - Raw OCR or bounding box evidence
 * @property {string} [recommendation] - Corrective guidance for packaging
 */

/**
 * @typedef {Object} VerificationResult
 * @property {number|string} id
 * @property {number|string} product_id
 * @property {string} [product_name]
 * @property {string} [category]
 * @property {string} [image_url]
 * @property {ComplianceStatus} status
 * @property {number|null} [score] - Score percentage (0-100)
 * @property {number} [total_rules_checked]
 * @property {number} [passed_rules]
 * @property {number} [failed_rules]
 * @property {number} [warning_rules]
 * @property {Array<RuleResult>} [rules]
 * @property {Array<RuleResult>} [violations]
 * @property {string} [created_at]
 */

/**
 * @typedef {Object} ApiError
 * @property {string} detail
 * @property {number} status_code
 */

export {};
