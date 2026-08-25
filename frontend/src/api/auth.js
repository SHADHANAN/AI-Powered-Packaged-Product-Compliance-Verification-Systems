import apiClient from './client';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * Auth API — thin wrappers around the backend /auth/* endpoints.
 * No business logic here; just HTTP calls.
 */

/**
 * POST /api/auth/login
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{access_token: string, token_type: string, ...}>}
 */
export const loginRequest = (email, password) =>
  apiClient.post(API_ENDPOINTS.AUTH.LOGIN, { email, password });

/**
 * GET /api/auth/me
 * Requires a valid JWT (attached automatically by the Axios interceptor).
 * @returns {Promise<{id, email, name, role, ...}>}
 */
export const getMeRequest = () =>
  apiClient.get(API_ENDPOINTS.AUTH.ME);
