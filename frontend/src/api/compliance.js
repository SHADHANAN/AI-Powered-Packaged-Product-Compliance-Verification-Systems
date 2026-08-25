import apiClient from './client';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * Compliance & Verification API Service
 * Handles fetching compliance evaluations, triggering verification engine checks,
 * and querying regulatory rulesets.
 */

/**
 * Fetch compliance verification results for a product or inspection ID.
 * @param {string|number} id - Product or Verification ID
 * @returns {Promise<Object>} Verification evaluation summary and rule-by-rule results
 */
export const getVerificationResult = async (id) => {
  // Uses /verifications/:id endpoint
  const endpoint = `${API_ENDPOINTS.VERIFICATIONS}/${id}`;
  const response = await apiClient.get(endpoint);
  return response.data;
};

/**
 * Execute automated compliance rule verification for a given product.
 * Evaluates extracted declarations against Legal Metrology & FSSAI rulesets.
 * @param {string|number} id - Product ID
 * @returns {Promise<Object>} Evaluated compliance report
 */
export const verifyProductCompliance = async (id) => {
  // Uses /compliance/verify/:id or /verifications/:id/verify
  const endpoint = `${API_ENDPOINTS.COMPLIANCE}/verify/${id}`;
  const response = await apiClient.post(endpoint);
  return response.data;
};

/**
 * Retrieve the active regulatory compliance rules and standards catalog.
 * @returns {Promise<Array>} List of compliance rule definitions
 */
export const getComplianceRules = async () => {
  const endpoint = `${API_ENDPOINTS.COMPLIANCE}/rules`;
  const response = await apiClient.get(endpoint);
  return response.data;
};
