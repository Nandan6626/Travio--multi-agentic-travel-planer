import { API_BASE_URL, API_V1_PREFIX } from '../constants/Config';
import { supabase } from './supabase';

const DEFAULT_TIMEOUT_MS = 8000;

let onUnauthorizedCallback = null;

export function setOnUnauthorizedHandler(callback) {
  onUnauthorizedCallback = callback;
}

/**
 * Robust fetch wrapper with timeout, auto Bearer JWT injection, and JSON parsing
 * @param {string} endpoint
 * @param {Object} [options]
 * @returns {Promise<any>}
 */
export async function apiFetch(endpoint, options = {}) {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, headers = {}, requiresAuth = false, ...rest } = options;
  const url = `${API_BASE_URL}${API_V1_PREFIX}${endpoint}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const requestHeaders = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...headers,
  };

  // Retrieve current Supabase access token if session exists
  try {
    const { data } = await supabase.auth.getSession();
    const token = data?.session?.access_token;
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    } else if (requiresAuth) {
      throw new Error('Authentication required. Please log in.');
    }
  } catch (err) {
    if (requiresAuth) throw err;
  }

  try {
    const response = await fetch(url, {
      ...rest,
      headers: requestHeaders,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.status === 401) {
      if (typeof onUnauthorizedCallback === 'function') {
        onUnauthorizedCallback();
      }
      throw new Error('Your session has expired. Please log in again.');
    }

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorJson = await response.json();
        if (errorJson?.detail) {
          errorMessage = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fallback
      }
      throw new Error(errorMessage);
    }

    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new Error(`Request timed out after ${timeoutMs}ms. Backend at ${API_BASE_URL} took too long to respond.`);
      }
      if (error.message.includes('Network request failed') || error.message.includes('Failed to fetch')) {
        throw new Error(
          `Cannot connect to backend at ${API_BASE_URL}. Ensure FastAPI is running on host 0.0.0.0 and your device is on the same network.`
        );
      }
      throw error;
    }
    throw new Error('An unexpected network error occurred');
  }
}

/**
 * Health check endpoint caller
 * @returns {Promise<{ data: any, latencyMs: number }>}
 */
export async function checkBackendHealth() {
  const startTime = Date.now();
  const data = await apiFetch('/health');
  const latencyMs = Date.now() - startTime;
  return { data, latencyMs };
}

/**
 * Format API error into user-readable string
 * @param {any} error
 * @returns {string}
 */
export function formatApiError(error) {
  if (error instanceof Error) {
    return error.message;
  }
  return 'Unknown error occurred while contacting backend';
}
