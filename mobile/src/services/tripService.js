import { apiFetch } from './api';

export const tripService = {
  /**
   * Get authenticated user profile
   */
  async getMyProfile() {
    return await apiFetch('/profiles/me', { requiresAuth: true });
  },

  /**
   * Synchronize profile information
   */
  async syncMyProfile(profileData) {
    return await apiFetch('/profiles/me', {
      method: 'POST',
      body: JSON.stringify(profileData),
      requiresAuth: true,
    });
  },

  /**
   * List all accessible trips for authenticated user
   */
  async getTrips() {
    return await apiFetch('/trips', { requiresAuth: true });
  },

  /**
   * Get specific trip details (enforcing membership)
   */
  async getTrip(tripId) {
    return await apiFetch(`/trips/${tripId}`, { requiresAuth: true });
  },

  /**
   * Create a new trip (sets owner and OWNER member)
   */
  async createTrip(tripData) {
    return await apiFetch('/trips', {
      method: 'POST',
      body: JSON.stringify(tripData),
      requiresAuth: true,
    });
  },

  /**
   * Update trip details (requires EDITOR or OWNER role)
   */
  async updateTrip(tripId, updateData) {
    return await apiFetch(`/trips/${tripId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
      requiresAuth: true,
    });
  },

  /**
   * Delete a trip (strictly requires OWNER role)
   */
  async deleteTrip(tripId) {
    return await apiFetch(`/trips/${tripId}`, {
      method: 'DELETE',
      requiresAuth: true,
    });
  },
};
