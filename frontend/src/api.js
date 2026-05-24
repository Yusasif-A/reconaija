/**
 * API Client for RecoNaija Backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Get list of demo users
 */
export const getDemoUsers = async () => {
  const response = await api.get('/demo-users');
  return response.data;
};

/**
 * Generate a review (Task A)
 * @param {Object} data - { user_id, persona_text, product_name, product_category }
 */
export const generateReview = async (data) => {
  const response = await api.post('/generate-review', data);
  return response.data;
};

/**
 * Get recommendations (Task B)
 * @param {Object} data - { user_id, persona_text, top_k }
 */
export const getRecommendations = async (data) => {
  const response = await api.post('/recommend', data);
  return response.data;
};

/**
 * Health check
 */
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
