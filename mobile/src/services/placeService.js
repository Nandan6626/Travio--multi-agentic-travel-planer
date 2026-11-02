import { apiFetch } from './api';

export const placeService = {
  /**
   * Create a place with coordinates
   */
  async createPlace(placeData) {
    return await apiFetch('/places', {
      method: 'POST',
      body: JSON.stringify(placeData),
      requiresAuth: true,
    });
  },

  /**
   * Retrieve a place by ID
   */
  async getPlace(placeId) {
    return await apiFetch(`/places/${placeId}`, { requiresAuth: true });
  },
};

