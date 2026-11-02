import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { tripService } from '../services/tripService';
import { itineraryService } from '../services/itineraryService';

export default function TripDetailsScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();

  const [trip, setTrip] = useState(null);
  const [days, setDays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Add Day Form
  const [showAddDay, setShowAddDay] = useState(false);
  const [dayNumber, setDayNumber] = useState('1');
  const [dayDate, setDayDate] = useState('');
  const [dayTitle, setDayTitle] = useState('');
  const [dayNotes, setDayNotes] = useState('');
  const [submittingDay, setSubmittingDay] = useState(false);

  const fetchTripAndDays = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError('');
    try {
      const [tripData, daysData] = await Promise.all([
        tripService.getTrip(id),
        itineraryService.getDays(id),
      ]);
      setTrip(tripData);
      setDays(daysData || []);

      // Auto compute next day defaults
      const nextNum = (daysData?.length || 0) + 1;
      setDayNumber(String(nextNum));
      if (tripData?.start_date) {
        setDayDate(tripData.start_date);
      }
    } catch (err) {
      setError(err.message || 'Failed to load trip itinerary.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchTripAndDays();
  }, [fetchTripAndDays]);

  const canEdit = trip?.user_role === 'OWNER' || trip?.user_role === 'EDITOR';

  const handleCreateDay = async () => {
    if (!dayTitle.trim() || !dayDate.trim()) {
      Alert.alert('Required Fields', 'Please enter a day date and title.');
      return;
    }
    const num = parseInt(dayNumber, 10);
    if (!num || num < 1) {
      Alert.alert('Invalid Day Number', 'Day number must be at least 1.');
      return;
    }
    if (dayDate < trip.start_date || dayDate > trip.end_date) {
      Alert.alert(
        'Date Out of Range',
        `Day date (${dayDate}) must be between trip start (${trip.start_date}) and end (${trip.end_date}).`
      );
      return;
    }

    setSubmittingDay(true);
    try {
      await itineraryService.createDay(id, {
        day_number: num,
        date: dayDate,
        title: dayTitle.trim(),
        notes: dayNotes.trim() || null,
      });

      setDayTitle('');
      setDayNotes('');
      setShowAddDay(false);
      await fetchTripAndDays();
      Alert.alert('Success', `Day ${num} added to itinerary!`);
    } catch (err) {
      Alert.alert('Create Day Error', err.message);
    } finally {
      setSubmittingDay(false);
    }
  };

  const handleDeleteDay = async (dayId, dNum) => {
    Alert.alert(
      'Delete Day',
      `Delete Day ${dNum} and all its scheduled activities? This cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await itineraryService.deleteDay(dayId);
              await fetchTripAndDays();
            } catch (err) {
              Alert.alert('Delete Error', err.message);
            }
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Header */}
      <View style={styles.topBar}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.topBarTitle}>Itinerary Plan</Text>
        <View style={{ width: 60 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {loading ? (
          <View style={styles.centerBox}>
            <ActivityIndicator color="#38BDF8" size="large" />
            <Text style={styles.loadingText}>Loading trip itinerary...</Text>
          </View>
        ) : error ? (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={fetchTripAndDays}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : trip ? (
          <>
            {/* Trip Hero Banner */}
            <View style={styles.heroCard}>
              <View style={styles.heroHeader}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.heroDestination}>📍 {trip.destination}</Text>
                  <Text style={styles.heroTitle}>{trip.title}</Text>
                </View>
                <View
                  style={[
                    styles.roleBadge,
                    {
                      backgroundColor:
                        trip.user_role === 'OWNER'
                          ? '#064E3B'
                          : trip.user_role === 'EDITOR'
                          ? '#1E3A8A'
                          : '#334155',
                    },
                  ]}>
                  <Text
                    style={[
                      styles.roleBadgeText,
                      {
                        color:
                          trip.user_role === 'OWNER'
                            ? '#34D399'
                            : trip.user_role === 'EDITOR'
                            ? '#93C5FD'
                            : '#94A3B8',
                      },
                    ]}>
                    {trip.user_role}
                  </Text>
                </View>
              </View>

              <View style={styles.statsRow}>
                <View style={styles.statItem}>
                  <Text style={styles.statLabel}>Dates</Text>
                  <Text style={styles.statValue}>
                    {trip.start_date} → {trip.end_date}
                  </Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statLabel}>Budget</Text>
                  <Text style={[styles.statValue, { color: '#10B981' }]}>
                    {trip.currency} {parseFloat(trip.total_budget).toLocaleString()}
                  </Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={styles.statLabel}>Travelers</Text>
                  <Text style={styles.statValue}>{trip.traveler_count} people</Text>
                </View>
              </View>
            </View>

            {/* Days Section Header */}
            <View style={styles.sectionHeaderRow}>
              <View>
                <Text style={styles.sectionTitle}>Itinerary Days ({days.length})</Text>
                <Text style={styles.sectionSubtitle}>Organize daily sightseeing &amp; activities</Text>
              </View>
              {canEdit && (
                <TouchableOpacity
                  style={styles.addDayButton}
                  onPress={() => setShowAddDay(!showAddDay)}
                  activeOpacity={0.8}>
                  <Text style={styles.addDayButtonText}>{showAddDay ? '✕ Close' : '+ Add Day'}</Text>
                </TouchableOpacity>
              )}
            </View>

            {/* Add Day Drawer */}
            {showAddDay && (
              <View style={styles.addDayForm}>
                <Text style={styles.formHeading}>Add New Itinerary Day</Text>

                <View style={styles.twoColRow}>
                  <View style={{ width: 100 }}>
                    <Text style={styles.formLabel}>Day #</Text>
                    <TextInput
                      style={styles.input}
                      keyboardType="numeric"
                      value={dayNumber}
                      onChangeText={setDayNumber}
                    />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.formLabel}>Date (YYYY-MM-DD)</Text>
                    <TextInput
                      style={styles.input}
                      placeholder={trip.start_date}
                      placeholderTextColor="#64748B"
                      value={dayDate}
                      onChangeText={setDayDate}
                    />
                  </View>
                </View>

                <View style={styles.formRow}>
                  <Text style={styles.formLabel}>Title / Theme</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="e.g. Historic Castles &amp; Gardens"
                    placeholderTextColor="#64748B"
                    value={dayTitle}
                    onChangeText={setDayTitle}
                  />
                </View>

                <View style={styles.formRow}>
                  <Text style={styles.formLabel}>Day Notes (Optional)</Text>
                  <TextInput
                    style={[styles.input, styles.textArea]}
                    placeholder="e.g. Wear comfortable walking shoes"
                    placeholderTextColor="#64748B"
                    multiline
                    numberOfLines={2}
                    value={dayNotes}
                    onChangeText={setDayNotes}
                  />
                </View>

                <TouchableOpacity
                  style={[styles.saveDayButton, submittingDay && styles.buttonDisabled]}
                  onPress={handleCreateDay}
                  disabled={submittingDay}
                  activeOpacity={0.8}>
                  {submittingDay ? (
                    <ActivityIndicator color="#FFFFFF" size="small" />
                  ) : (
                    <Text style={styles.saveDayButtonText}>Save Day</Text>
                  )}
                </TouchableOpacity>
              </View>
            )}

            {/* List of Days */}
            {days.length === 0 ? (
              <View style={styles.emptyCard}>
                <Text style={styles.emptyIcon}>📅</Text>
                <Text style={styles.emptyTitle}>No Days Scheduled Yet</Text>
                <Text style={styles.emptySubtitle}>
                  Tap "+ Add Day" above to start building your chronological travel itinerary.
                </Text>
              </View>
            ) : (
              <View style={styles.daysList}>
                {days.map((d) => (
                  <TouchableOpacity
                    key={d.id}
                    style={styles.dayCard}
                    activeOpacity={0.85}
                    onPress={() =>
                      router.push({
                        pathname: '/day-details',
                        params: {
                          dayId: d.id,
                          tripId: trip.id,
                          role: trip.user_role,
                          dayNumber: d.day_number,
                          title: d.title,
                          date: d.date,
                        },
                      })
                    }>
                    <View style={styles.dayCardHeader}>
                      <View style={styles.dayNumberBadge}>
                        <Text style={styles.dayNumberText}>Day {d.day_number}</Text>
                      </View>
                      <Text style={styles.dayDateText}>{d.date}</Text>
                      <View style={{ flex: 1 }} />
                      {canEdit && (
                        <TouchableOpacity
                          style={styles.deleteDayButton}
                          onPress={() => handleDeleteDay(d.id, d.day_number)}>
                          <Text style={styles.deleteDayText}>✕</Text>
                        </TouchableOpacity>
                      )}
                    </View>

                    <Text style={styles.dayTitleText}>{d.title}</Text>
                    {d.notes ? <Text style={styles.dayNotesText}>{d.notes}</Text> : null}

                    <View style={styles.dayFooter}>
                      <Text style={styles.activityCount}>
                        🎯 {d.items?.length || 0} activities scheduled
                      </Text>
                      <Text style={styles.openDayText}>View Itinerary →</Text>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
    backgroundColor: '#0B1120',
  },
  backButton: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: '#1E293B',
  },
  backButtonText: {
    color: '#38BDF8',
    fontWeight: '700',
    fontSize: 14,
  },
  topBarTitle: {
    color: '#F8FAFC',
    fontWeight: '700',
    fontSize: 16,
  },
  scrollContent: {
    padding: 16,
    gap: 16,
  },
  centerBox: {
    padding: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    color: '#94A3B8',
    fontSize: 14,
  },
  errorBox: {
    backgroundColor: '#450A0A',
    borderColor: '#7F1D1D',
    borderWidth: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    gap: 10,
  },
  errorText: {
    color: '#FCA5A5',
    textAlign: 'center',
    fontSize: 14,
  },
  retryButton: {
    backgroundColor: '#EF4444',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  retryText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  heroCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 12,
  },
  heroHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 10,
  },
  heroDestination: {
    color: '#38BDF8',
    fontWeight: '700',
    fontSize: 13,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  heroTitle: {
    color: '#F8FAFC',
    fontSize: 20,
    fontWeight: '800',
  },
  roleBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  roleBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: '#0F172A',
    borderRadius: 12,
    padding: 12,
    justifyContent: 'space-between',
  },
  statItem: {
    gap: 4,
  },
  statLabel: {
    color: '#64748B',
    fontSize: 11,
    fontWeight: '600',
  },
  statValue: {
    color: '#F1F5F9',
    fontSize: 13,
    fontWeight: '700',
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    color: '#F8FAFC',
    fontSize: 18,
    fontWeight: '800',
  },
  sectionSubtitle: {
    color: '#94A3B8',
    fontSize: 12,
  },
  addDayButton: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
  },
  addDayButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  addDayForm: {
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#38BDF8',
    gap: 12,
  },
  formHeading: {
    color: '#38BDF8',
    fontWeight: '800',
    fontSize: 15,
  },
  formRow: {
    gap: 6,
  },
  twoColRow: {
    flexDirection: 'row',
    gap: 10,
  },
  formLabel: {
    color: '#CBD5E1',
    fontSize: 12,
    fontWeight: '600',
  },
  input: {
    backgroundColor: '#0F172A',
    borderColor: '#334155',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#F8FAFC',
    fontSize: 14,
  },
  textArea: {
    minHeight: 60,
    textAlignVertical: 'top',
  },
  saveDayButton: {
    backgroundColor: '#059669',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 4,
  },
  saveDayButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  emptyCard: {
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#334155',
    gap: 8,
  },
  emptyIcon: {
    fontSize: 40,
  },
  emptyTitle: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '700',
  },
  emptySubtitle: {
    color: '#94A3B8',
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 18,
  },
  daysList: {
    gap: 12,
  },
  dayCard: {
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 10,
  },
  dayCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  dayNumberBadge: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  dayNumberText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
  },
  dayDateText: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: '600',
  },
  deleteDayButton: {
    padding: 4,
  },
  deleteDayText: {
    color: '#EF4444',
    fontSize: 14,
    fontWeight: '700',
  },
  dayTitleText: {
    color: '#F8FAFC',
    fontSize: 17,
    fontWeight: '700',
  },
  dayNotesText: {
    color: '#94A3B8',
    fontSize: 13,
    lineHeight: 18,
  },
  dayFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  activityCount: {
    color: '#38BDF8',
    fontSize: 12,
    fontWeight: '600',
  },
  openDayText: {
    color: '#A855F7',
    fontSize: 13,
    fontWeight: '700',
  },
});

