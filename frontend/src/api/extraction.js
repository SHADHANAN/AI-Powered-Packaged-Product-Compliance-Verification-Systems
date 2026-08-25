import apiClient from './client';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * Extraction & OCR API Service
 * Handles fetching OCR raw text, structured field extractions, and field corrections.
 */

/**
 * Get extraction and OCR results for a specific product / inspection ID.
 * @param {string|number} id - Product or Verification ID
 * @returns {Promise<Object>} Extraction result containing fields and raw OCR text
 */
export const getExtractionResult = async (id) => {
  const endpoint = `${API_ENDPOINTS.EXTRACTION}/${id}`;
  const response = await apiClient.get(endpoint);
  return response.data;
};

/**
 * Trigger or re-run OCR extraction for a given product image.
 * @param {string|number} id - Product or Verification ID
 * @returns {Promise<Object>} Triggered extraction response
 */
export const extractProductFields = async (id) => {
  const endpoint = `${API_ENDPOINTS.EXTRACTION}/${id}/extract`;
  const response = await apiClient.post(endpoint);
  return response.data;
};

/**
 * Update / correct extracted declaration fields before compliance validation.
 * @param {string|number} id - Product or Extraction ID
 * @param {Object} updatedFields - Map of field keys to corrected values
 * @returns {Promise<Object>} Updated extraction state
 */
export const updateExtractedFields = async (id, updatedFields) => {
  const endpoint = `${API_ENDPOINTS.EXTRACTION}/${id}/fields`;
  const response = await apiClient.put(endpoint, { fields: updatedFields });
  return response.data;
};
