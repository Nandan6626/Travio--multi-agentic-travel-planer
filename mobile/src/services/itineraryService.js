import { apiFetch } from './api';

export const itineraryService = {
  /**
   * List all days for a trip
   */
  async getDays(tripId) {
    return await apiFetch(`/trips/${tripId}/days`, { requiresAuth: true });
  },

  /**
   * Create an itinerary day
   */
  async createDay(tripId, dayData) {
    return await apiFetch(`/trips/${tripId}/days`, {
      method: 'POST',
      body: JSON.stringify(dayData),
      requiresAuth: true,
    });
  },

  /**
   * Retrieve an itinerary day with items
   */
  async getDay(dayId) {
    return await apiFetch(`/days/${dayId}`, { requiresAuth: true });
  },

  /**
   * Update an itinerary day
   */
  async updateDay(dayId, updateData) {
    return await apiFetch(`/days/${dayId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
      requiresAuth: true,
    });
  },

  /**
   * Delete an itinerary day
   */
  async deleteDay(dayId) {
    return await apiFetch(`/days/${dayId}`, {
      method: 'DELETE',
      requiresAuth: true,
    });
  },

  /**
   * List activities for an itinerary day
   */
  async getItems(dayId) {
    return await apiFetch(`/days/${dayId}/items`, { requiresAuth: true });
  },

  /**
   * Create an activity for an itinerary day
   */
  async createItem(dayId, itemData) {
    return await apiFetch(`/days/${dayId}/items`, {
      method: 'POST',
      body: JSON.stringify(itemData),
      requiresAuth: true,
    });
  },

  /**
   * Retrieve an activity
   */
  async getItem(itemId) {
    return await apiFetch(`/items/${itemId}`, { requiresAuth: true });
  },

  /**
   * Update an activity
   */
  async updateItem(itemId, updateData) {
    return await apiFetch(`/items/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
      requiresAuth: true,
    });
  },

  /**
   * Delete an activity
   */
  async deleteItem(itemId) {
    return await apiFetch(`/items/${itemId}`, {
      method: 'DELETE',
      requiresAuth: true,
    });
  },

  /**
   * Reorder activities for an itinerary day
   */
  async reorderItems(dayId, itemIds) {
    return await apiFetch(`/days/${dayId}/items/reorder`, {
      method: 'PATCH',
      body: JSON.stringify({ item_ids: itemIds }),
      requiresAuth: true,
    });
  },
};

