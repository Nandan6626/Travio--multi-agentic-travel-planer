import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Platform,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { itineraryService } from '../services/itineraryService';

// Graceful import for native MapView vs Web
let MapView = null;
let Marker = null;
let Callout = null;

if (Platform.OS !== 'web') {
  try {
    const maps = require('react-native-maps');
    MapView = maps.default;
    Marker = maps.Marker;
    Callout = maps.Callout;
  } catch (e) {
    console.warn('Could not load native react-native-maps module:', e);
  }
}

export default function InteractiveMapScreen() {
  const router = useRouter();
  const { dayId, dayTitle, dayNumber } = useLocalSearchParams();
  const mapRef = useRef(null);

  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!dayId) return;
    setLoading(true);
    itineraryService
      .getItems(dayId)
      .then((data) => {
        setItems(data || []);
        const firstWithCoords = (data || []).find(
          (it) => it.place && it.place.latitude != null && it.place.longitude != null
        );
        if (firstWithCoords) {
          setSelectedItem(firstWithCoords);
        }
      })
      .catch((err) => {
        setError(err.message || 'Failed to load day locations.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [dayId]);

  const placesWithCoords = items.filter(
    (it) => it.place && it.place.latitude != null && it.place.longitude != null
  );

  const initialRegion =
    placesWithCoords.length > 0
      ? {
          latitude: placesWithCoords[0].place.latitude,
          longitude: placesWithCoords[0].place.longitude,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        }
      : {
          latitude: 48.8566,
          longitude: 2.3522,
          latitudeDelta: 0.1,
          longitudeDelta: 0.1,
        };

  const focusActivity = (item) => {
    setSelectedItem(item);
    if (mapRef.current && item.place) {
      mapRef.current.animateToRegion(
        {
          latitude: item.place.latitude,
          longitude: item.place.longitude,
          latitudeDelta: 0.02,
          longitudeDelta: 0.02,
        },
        500
      );
    }
  };

  const openExternalMap = (lat, lon, label) => {
    const url = Platform.select({
      ios: `maps:0,0?q=${label}@${lat},${lon}`,
      android: `geo:0,0?q=${lat},${lon}(${label})`,
      web: `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`,
    });
    Linking.openURL(url);
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Header */}
      <View style={styles.topBar}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Day {dayNumber}</Text>
        </TouchableOpacity>
        <View style={styles.titleBox}>
          <Text style={styles.topBarTitle} numberOfLines={1}>
            {dayTitle || 'Day Itinerary Map'}
          </Text>
          <Text style={styles.topBarSub}>
            {placesWithCoords.length} geo-tagged activities
          </Text>
        </View>
        <View style={{ width: 60 }} />
      </View>

      {loading ? (
        <View style={styles.centerBox}>
          <ActivityIndicator color="#38BDF8" size="large" />
          <Text style={styles.loadingText}>Loading activity coordinates...</Text>
        </View>
      ) : error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : placesWithCoords.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>📍</Text>
          <Text style={styles.emptyTitle}>No Geo-Tagged Places</Text>
          <Text style={styles.emptySubtitle}>
            None of the activities scheduled for Day {dayNumber} have latitude and longitude
            coordinates yet.
          </Text>
          <Text style={styles.emptyHint}>
            Tip: Edit an activity and provide location coordinates to visualize it on this map.
          </Text>
          <TouchableOpacity style={styles.backActionButton} onPress={() => router.back()}>
            <Text style={styles.backActionText}>Return to Activities</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.mapWrapper}>
          {Platform.OS !== 'web' && MapView && Marker ? (
            /* Native react-native-maps for Android & iOS */
            <MapView
              ref={mapRef}
              style={styles.map}
              initialRegion={initialRegion}
              showsUserLocation={false}
              showsCompass={true}>
              {placesWithCoords.map((item, index) => (
                <Marker
                  key={item.id}
                  coordinate={{
                    latitude: item.place.latitude,
                    longitude: item.place.longitude,
                  }}
                  title={`#${index + 1}: ${item.activity_name}`}
                  description={`${item.start_time.substring(0, 5)} - ${item.end_time.substring(
                    0,
                    5
                  )} • ${item.place.name}`}
                  onPress={() => setSelectedItem(item)}>
                  <View
                    style={[
                      styles.customMarker,
                      selectedItem?.id === item.id && styles.selectedMarker,
                    ]}>
                    <Text style={styles.customMarkerText}>#{index + 1}</Text>
                  </View>
                  {Callout && (
                    <Callout>
                      <View style={styles.calloutBox}>
                        <Text style={styles.calloutTitle}>
                          #{index + 1} {item.activity_name}
                        </Text>
                        <Text style={styles.calloutPlace}>{item.place.name}</Text>
                        <Text style={styles.calloutTime}>
                          🕒 {item.start_time.substring(0, 5)} - {item.end_time.substring(0, 5)}
                        </Text>
                      </View>
                    </Callout>
                  )}
                </Marker>
              ))}
            </MapView>
          ) : (
            /* Graceful Interactive Web Fallback */
            <View style={styles.webFallbackContainer}>
              <View style={styles.webNoticePill}>
                <Text style={styles.webNoticeText}>
                  🌐 Interactive Geo-Route Inspector (Web Fallback)
                </Text>
              </View>

              <ScrollView contentContainerStyle={styles.webGrid}>
                {placesWithCoords.map((item, index) => (
                  <TouchableOpacity
                    key={item.id}
                    style={[
                      styles.webCard,
                      selectedItem?.id === item.id && styles.webCardSelected,
                    ]}
                    onPress={() => setSelectedItem(item)}>
                    <View style={styles.webCardHeader}>
                      <View style={styles.webOrderBadge}>
                        <Text style={styles.webOrderText}>Stop #{index + 1}</Text>
                      </View>
                      <Text style={styles.webTime}>
                        {item.start_time.substring(0, 5)} - {item.end_time.substring(0, 5)}
                      </Text>
                    </View>

                    <Text style={styles.webActName}>{item.activity_name}</Text>
                    <Text style={styles.webPlaceName}>📍 {item.place.name}</Text>
                    {item.place.address ? (
                      <Text style={styles.webAddress}>{item.place.address}</Text>
                    ) : null}

                    <View style={styles.webCoordsRow}>
                      <Text style={styles.webCoords}>
                        Lat: {item.place.latitude.toFixed(4)}, Lon:{' '}
                        {item.place.longitude.toFixed(4)}
                      </Text>
                      <TouchableOpacity
                        style={styles.extMapLink}
                        onPress={() =>
                          openExternalMap(
                            item.place.latitude,
                            item.place.longitude,
                            item.place.name
                          )
                        }>
                        <Text style={styles.extMapText}>Open in Maps ↗</Text>
                      </TouchableOpacity>
                    </View>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          )}

          {/* Bottom Selected Activity Carousel */}
          <View style={styles.carouselContainer}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.carousel}>
              {placesWithCoords.map((item, index) => {
                const isSelected = selectedItem?.id === item.id;
                return (
                  <TouchableOpacity
                    key={item.id}
                    style={[styles.carouselCard, isSelected && styles.carouselCardSelected]}
                    activeOpacity={0.85}
                    onPress={() => focusActivity(item)}>
                    <View style={styles.carouselTopRow}>
                      <View style={styles.seqBadge}>
                        <Text style={styles.seqText}>#{index + 1}</Text>
                      </View>
                      <Text style={styles.carouselTime}>
                        {item.start_time.substring(0, 5)} - {item.end_time.substring(0, 5)}
                      </Text>
                    </View>
                    <Text style={styles.carouselTitle} numberOfLines={1}>
                      {item.activity_name}
                    </Text>
                    <Text style={styles.carouselPlace} numberOfLines={1}>
                      📍 {item.place.name}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          </View>
        </View>
      )}
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
  titleBox: {
    alignItems: 'center',
    maxWidth: 220,
  },
  topBarTitle: {
    color: '#F8FAFC',
    fontWeight: '800',
    fontSize: 15,
  },
  topBarSub: {
    color: '#94A3B8',
    fontSize: 11,
  },
  centerBox: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    color: '#94A3B8',
    fontSize: 14,
  },
  errorBox: {
    margin: 20,
    padding: 16,
    backgroundColor: '#450A0A',
    borderRadius: 12,
  },
  errorText: {
    color: '#FCA5A5',
    textAlign: 'center',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
    gap: 12,
  },
  emptyIcon: {
    fontSize: 50,
  },
  emptyTitle: {
    color: '#F8FAFC',
    fontSize: 18,
    fontWeight: '800',
  },
  emptySubtitle: {
    color: '#94A3B8',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  emptyHint: {
    color: '#64748B',
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  backActionButton: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 10,
  },
  backActionText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  mapWrapper: {
    flex: 1,
    position: 'relative',
  },
  map: {
    ...StyleSheet.absoluteFillObject,
  },
  customMarker: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 4,
  },
  selectedMarker: {
    backgroundColor: '#EC4899',
    borderColor: '#FDF2F8',
    transform: [{ scale: 1.15 }],
  },
  customMarkerText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 12,
  },
  calloutBox: {
    width: 180,
    padding: 6,
    gap: 4,
  },
  calloutTitle: {
    fontWeight: '800',
    fontSize: 13,
    color: '#0F172A',
  },
  calloutPlace: {
    fontSize: 11,
    color: '#334155',
  },
  calloutTime: {
    fontSize: 10,
    color: '#64748B',
  },
  webFallbackContainer: {
    flex: 1,
    backgroundColor: '#0B1120',
    padding: 16,
  },
  webNoticePill: {
    backgroundColor: '#1E293B',
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#38BDF8',
  },
  webNoticeText: {
    color: '#38BDF8',
    fontSize: 13,
    fontWeight: '700',
    textAlign: 'center',
  },
  webGrid: {
    gap: 12,
    paddingBottom: 110,
  },
  webCard: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 6,
  },
  webCardSelected: {
    borderColor: '#38BDF8',
    backgroundColor: '#1E3A8A',
  },
  webCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  webOrderBadge: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  webOrderText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 11,
  },
  webTime: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '600',
  },
  webActName: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: '700',
  },
  webPlaceName: {
    color: '#F59E0B',
    fontSize: 13,
    fontWeight: '600',
  },
  webAddress: {
    color: '#94A3B8',
    fontSize: 11,
  },
  webCoordsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  webCoords: {
    color: '#64748B',
    fontSize: 11,
  },
  extMapLink: {
    backgroundColor: '#0F172A',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  extMapText: {
    color: '#38BDF8',
    fontSize: 11,
    fontWeight: '700',
  },
  carouselContainer: {
    position: 'absolute',
    bottom: 16,
    left: 0,
    right: 0,
    paddingHorizontal: 12,
  },
  carousel: {
    flexDirection: 'row',
  },
  carouselCard: {
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 12,
    marginRight: 10,
    width: 200,
    borderWidth: 1,
    borderColor: '#334155',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.4,
    shadowRadius: 4,
    elevation: 5,
    gap: 4,
  },
  carouselCardSelected: {
    borderColor: '#38BDF8',
    backgroundColor: '#0F2B48',
  },
  carouselTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  seqBadge: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  seqText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 11,
  },
  carouselTime: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
  },
  carouselTitle: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '700',
  },
  carouselPlace: {
    color: '#F59E0B',
    fontSize: 12,
  },
});

