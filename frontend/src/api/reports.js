import apiClient from './client';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * Compliance Reports API Service
 * Handles report queries, report generation requests, and authenticated binary downloads (PDF / Excel).
 */

/**
 * Fetch list of generated compliance audit reports.
 * @returns {Promise<Array>} List of compliance reports
 */
export const getReports = async () => {
  const endpoint = API_ENDPOINTS.REPORTS;
  const response = await apiClient.get(endpoint);
  return response.data;
};

/**
 * Fetch detailed report metadata and findings for a specific report ID.
 * @param {string|number} id - Report ID
 * @returns {Promise<Object>} Detailed report payload
 */
export const getReport = async (id) => {
  const endpoint = `${API_ENDPOINTS.REPORTS}/${id}`;
  const response = await apiClient.get(endpoint);
  return response.data;
};

/**
 * Request generation of a new compliance audit report from an existing verification result.
 * @param {Object} data - Generation payload ({ verification_id, format, include_evidence })
 * @returns {Promise<Object>} Created report record
 */
export const generateReport = async (data) => {
  const endpoint = `${API_ENDPOINTS.REPORTS}/generate`;
  const response = await apiClient.post(endpoint, data);
  return response.data;
};

/**
 * Download an authenticated compliance report in binary format (PDF / Excel / CSV).
 * Manages blob streaming, filename assignment, and object URL revocation safely.
 * @param {string|number} id - Report or Verification ID
 * @param {'pdf'|'excel'|'csv'} [format='pdf'] - Desired file format
 * @param {string} [customFilename] - Optional override for the downloaded file name
 * @returns {Promise<void>}
 */
export const downloadReport = async (id, format = 'pdf', customFilename) => {
  const endpoint = `${API_ENDPOINTS.REPORTS}/${id}/download`;
  
  const response = await apiClient.get(endpoint, {
    params: { format: format.toLowerCase() },
    responseType: 'blob',
  });

  const mimeMap = {
    pdf: 'application/pdf',
    excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    csv: 'text/csv',
  };

  const extensionMap = {
    pdf: 'pdf',
    excel: 'xlsx',
    csv: 'csv',
  };

  const contentType = mimeMap[format.toLowerCase()] || response.headers['content-type'] || 'application/octet-stream';
  const blob = new Blob([response.data], { type: contentType });
  const downloadUrl = window.URL.createObjectURL(blob);

  // Generate safe filename
  const filename =
    customFilename ||
    `compliance_audit_report_${id}_${new Date().toISOString().split('T')[0]}.${extensionMap[format.toLowerCase()] || format}`;

  // Trigger browser download via invisible link
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();

  // Cleanup
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
};
