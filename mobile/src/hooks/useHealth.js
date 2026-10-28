import { useState, useEffect, useCallback } from 'react';
import { checkBackendHealth, formatApiError } from '../services/api';

/**
 * Hook to manage backend health diagnostics
 * @param {boolean} [autoPoll=false]
 * @param {number} [pollIntervalMs=10000]
 */
export function useHealth(autoPoll = false, pollIntervalMs = 10000) {
  const [state, setState] = useState({
    status: 'checking',
    data: null,
    error: null,
    latencyMs: null,
    lastChecked: null,
  });

  const check = useCallback(async () => {
    setState((prev) => ({ ...prev, status: 'checking', error: null }));
    try {
      const { data, latencyMs } = await checkBackendHealth();
      setState({
        status: 'connected',
        data,
        error: null,
        latencyMs,
        lastChecked: new Date(),
      });
    } catch (err) {
      setState({
        status: 'error',
        data: null,
        error: formatApiError(err),
        latencyMs: null,
        lastChecked: new Date(),
      });
    }
  }, []);

  useEffect(() => {
    check();

    if (!autoPoll) return;
    const interval = setInterval(check, pollIntervalMs);
    return () => clearInterval(interval);
  }, [check, autoPoll, pollIntervalMs]);

  return { ...state, refetch: check };
}
