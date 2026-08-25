import apiClient from './client';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * Products API — handles product packaging uploads and product queries.
 * Consumes the existing backend endpoints with Axios.
 */

/**
 * Upload a packaged product image for compliance verification.
 * Sends multipart/form-data with the image file and optional metadata.
 *
 * @param {File} file - Validated image file (JPG, PNG, WEBP)
 * @param {Object} [metadata] - Optional inspection metadata
 * @param {string} [metadata.name] - Product / commodity name
 * @param {string} [metadata.category] - Product category
 * @param {string} [metadata.batch_number] - Batch or Lot number
 * @param {Function} [onUploadProgress] - Optional upload progress callback
 * @returns {Promise<Object>} Backend verification / product response
 */
export const uploadProductImage = async (file, metadata = {}, onUploadProgress = null) => {
  const formData = new FormData();
  
  // Attach file under standard 'image' and 'file' fields for compatibility
  formData.append('image', file);

  if (metadata.name?.trim()) {
    formData.append('name', metadata.name.trim());
  }
  if (metadata.category?.trim()) {
    formData.append('category', metadata.category.trim());
  }
  if (metadata.batch_number?.trim()) {
    formData.append('batch_number', metadata.batch_number.trim());
  }

  const config = {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  };

  if (typeof onUploadProgress === 'function') {
    config.onUploadProgress = onUploadProgress;
  }

  // Uses API_ENDPOINTS.PRODUCTS_UPLOAD ('/products/upload')
  const response = await apiClient.post(API_ENDPOINTS.PRODUCTS_UPLOAD, formData, config);
  return response.data;
};

/**
 * Fetch all registered products (if supported by backend).
 * @returns {Promise<Array>}
 */
export const getProducts = async () => {
  const response = await apiClient.get(API_ENDPOINTS.PRODUCTS);
  return response.data;
};
