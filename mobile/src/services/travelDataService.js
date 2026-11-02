import { apiFetch } from './api';

export const travelDataService = {
  /**
   * Search real places and POIs via Geoapify through FastAPI backend
   */
  async searchPlaces({ text, categories, lat, lon, radiusMeters = 5000, limit = 20 } = {}) {
    const params = new URLSearchParams();
    if (text) params.append('text', text);
    if (categories) params.append('categories', categories);
    if (lat !== undefined && lat !== null) params.append('lat', lat.toString());
    if (lon !== undefined && lon !== null) params.append('lon', lon.toString());
    params.append('radius_meters', radiusMeters.toString());
    params.append('limit', limit.toString());

    return await apiFetch(`/places/search?${params.toString()}`, { requiresAuth: true });
  },

  /**
   * Get place details (cached DB place or Geoapify place_id)
   */
  async getPlaceDetails(placeId) {
    return await apiFetch(`/places/${placeId}`, { requiresAuth: true });
  },

  /**
   * Calculate routing distance, duration, and GeoJSON geometry via OSRM
   */
  async calculateRoute({ origin, destination, waypoints = [], profile = 'driving' }) {
    return await apiFetch('/routes/calculate', {
      method: 'POST',
      body: JSON.stringify({
        origin,
        destination,
        waypoints,
        profile,
      }),
      requiresAuth: true,
    });
  },

  /**
   * Get real-time and daily weather forecast via Open-Meteo
   */
  async getWeatherForecast({ lat, lon, days = 7 }) {
    const params = new URLSearchParams({
      lat: lat.toString(),
      lon: lon.toString(),
      days: days.toString(),
    });
    return await apiFetch(`/weather/forecast?${params.toString()}`, { requiresAuth: true });
  },

  /**
   * Search flight offers via Duffel Flights API
   */
  async searchFlights(searchParams) {
    return await apiFetch('/offers/flights/search', {
      method: 'POST',
      body: JSON.stringify(searchParams),
      requiresAuth: true,
    });
  },

  /**
   * Search accommodation and hotel offers via Duffel Stays API
   */
  async searchHotels(searchParams) {
    return await apiFetch('/offers/hotels/search', {
      method: 'POST',
      body: JSON.stringify(searchParams),
      requiresAuth: true,
    });
  },

  /**
   * Retrieve a stored travel offer by ID and verify its validity
   */
  async getOfferDetails(offerId) {
    return await apiFetch(`/offers/${offerId}`, { requiresAuth: true });
  },
};
