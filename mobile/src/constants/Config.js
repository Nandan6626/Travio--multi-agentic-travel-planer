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

  const debuggerHost = Constants.expoConfig?.hostUri;
  if (debuggerHost) {
    const ip = debuggerHost.split(':')[0];
    if (ip && ip !== 'localhost' && ip !== '127.0.0.1') {
      return `http://${ip}:8000`;
    }
  }

  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000';
  }

  return 'http://localhost:8000';
}

export const API_BASE_URL = getBackendBaseUrl();
export const API_V1_PREFIX = '/api/v1';
