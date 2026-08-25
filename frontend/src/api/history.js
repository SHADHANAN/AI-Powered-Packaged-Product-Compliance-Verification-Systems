import apiClient from './client';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * Verification History & Product Repository API Service
 * Handles queries for past product scans, audit records, and historical compliance verifications.
 */

/**
 * Fetch list of historical compliance verification inspection records.
 * @param {Object} [params] - Query parameters (e.g. { search, status, page, page_size })
 * @returns {Promise<Array|Object>} Historical verification records
 */
export const getVerificationHistory = async (params = {}) => {
  const endpoint = API_ENDPOINTS.VERIFICATIONS;
  const response = await apiClient.get(endpoint, { params });
  return response.data;
};

/**
 * Fetch a specific verification record by ID.
 * @param {string|number} id - Verification ID
 * @returns {Promise<Object>} Detailed verification inspection record
 */
export const getVerification = async (id) => {
  const endpoint = `${API_ENDPOINTS.VERIFICATIONS}/${id}`;
  const response = await apiClient.get(endpoint);
  return response.data;
};

/**
 * Retrieve all historical inspections for a specific product ID.
 * @param {string|number} productId - Product ID
 * @returns {Promise<Array>} List of verification records for the product
 */
export const getProductHistory = async (productId) => {
  const endpoint = `${API_ENDPOINTS.PRODUCTS}/${productId}/verifications`;
  const response = await apiClient.get(endpoint);
  return response.data;
};

/**
 * Search historical verification records by keyword (product name, batch, ID, inspector).
 * @param {string} query - Search string
 * @returns {Promise<Array>} Matching verification records
 */
export const searchVerifications = async (query) => {
  const endpoint = API_ENDPOINTS.VERIFICATIONS;
  const response = await apiClient.get(endpoint, { params: { search: query } });
  return response.data;
};
