import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { itineraryService } from '../services/itineraryService';

export default function DayDetailsScreen() {
  const router = useRouter();
  const { dayId, tripId, role, dayNumber, title, date } = useLocalSearchParams();

  const [day, setDay] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reordering, setReordering] = useState(false);
  const [error, setError] = useState('');

  const canEdit = role === 'OWNER' || role === 'EDITOR';

  const fetchDayDetails = useCallback(async () => {
    if (!dayId) return;
    setLoading(true);
    setError('');
    try {
      const data = await itineraryService.getDay(dayId);
      setDay(data);
      setItems(data.items || []);
    } catch (err) {
      setError(err.message || 'Failed to load day itinerary.');
    } finally {
      setLoading(false);
    }
  }, [dayId]);

  useEffect(() => {
    fetchDayDetails();
  }, [fetchDayDetails]);

  const handleDeleteItem = async (itemId, actName) => {
    Alert.alert('Delete Activity', `Remove "${actName}" from this day's schedule?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await itineraryService.deleteItem(itemId);
            await fetchDayDetails();
          } catch (err) {
            Alert.alert('Delete Error', err.message);
          }
        },
      },
    ]);
  };

  const handleMoveOrder = async (index, direction) => {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= items.length) return;

    const newItems = [...items];
    const [moved] = newItems.splice(index, 1);
    newItems.splice(targetIndex, 0, moved);

    setReordering(true);
    try {
      const itemIds = newItems.map((it) => it.id);
      const reordered = await itineraryService.reorderItems(dayId, itemIds);
      setItems(reordered);
    } catch (err) {
      Alert.alert('Reorder Error', err.message || 'Failed to reorder activities.');
      await fetchDayDetails();
    } finally {
      setReordering(false);
    }
  };

  const placesWithCoordinates = items.filter(
    (item) => item.place && item.place.latitude != null && item.place.longitude != null
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Navigation */}
      <View style={styles.topBar}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Days</Text>
        </TouchableOpacity>
        <Text style={styles.topBarTitle}>
          Day {dayNumber || day?.day_number}: {title || day?.title}
        </Text>
        <View style={{ width: 60 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Day Header Info */}
        <View style={styles.headerCard}>
          <View style={styles.headerTop}>
            <View style={styles.dayPill}>
              <Text style={styles.dayPillText}>Day {day?.day_number || dayNumber}</Text>
            </View>
            <Text style={styles.dayDate}>{day?.date || date}</Text>
          </View>
          <Text style={styles.dayTitle}>{day?.title || title}</Text>
          {day?.notes ? <Text style={styles.dayNotes}>{day.notes}</Text> : null}

          {/* Action Row */}
          <View style={styles.actionRow}>
            {canEdit && (
              <TouchableOpacity
                style={styles.addActButton}
                activeOpacity={0.8}
                onPress={() =>
                  router.push({
                    pathname: '/activity-edit',
                    params: { dayId: dayId, role: role },
                  })
                }>
                <Text style={styles.addActText}>+ Add Activity</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={[
                styles.mapButton,
                placesWithCoordinates.length === 0 && styles.mapButtonDisabled,
              ]}
              activeOpacity={0.8}
              onPress={() =>
                router.push({
                  pathname: '/map',
                  params: {
                    dayId: dayId,
                    dayTitle: day?.title || title,
                    dayNumber: day?.day_number || dayNumber,
                  },
                })
              }>
              <Text style={styles.mapButtonText}>
                🗺️ View on Map ({placesWithCoordinates.length})
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Activities List */}
        <View style={styles.activitiesSection}>
          <Text style={styles.sectionHeading}>
            Scheduled Activities ({items.length})
          </Text>

          {loading ? (
            <View style={styles.centerBox}>
              <ActivityIndicator color="#38BDF8" size="large" />
              <Text style={styles.loadingText}>Loading activities...</Text>
            </View>
          ) : error ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{error}</Text>
              <TouchableOpacity style={styles.retryButton} onPress={fetchDayDetails}>
                <Text style={styles.retryText}>Retry</Text>
              </TouchableOpacity>
            </View>
          ) : items.length === 0 ? (
            <View style={styles.emptyCard}>
              <Text style={styles.emptyIcon}>🎯</Text>
              <Text style={styles.emptyTitle}>No Activities Planned Yet</Text>
              <Text style={styles.emptySubtitle}>
                Add your first morning tour, sightseeing spot, or dinner reservation.
              </Text>
            </View>
          ) : (
            <View style={styles.itemList}>
              {items.map((item, index) => {
                const hasCoords =
                  item.place && item.place.latitude != null && item.place.longitude != null;

                return (
                  <View key={item.id} style={styles.itemCard}>
                    {/* Time & Sequence Bar */}
                    <View style={styles.itemTopRow}>
                      <View style={styles.orderBadge}>
                        <Text style={styles.orderBadgeText}>#{index + 1}</Text>
                      </View>
                      <Text style={styles.timeRangeText}>
                        🕒 {item.start_time.substring(0, 5)} - {item.end_time.substring(0, 5)}{' '}
                        <Text style={styles.durationText}>({item.duration_minutes}m)</Text>
                      </Text>
                      <View style={{ flex: 1 }} />
                      <View style={styles.categoryBadge}>
                        <Text style={styles.categoryBadgeText}>
                          {item.category?.toUpperCase()}
                        </Text>
                      </View>
                    </View>

                    {/* Activity Title & Description */}
                    <Text style={styles.activityName}>{item.activity_name}</Text>
                    {item.description ? (
                      <Text style={styles.activityDescription}>{item.description}</Text>
                    ) : null}

                    {/* Cost & Linked Place Info */}
                    <View style={styles.metaRow}>
                      <Text style={styles.costText}>
                        💰 {item.currency} {parseFloat(item.estimated_cost).toFixed(2)}
                      </Text>
                      {item.place && (
                        <View style={styles.placeBadge}>
                          <Text style={styles.placeName} numberOfLines={1}>
                            📍 {item.place.name}
                          </Text>
                          {hasCoords && (
                            <Text style={styles.coordsText}>
                              ({item.place.latitude.toFixed(3)}, {item.place.longitude.toFixed(3)})
                            </Text>
                          )}
                        </View>
                      )}
                    </View>

                    {/* Actions Row */}
                    {canEdit && (
                      <View style={styles.itemActionsRow}>
                        <View style={styles.reorderButtons}>
                          <TouchableOpacity
                            style={[
                              styles.moveButton,
                              (index === 0 || reordering) && styles.moveButtonDisabled,
                            ]}
                            disabled={index === 0 || reordering}
                            onPress={() => handleMoveOrder(index, -1)}>
                            <Text style={styles.moveButtonText}>▲ Up</Text>
                          </TouchableOpacity>
                          <TouchableOpacity
                            style={[
                              styles.moveButton,
                              (index === items.length - 1 || reordering) &&
                                styles.moveButtonDisabled,
                            ]}
                            disabled={index === items.length - 1 || reordering}
                            onPress={() => handleMoveOrder(index, 1)}>
                            <Text style={styles.moveButtonText}>▼ Down</Text>
                          </TouchableOpacity>
                        </View>

                        <View style={styles.editDeleteButtons}>
                          <TouchableOpacity
                            style={styles.editButton}
                            onPress={() =>
                              router.push({
                                pathname: '/activity-edit',
                                params: {
                                  dayId: dayId,
                                  itemId: item.id,
                                  role: role,
                                },
                              })
                            }>
                            <Text style={styles.editText}>Edit</Text>
                          </TouchableOpacity>
                          <TouchableOpacity
                            style={styles.deleteButton}
                            onPress={() => handleDeleteItem(item.id, item.activity_name)}>
                            <Text style={styles.deleteText}>Delete</Text>
                          </TouchableOpacity>
                        </View>
                      </View>
                    )}
                  </View>
                );
              })}
            </View>
          )}
        </View>
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
    fontSize: 15,
  },
  scrollContent: {
    padding: 16,
    gap: 16,
  },
  headerCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 10,
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  dayPill: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  dayPillText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 12,
  },
  dayDate: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: '600',
  },
  dayTitle: {
    color: '#F8FAFC',
    fontSize: 20,
    fontWeight: '800',
  },
  dayNotes: {
    color: '#CBD5E1',
    fontSize: 13,
    lineHeight: 18,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 6,
  },
  addActButton: {
    flex: 1,
    backgroundColor: '#0284C7',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  addActText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  mapButton: {
    flex: 1,
    backgroundColor: '#059669',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  mapButtonDisabled: {
    opacity: 0.6,
  },
  mapButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  activitiesSection: {
    gap: 12,
  },
  sectionHeading: {
    color: '#F8FAFC',
    fontSize: 17,
    fontWeight: '800',
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
  itemList: {
    gap: 12,
  },
  itemCard: {
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 8,
  },
  itemTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  orderBadge: {
    backgroundColor: '#3B82F6',
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  orderBadgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '800',
  },
  timeRangeText: {
    color: '#38BDF8',
    fontSize: 13,
    fontWeight: '700',
  },
  durationText: {
    color: '#94A3B8',
    fontWeight: '500',
    fontSize: 12,
  },
  categoryBadge: {
    backgroundColor: '#334155',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  categoryBadgeText: {
    color: '#E2E8F0',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  activityName: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '700',
  },
  activityDescription: {
    color: '#94A3B8',
    fontSize: 13,
    lineHeight: 18,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#283548',
    gap: 10,
  },
  costText: {
    color: '#10B981',
    fontWeight: '700',
    fontSize: 13,
  },
  placeBadge: {
    flex: 1,
    alignItems: 'flex-end',
  },
  placeName: {
    color: '#F59E0B',
    fontWeight: '600',
    fontSize: 12,
  },
  coordsText: {
    color: '#64748B',
    fontSize: 10,
  },
  itemActionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#334155',
    marginTop: 4,
  },
  reorderButtons: {
    flexDirection: 'row',
    gap: 6,
  },
  moveButton: {
    backgroundColor: '#0F172A',
    borderColor: '#334155',
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  moveButtonDisabled: {
    opacity: 0.4,
  },
  moveButtonText: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '700',
  },
  editDeleteButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  editButton: {
    backgroundColor: '#1E3A8A',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 6,
  },
  editText: {
    color: '#93C5FD',
    fontSize: 12,
    fontWeight: '700',
  },
  deleteButton: {
    backgroundColor: '#450A0A',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 6,
  },
  deleteText: {
    color: '#FCA5A5',
    fontSize: 12,
    fontWeight: '700',
  },
});

