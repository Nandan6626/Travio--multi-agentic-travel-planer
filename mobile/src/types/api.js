/**
 * @typedef {Object} HealthResponse
 * @property {string} status
 * @property {string} environment
 * @property {string} version
 * @property {string} timestamp
 * @property {Object.<string, string>} services
 */

/**
 * @typedef {'checking' | 'connected' | 'error'} HealthStatus
 */

/**
 * @typedef {Object} HealthCheckState
 * @property {HealthStatus} status
 * @property {HealthResponse|null} data
 * @property {string|null} error
 * @property {number|null} latencyMs
 * @property {Date|null} lastChecked
 */

export const INITIAL_HEALTH_STATE = {
  status: 'checking',
  data: null,
  error: null,
  latencyMs: null,
  lastChecked: null,
};
