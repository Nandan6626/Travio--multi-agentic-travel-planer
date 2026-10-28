import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../hooks/useAuth';
import { tripService } from '../services/tripService';

export function TripsManager() {
  const router = useRouter();
  const { user, profile, signOut, isConfigured } = useAuth();
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creating, setCreating] = useState(false);

  // Form inputs
  const [title, setTitle] = useState('');
  const [destination, setDestination] = useState('');
  const [startDate, setStartDate] = useState('2026-11-01');
  const [endDate, setEndDate] = useState('2026-11-08');
  const [budget, setBudget] = useState('2500.00');
  const [currency, setCurrency] = useState('USD');
  const [travelers, setTravelers] = useState('2');

  const fetchTrips = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError('');
    try {
      const data = await tripService.getTrips();
      setTrips(data.trips || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch trips');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchTrips();
  }, [fetchTrips]);

  const handleCreateTrip = async () => {
    if (!title.trim() || !destination.trim() || !startDate || !endDate) {
      Alert.alert('Required Fields', 'Please complete title, destination, and dates.');
      return;
    }
    if (new Date(endDate) < new Date(startDate)) {
      Alert.alert('Invalid Dates', 'End date cannot be earlier than start date.');
      return;
    }
    const numBudget = parseFloat(budget) || 0;
    if (numBudget < 0) {
      Alert.alert('Invalid Budget', 'Budget cannot be negative.');
      return;
    }
    const numTravelers = parseInt(travelers, 10) || 1;
    if (numTravelers < 1) {
      Alert.alert('Invalid Travelers', 'Travelers must be at least 1.');
      return;
    }

    setCreating(true);
    try {
      await tripService.createTrip({
        title: title.trim(),
        destination: destination.trim(),
        start_date: startDate,
        end_date: endDate,
        total_budget: numBudget.toFixed(2),
        currency: currency.toUpperCase().trim(),
        traveler_count: numTravelers,
      });

      // Reset and refresh
      setTitle('');
      setDestination('');
      setShowCreateForm(false);
      await fetchTrips();
      Alert.alert('Success', 'Trip created successfully as OWNER!');
    } catch (err) {
      Alert.alert('Trip Creation Error', err.message || 'Failed to create trip');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteTrip = async (tripId, tripTitle) => {
    Alert.alert(
      'Delete Trip',
      `Are you sure you want to delete "${tripTitle}"? This cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await tripService.deleteTrip(tripId);
              await fetchTrips();
            } catch (err) {
              Alert.alert('Delete Error', err.message);
            }
          },
        },
      ]
    );
  };

  if (!user) {
    return (
      <View style={styles.card}>
        <View style={styles.authPromptHeader}>
          <Text style={styles.authPromptIcon}>🔐</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.authPromptTitle}>Authenticated Trip Management</Text>
            <Text style={styles.authPromptSubtitle}>
              Sign in with Supabase Auth to create and manage trips with role-based permissions.
            </Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.signInButton}
          onPress={() => router.push('/(auth)/login')}
          activeOpacity={0.8}>
          <Text style={styles.signInButtonText}>Sign In / Register</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* User Session Bar */}
      <View style={styles.userBar}>
        <View style={styles.userInfo}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {(profile?.full_name || user?.email || 'U')[0].toUpperCase()}
            </Text>
          </View>
          <View>
            <Text style={styles.userName}>{profile?.full_name || 'Travio Traveler'}</Text>
            <Text style={styles.userEmail}>{user?.email}</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.signOutButton} onPress={signOut}>
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>
      </View>

      {/* Header and Add Button */}
      <View style={styles.listHeaderRow}>
        <View>
          <Text style={styles.sectionTitle}>My Trips ({trips.length})</Text>
          <Text style={styles.sectionSubtitle}>OWNER, EDITOR &amp; VIEWER Protected</Text>
        </View>
        <TouchableOpacity
          style={styles.addTripButton}
          onPress={() => setShowCreateForm(!showCreateForm)}
          activeOpacity={0.8}>
          <Text style={styles.addTripButtonText}>{showCreateForm ? '✕ Close' : '+ New Trip'}</Text>
        </TouchableOpacity>
      </View>

      {/* Create Trip Form Drawer */}
      {showCreateForm && (
        <View style={styles.createCard}>
          <Text style={styles.formHeading}>Plan a New Trip</Text>

          <View style={styles.formRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.formLabel}>Trip Title</Text>
              <TextInput
                style={styles.formInput}
                placeholder="e.g. Japanese Alps Hiking"
                placeholderTextColor="#64748B"
                value={title}
                onChangeText={setTitle}
              />
            </View>
          </View>

          <View style={styles.formRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.formLabel}>Destination</Text>
              <TextInput
                style={styles.formInput}
                placeholder="e.g. Nagano, Japan"
                placeholderTextColor="#64748B"
                value={destination}
                onChangeText={setDestination}
              />
            </View>
          </View>

          <View style={styles.twoColRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.formLabel}>Start Date (YYYY-MM-DD)</Text>
              <TextInput
                style={styles.formInput}
                placeholder="2026-11-01"
                placeholderTextColor="#64748B"
                value={startDate}
                onChangeText={setStartDate}
              />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.formLabel}>End Date (YYYY-MM-DD)</Text>
              <TextInput
                style={styles.formInput}
                placeholder="2026-11-08"
                placeholderTextColor="#64748B"
                value={endDate}
                onChangeText={setEndDate}
              />
            </View>
          </View>

          <View style={styles.twoColRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.formLabel}>Budget Limit</Text>
              <TextInput
                style={styles.formInput}
                placeholder="2500.00"
                placeholderTextColor="#64748B"
                keyboardType="numeric"
                value={budget}
                onChangeText={setBudget}
              />
            </View>
            <View style={{ width: 80 }}>
              <Text style={styles.formLabel}>Currency</Text>
              <TextInput
                style={styles.formInput}
                placeholder="USD"
                placeholderTextColor="#64748B"
                value={currency}
                onChangeText={setCurrency}
                maxLength={3}
                autoCapitalize="characters"
              />
            </View>
            <View style={{ width: 80 }}>
              <Text style={styles.formLabel}>Travelers</Text>
              <TextInput
                style={styles.formInput}
                placeholder="2"
                placeholderTextColor="#64748B"
                keyboardType="numeric"
                value={travelers}
                onChangeText={setTravelers}
              />
            </View>
          </View>

          <TouchableOpacity
            style={[styles.submitTripButton, creating && styles.buttonDisabled]}
            onPress={handleCreateTrip}
            disabled={creating}
            activeOpacity={0.8}>
            {creating ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={styles.submitTripButtonText}>Save Trip (as OWNER)</Text>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* Trips List */}
      {loading ? (
        <View style={styles.centerBox}>
          <ActivityIndicator color="#38BDF8" size="large" />
          <Text style={styles.loadingText}>Loading trips from database...</Text>
        </View>
      ) : error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchTrips}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : trips.length === 0 ? (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyIcon}>🗺️</Text>
          <Text style={styles.emptyTitle}>No Trips Found</Text>
          <Text style={styles.emptySubtitle}>
            Create your first trip above to test atomic PostgreSQL persistence and owner permissions!
          </Text>
        </View>
      ) : (
        <View style={styles.tripList}>
          {trips.map((trip) => {
            const isOwner = trip.user_role === 'OWNER';
            const roleBadgeBg = isOwner ? '#064E3B' : trip.user_role === 'EDITOR' ? '#1E3A8A' : '#334155';
            const roleColor = isOwner ? '#34D399' : trip.user_role === 'EDITOR' ? '#93C5FD' : '#94A3B8';

            return (
              <View key={trip.id} style={styles.tripCard}>
                <View style={styles.tripCardHeader}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.tripDestination}>{trip.destination}</Text>
                    <Text style={styles.tripTitle}>{trip.title}</Text>
                  </View>
                  <View style={[styles.roleBadge, { backgroundColor: roleBadgeBg }]}>
                    <Text style={[styles.roleBadgeText, { color: roleColor }]}>{trip.user_role}</Text>
                  </View>
                </View>

                <View style={styles.tripDetailsGrid}>
                  <View style={styles.detailItem}>
                    <Text style={styles.detailLabel}>Dates</Text>
                    <Text style={styles.detailValue}>
                      {trip.start_date} → {trip.end_date}
                    </Text>
                  </View>
                  <View style={styles.detailItem}>
                    <Text style={styles.detailLabel}>Budget</Text>
                    <Text style={[styles.detailValue, { color: '#10B981' }]}>
                      {trip.currency} {parseFloat(trip.total_budget).toLocaleString()}
                    </Text>
                  </View>
                  <View style={styles.detailItem}>
                    <Text style={styles.detailLabel}>Travelers</Text>
                    <Text style={styles.detailValue}>{trip.traveler_count} people</Text>
                  </View>
                </View>

                {isOwner && (
                  <View style={styles.tripActions}>
                    <TouchableOpacity
                      style={styles.deleteButton}
                      onPress={() => handleDeleteTrip(trip.id, trip.title)}>
                      <Text style={styles.deleteButtonText}>Delete Trip</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            );
          })}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    gap: 14,
  },
  card: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 12,
  },
  authPromptHeader: {
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
  },
  authPromptIcon: {
    fontSize: 28,
  },
  authPromptTitle: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: '700',
  },
  authPromptSubtitle: {
    color: '#94A3B8',
    fontSize: 12,
    lineHeight: 16,
  },
  signInButton: {
    backgroundColor: '#2563EB',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  signInButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  userBar: {
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  avatar: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: '#2563EB',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 16,
  },
  userName: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '700',
  },
  userEmail: {
    color: '#94A3B8',
    fontSize: 11,
  },
  signOutButton: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    backgroundColor: '#334155',
  },
  signOutText: {
    color: '#CBD5E1',
    fontSize: 12,
    fontWeight: '600',
  },
  listHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  sectionTitle: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '800',
  },
  sectionSubtitle: {
    color: '#64748B',
    fontSize: 11,
  },
  addTripButton: {
    backgroundColor: '#059669',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  addTripButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 12,
  },
  createCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#059669',
    gap: 12,
  },
  formHeading: {
    color: '#34D399',
    fontSize: 14,
    fontWeight: '700',
  },
  formRow: {
    gap: 4,
  },
  twoColRow: {
    flexDirection: 'row',
    gap: 8,
  },
  formLabel: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 4,
  },
  formInput: {
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    color: '#F8FAFC',
    fontSize: 13,
  },
  submitTripButton: {
    backgroundColor: '#059669',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 6,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  submitTripButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  centerBox: {
    padding: 24,
    alignItems: 'center',
    gap: 8,
  },
  loadingText: {
    color: '#94A3B8',
    fontSize: 12,
  },
  errorBox: {
    backgroundColor: '#450A0A',
    borderRadius: 12,
    padding: 12,
    gap: 8,
  },
  errorText: {
    color: '#FCA5A5',
    fontSize: 12,
  },
  retryButton: {
    backgroundColor: '#7F1D1D',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  retryText: {
    color: '#FECACA',
    fontSize: 11,
    fontWeight: '700',
  },
  emptyCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
    gap: 6,
  },
  emptyIcon: {
    fontSize: 32,
    marginBottom: 4,
  },
  emptyTitle: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: '700',
  },
  emptySubtitle: {
    color: '#94A3B8',
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 16,
  },
  tripList: {
    gap: 12,
  },
  tripCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 12,
  },
  tripCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 8,
  },
  tripDestination: {
    color: '#38BDF8',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  tripTitle: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '800',
  },
  roleBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  roleBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  tripDetailsGrid: {
    flexDirection: 'row',
    backgroundColor: '#0F172A',
    borderRadius: 10,
    padding: 10,
    gap: 8,
  },
  detailItem: {
    flex: 1,
  },
  detailLabel: {
    color: '#64748B',
    fontSize: 10,
    fontWeight: '600',
    marginBottom: 2,
  },
  detailValue: {
    color: '#F1F5F9',
    fontSize: 11,
    fontWeight: '700',
  },
  tripActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    borderTopWidth: 1,
    borderTopColor: '#334155',
    paddingTop: 8,
  },
  deleteButton: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 6,
    backgroundColor: '#450A0A',
  },
  deleteButtonText: {
    color: '#FCA5A5',
    fontSize: 11,
    fontWeight: '700',
  },
});
