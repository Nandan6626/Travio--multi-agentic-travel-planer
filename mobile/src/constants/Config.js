import Constants from 'expo-constants';
import { Platform } from 'react-native';

/**
 * Resolves the appropriate FastAPI backend base URL depending on runtime environment:
 * - Environment variable override (EXPO_PUBLIC_API_URL)
 * - Physical device running Expo Go: derives laptop LAN IP from hostUri
 * - Android Emulator: 10.0.2.2
 * - Web / iOS Simulator: localhost
 */
export function getBackendBaseUrl() {
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL;
  }

  // If running in browser (web), dynamically match the browser's current host
  if (Platform.OS === 'web' && typeof window !== 'undefined' && window.location?.hostname) {
    const hostname = window.location.hostname;
    return `http://${hostname}:8000`;
  }

  // If running in Expo Go on mobile device, derive laptop LAN IP from hostUri
  const debuggerHost = Constants.expoConfig?.hostUri || Constants.manifest?.debuggerHost;
  if (debuggerHost) {
    const ip = debuggerHost.split(':')[0];
    if (ip && ip !== 'localhost' && ip !== '127.0.0.1') {
      return `http://${ip}:8000`;
    }
  }

  // Android emulator fallback
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000';
  }

  return 'http://localhost:8000';
}

export const API_BASE_URL = getBackendBaseUrl();
export const API_V1_PREFIX = '/api/v1';
