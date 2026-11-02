import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { travelDataService } from '../services/travelDataService';

const PRESETS = [
  { name: 'Paris', lat: 48.8566, lon: 2.3522, originAir: 'JFK', destAir: 'CDG' },
  { name: 'Tokyo', lat: 35.6762, lon: 139.6503, originAir: 'SFO', destAir: 'HND' },
  { name: 'London', lat: 51.5074, lon: -0.1278, originAir: 'JFK', destAir: 'LHR' },
  { name: 'New York', lat: 40.7128, lon: -74.0060, originAir: 'LAX', destAir: 'JFK' },
];

export default function ExploreScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('places'); // 'places' | 'routing' | 'weather' | 'offers'

  // ---- Places State ----
  const [placeQuery, setPlaceQuery] = useState('Paris');
  const [placeCategory, setPlaceCategory] = useState('tourism.attraction');
  const [places, setPlaces] = useState([]);
  const [loadingPlaces, setLoadingPlaces] = useState(false);
  const [placesError, setPlacesError] = useState('');

  // ---- Routing State ----
  const [routeOriginLat, setRouteOriginLat] = useState('48.8566');
  const [routeOriginLon, setRouteOriginLon] = useState('2.3522');
  const [routeDestLat, setRouteDestLat] = useState('48.8584');
  const [routeDestLon, setRouteDestLon] = useState('2.2945');
  const [routeProfile, setRouteProfile] = useState('driving');
  const [routeResult, setRouteResult] = useState(null);
  const [loadingRoute, setLoadingRoute] = useState(false);
  const [routeError, setRouteError] = useState('');

  // ---- Weather State ----
  const [weatherLat, setWeatherLat] = useState('48.8566');
  const [weatherLon, setWeatherLon] = useState('2.3522');
  const [weatherData, setWeatherData] = useState(null);
  const [loadingWeather, setLoadingWeather] = useState(false);
  const [weatherError, setWeatherError] = useState('');

  // ---- Offers State ----
  const [offerType, setOfferType] = useState('flight'); // 'flight' | 'hotel'
  const [flightOrigin, setFlightOrigin] = useState('JFK');
  const [flightDest, setFlightDest] = useState('LHR');
  const [flightDate, setFlightDate] = useState('2026-12-01');
  const [flightReturnDate, setFlightReturnDate] = useState('2026-12-10');
  const [hotelLat, setHotelLat] = useState('40.7580');
  const [hotelLon, setHotelLon] = useState('-73.9855');
  const [hotelCheckIn, setHotelCheckIn] = useState('2026-12-01');
  const [hotelCheckOut, setHotelCheckOut] = useState('2026-12-05');
  const [offersList, setOffersList] = useState([]);
  const [loadingOffers, setLoadingOffers] = useState(false);
  const [offersError, setOffersError] = useState('');

  // ---- Places Actions ----
  const handleSearchPlaces = async () => {
    if (!placeQuery.trim()) return;
    setLoadingPlaces(true);
    setPlacesError('');
    try {
      const results = await travelDataService.searchPlaces({
        text: placeQuery.trim(),
        categories: placeCategory,
        limit: 15,
      });
      setPlaces(results || []);
    } catch (err) {
      setPlacesError(err.message || 'Failed to search places.');
    } finally {
      setLoadingPlaces(false);
    }
  };

  // ---- Routing Actions ----
  const handleCalculateRoute = async () => {
    setLoadingRoute(true);
    setRouteError('');
    try {
      const res = await travelDataService.calculateRoute({
        origin: { latitude: parseFloat(routeOriginLat), longitude: parseFloat(routeOriginLon) },
        destination: { latitude: parseFloat(routeDestLat), longitude: parseFloat(routeDestLon) },
        profile: routeProfile,
      });
      setRouteResult(res);
    } catch (err) {
      setRouteError(err.message || 'Failed to calculate route.');
    } finally {
      setLoadingRoute(false);
    }
  };

  // ---- Weather Actions ----
  const handleGetWeather = async (lat = weatherLat, lon = weatherLon) => {
    setLoadingWeather(true);
    setWeatherError('');
    try {
      const res = await travelDataService.getWeatherForecast({
        lat: parseFloat(lat),
        lon: parseFloat(lon),
        days: 7,
      });
      setWeatherData(res);
    } catch (err) {
      setWeatherError(err.message || 'Failed to fetch weather.');
    } finally {
      setLoadingWeather(false);
    }
  };

  // ---- Offers Actions ----
  const handleSearchOffers = async () => {
    setLoadingOffers(true);
    setOffersError('');
    setOffersList([]);
    try {
      if (offerType === 'flight') {
        const payload = {
          origin: flightOrigin.trim().toUpperCase(),
          destination: flightDest.trim().toUpperCase(),
          departure_date: flightDate,
          return_date: flightReturnDate || undefined,
          adults: 1,
          cabin_class: 'economy',
        };
        const res = await travelDataService.searchFlights(payload);
        setOffersList(res || []);
      } else {
        const payload = {
          latitude: parseFloat(hotelLat),
          longitude: parseFloat(hotelLon),
          check_in_date: hotelCheckIn,
          check_out_date: hotelCheckOut,
          rooms: 1,
          guests: 2,
        };
        const res = await travelDataService.searchHotels(payload);
        setOffersList(res || []);
      }
    } catch (err) {
      setOffersError(err.message || 'Travel offer search error.');
    } finally {
      setLoadingOffers(false);
    }
  };

  const applyPreset = (preset) => {
    setPlaceQuery(preset.name);
    setWeatherLat(String(preset.lat));
    setWeatherLon(String(preset.lon));
    setFlightOrigin(preset.originAir);
    setFlightDest(preset.destAir);
    setHotelLat(String(preset.lat));
    setHotelLon(String(preset.lon));
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        {/* Navigation Bar */}
        <View style={styles.navBar}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
            <Text style={styles.backBtnText}>← Back</Text>
          </TouchableOpacity>
          <Text style={styles.title}>Travel Data Hub</Text>
          <View style={{ width: 60 }} />
        </View>

        {/* Preset Chips */}
        <View style={styles.presetSection}>
          <Text style={styles.presetLabel}>Quick Presets:</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.presetScroll}>
            {PRESETS.map((p) => (
              <TouchableOpacity key={p.name} style={styles.presetChip} onPress={() => applyPreset(p)}>
                <Text style={styles.presetChipText}>{p.name}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Tab Switcher */}
        <View style={styles.tabBar}>
          <TouchableOpacity
            style={[styles.tabItem, activeTab === 'places' && styles.tabItemActive]}
            onPress={() => setActiveTab('places')}
          >
            <Text style={[styles.tabText, activeTab === 'places' && styles.tabTextActive]}>📍 Places</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tabItem, activeTab === 'routing' && styles.tabItemActive]}
            onPress={() => setActiveTab('routing')}
          >
            <Text style={[styles.tabText, activeTab === 'routing' && styles.tabTextActive]}>🛣️ Routing</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tabItem, activeTab === 'weather' && styles.tabItemActive]}
            onPress={() => setActiveTab('weather')}
          >
            <Text style={[styles.tabText, activeTab === 'weather' && styles.tabTextActive]}>☀️ Weather</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tabItem, activeTab === 'offers' && styles.tabItemActive]}
            onPress={() => setActiveTab('offers')}
          >
            <Text style={[styles.tabText, activeTab === 'offers' && styles.tabTextActive]}>✈️ Offers</Text>
          </TouchableOpacity>
        </View>

        {/* =========================================================================
            TAB 1: PLACES (Geoapify)
        ========================================================================= */}
        {activeTab === 'places' && (
          <View style={styles.card}>
            <Text style={styles.cardHeader}>Real Places &amp; Attractions (Geoapify)</Text>
            <Text style={styles.cardSub}>Search points of interest with verified coordinates and metadata.</Text>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Destination / Keyword</Text>
              <TextInput
                style={styles.input}
                value={placeQuery}
                onChangeText={setPlaceQuery}
                placeholder="e.g. Paris, Eiffel Tower, Tokyo"
                placeholderTextColor="#64748B"
              />
            </View>

            <View style={styles.categoryPills}>
              {[
                { label: 'Attractions', value: 'tourism.attraction' },
                { label: 'Restaurants', value: 'catering.restaurant' },
                { label: 'Museums', value: 'entertainment.museum' },
                { label: 'Leisure', value: 'leisure.park' },
              ].map((c) => (
                <TouchableOpacity
                  key={c.value}
                  style={[styles.catPill, placeCategory === c.value && styles.catPillActive]}
                  onPress={() => setPlaceCategory(c.value)}
                >
                  <Text style={[styles.catPillText, placeCategory === c.value && styles.catPillTextActive]}>
                    {c.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <TouchableOpacity style={styles.primaryBtn} onPress={handleSearchPlaces} disabled={loadingPlaces}>
              {loadingPlaces ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.primaryBtnText}>🔍 Search Real Places</Text>
              )}
            </TouchableOpacity>

            {placesError ? (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>⚠️ {placesError}</Text>
                <TouchableOpacity style={styles.retryBtn} onPress={handleSearchPlaces}>
                  <Text style={styles.retryText}>Retry</Text>
                </TouchableOpacity>
              </View>
            ) : null}

            {places.length > 0 ? (
              <View style={styles.resultsList}>
                <Text style={styles.resultsCount}>Found {places.length} verified places:</Text>
                {places.map((place, idx) => (
                  <View key={place.provider_id || idx} style={styles.placeItem}>
                    <View style={styles.placeHeader}>
                      <Text style={styles.placeName}>{place.name}</Text>
                      <View style={styles.providerBadge}>
                        <Text style={styles.providerBadgeText}>Geoapify</Text>
                      </View>
                    </View>
                    {place.address ? <Text style={styles.placeAddress}>📍 {place.address}</Text> : null}
                    <View style={styles.placeMetaRow}>
                      <Text style={styles.placeCoords}>
                        🌐 {place.latitude.toFixed(4)}, {place.longitude.toFixed(4)}
                      </Text>
                      {place.rating ? <Text style={styles.placeRating}>⭐ {place.rating}</Text> : null}
                    </View>
                    {place.opening_hours?.open_now !== undefined ? (
                      <Text style={place.opening_hours.open_now ? styles.openText : styles.closedText}>
                        🕒 {place.opening_hours.open_now ? 'Open Now' : 'Closed'}
                      </Text>
                    ) : null}
                  </View>
                ))}
              </View>
            ) : !loadingPlaces && !placesError ? (
              <Text style={styles.emptyText}>Enter a location and tap search to retrieve points of interest.</Text>
            ) : null}
          </View>
        )}

        {/* =========================================================================
            TAB 2: ROUTING (OSRM)
        ========================================================================= */}
        {activeTab === 'routing' && (
          <View style={styles.card}>
            <Text style={styles.cardHeader}>Routing &amp; Travel Duration (OSRM)</Text>
            <Text style={styles.cardSub}>Computes exact distance and free-flow travel time between coordinates.</Text>

            <View style={styles.coordsGrid}>
              <View style={styles.coordsCol}>
                <Text style={styles.inputLabel}>Origin Latitude</Text>
                <TextInput
                  style={styles.input}
                  value={routeOriginLat}
                  onChangeText={setRouteOriginLat}
                  keyboardType="numeric"
                />
              </View>
              <View style={styles.coordsCol}>
                <Text style={styles.inputLabel}>Origin Longitude</Text>
                <TextInput
                  style={styles.input}
                  value={routeOriginLon}
                  onChangeText={setRouteOriginLon}
                  keyboardType="numeric"
                />
              </View>
            </View>

            <View style={styles.coordsGrid}>
              <View style={styles.coordsCol}>
                <Text style={styles.inputLabel}>Destination Latitude</Text>
                <TextInput
                  style={styles.input}
                  value={routeDestLat}
                  onChangeText={setRouteDestLat}
                  keyboardType="numeric"
                />
              </View>
              <View style={styles.coordsCol}>
                <Text style={styles.inputLabel}>Destination Longitude</Text>
                <TextInput
                  style={styles.input}
                  value={routeDestLon}
                  onChangeText={setRouteDestLon}
                  keyboardType="numeric"
                />
              </View>
            </View>

            {/* Profile Selection */}
            <View style={styles.profileRow}>
              {['driving', 'walking', 'cycling'].map((p) => (
                <TouchableOpacity
                  key={p}
                  style={[styles.profileBtn, routeProfile === p && styles.profileBtnActive]}
                  onPress={() => setRouteProfile(p)}
                >
                  <Text style={[styles.profileText, routeProfile === p && styles.profileTextActive]}>
                    {p.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <TouchableOpacity style={styles.primaryBtn} onPress={handleCalculateRoute} disabled={loadingRoute}>
              {loadingRoute ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.primaryBtnText}>📐 Calculate Distance &amp; Time</Text>
              )}
            </TouchableOpacity>

            {routeError ? (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>⚠️ {routeError}</Text>
                <TouchableOpacity style={styles.retryBtn} onPress={handleCalculateRoute}>
                  <Text style={styles.retryText}>Retry</Text>
                </TouchableOpacity>
              </View>
            ) : null}

            {routeResult ? (
              <View style={styles.routeResultBox}>
                <View style={styles.statRow}>
                  <View style={styles.statBox}>
                    <Text style={styles.statVal}>{routeResult.distance_km} km</Text>
                    <Text style={styles.statLabel}>Distance ({routeResult.distance_meters} m)</Text>
                  </View>
                  <View style={styles.statBox}>
                    <Text style={styles.statVal}>{routeResult.duration_minutes} min</Text>
                    <Text style={styles.statLabel}>Est. Travel Time</Text>
                  </View>
                </View>
                <View style={styles.disclaimerBox}>
                  <Text style={styles.disclaimerText}>
                    ℹ️ <Text style={{ fontWeight: '700' }}>Note:</Text> Calculated via OSRM based on speed limits and free flow. Live traffic conditions are not included.
                  </Text>
                </View>
                {routeResult.geometry?.coordinates ? (
                  <Text style={styles.geomText}>
                    📍 Path Geometry: {routeResult.geometry.coordinates.length} route coordinates plotted.
                  </Text>
                ) : null}
              </View>
            ) : null}
          </View>
        )}

        {/* =========================================================================
            TAB 3: WEATHER (Open-Meteo)
        ========================================================================= */}
        {activeTab === 'weather' && (
          <View style={styles.card}>
            <Text style={styles.cardHeader}>Destination Weather Forecast (Open-Meteo)</Text>
            <Text style={styles.cardSub}>Current atmospheric conditions and 7-day forecast via Open-Meteo API.</Text>

            <View style={styles.coordsGrid}>
              <View style={styles.coordsCol}>
                <Text style={styles.inputLabel}>Latitude</Text>
                <TextInput
                  style={styles.input}
                  value={weatherLat}
                  onChangeText={setWeatherLat}
                  keyboardType="numeric"
                />
              </View>
              <View style={styles.coordsCol}>
                <Text style={styles.inputLabel}>Longitude</Text>
                <TextInput
                  style={styles.input}
                  value={weatherLon}
                  onChangeText={setWeatherLon}
                  keyboardType="numeric"
                />
              </View>
            </View>

            <TouchableOpacity style={styles.primaryBtn} onPress={() => handleGetWeather()} disabled={loadingWeather}>
              {loadingWeather ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.primaryBtnText}>🌤️ Fetch Live Weather</Text>
              )}
            </TouchableOpacity>

            {weatherError ? (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>⚠️ {weatherError}</Text>
                <TouchableOpacity style={styles.retryBtn} onPress={() => handleGetWeather()}>
                  <Text style={styles.retryText}>Retry</Text>
                </TouchableOpacity>
              </View>
            ) : null}

            {weatherData?.current ? (
              <View style={styles.weatherCard}>
                <View style={styles.weatherHero}>
                  <Text style={styles.tempHero}>{weatherData.current.temperature_celsius}°C</Text>
                  <Text style={styles.conditionHero}>{weatherData.current.condition}</Text>
                </View>
                <View style={styles.weatherDetailsGrid}>
                  <View style={styles.weatherDetailCol}>
                    <Text style={styles.weatherDetailLabel}>Humidity</Text>
                    <Text style={styles.weatherDetailVal}>{weatherData.current.humidity_percent ?? '--'}%</Text>
                  </View>
                  <View style={styles.weatherDetailCol}>
                    <Text style={styles.weatherDetailLabel}>Wind Speed</Text>
                    <Text style={styles.weatherDetailVal}>{weatherData.current.wind_speed_kmh ?? '--'} km/h</Text>
                  </View>
                  <View style={styles.weatherDetailCol}>
                    <Text style={styles.weatherDetailLabel}>Timezone</Text>
                    <Text style={styles.weatherDetailVal}>{weatherData.timezone}</Text>
                  </View>
                </View>

                {/* 7-Day Forecast */}
                <Text style={styles.forecastHeader}>7-Day Daily Forecast</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.dailyScroll}>
                  {weatherData.daily.map((d) => (
                    <View key={d.date} style={styles.dailyCard}>
                      <Text style={styles.dailyDate}>{d.date.slice(5)}</Text>
                      <Text style={styles.dailyCondition}>{d.condition}</Text>
                      <Text style={styles.dailyTempMax}>{d.temp_max_celsius}°</Text>
                      <Text style={styles.dailyTempMin}>{d.temp_min_celsius}°</Text>
                      {d.precipitation_probability_percent !== null && (
                        <Text style={styles.dailyRain}>💧 {d.precipitation_probability_percent}%</Text>
                      )}
                    </View>
                  ))}
                </ScrollView>
              </View>
            ) : null}
          </View>
        )}

        {/* =========================================================================
            TAB 4: TRAVEL OFFERS (Duffel API)
        ========================================================================= */}
        {activeTab === 'offers' && (
          <View style={styles.card}>
            <Text style={styles.cardHeader}>Travel Offers &amp; Quotes (Duffel API)</Text>
            <Text style={styles.cardSub}>Search live flight and hotel rates. Prices are verified directly from Duffel.</Text>

            {/* Sub-tab selection */}
            <View style={styles.subTabBar}>
              <TouchableOpacity
                style={[styles.subTabItem, offerType === 'flight' && styles.subTabItemActive]}
                onPress={() => setOfferType('flight')}
              >
                <Text style={[styles.subTabText, offerType === 'flight' && styles.subTabTextActive]}>
                  ✈️ Flight Search
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.subTabItem, offerType === 'hotel' && styles.subTabItemActive]}
                onPress={() => setOfferType('hotel')}
              >
                <Text style={[styles.subTabText, offerType === 'hotel' && styles.subTabTextActive]}>
                  🏨 Hotel Search
                </Text>
              </TouchableOpacity>
            </View>

            {offerType === 'flight' ? (
              <View>
                <View style={styles.coordsGrid}>
                  <View style={styles.coordsCol}>
                    <Text style={styles.inputLabel}>Origin (IATA/City)</Text>
                    <TextInput
                      style={styles.input}
                      value={flightOrigin}
                      onChangeText={setFlightOrigin}
                      placeholder="e.g. JFK"
                      placeholderTextColor="#64748B"
                      autoCapitalize="characters"
                    />
                  </View>
                  <View style={styles.coordsCol}>
                    <Text style={styles.inputLabel}>Destination</Text>
                    <TextInput
                      style={styles.input}
                      value={flightDest}
                      onChangeText={setFlightDest}
                      placeholder="e.g. LHR"
                      placeholderTextColor="#64748B"
                      autoCapitalize="characters"
                    />
                  </View>
                </View>
                <View style={styles.coordsGrid}>
                  <View style={styles.coordsCol}>
                    <Text style={styles.inputLabel}>Departure Date</Text>
                    <TextInput
                      style={styles.input}
                      value={flightDate}
                      onChangeText={setFlightDate}
                      placeholder="YYYY-MM-DD"
                      placeholderTextColor="#64748B"
                    />
                  </View>
                  <View style={styles.coordsCol}>
                    <Text style={styles.inputLabel}>Return Date (Opt)</Text>
                    <TextInput
                      style={styles.input}
                      value={flightReturnDate}
                      onChangeText={setFlightReturnDate}
                      placeholder="YYYY-MM-DD"
                      placeholderTextColor="#64748B"
                    />
                  </View>
                </View>
              </View>
            ) : (
              <View>
                <View style={styles.coordsGrid}>
                  <View style={styles.coordsCol}>
                    <Text style={styles.inputLabel}>Center Latitude</Text>
                    <TextInput
                      style={styles.input}
                      value={hotelLat}
                      onChangeText={setHotelLat}
                      keyboardType="numeric"
                    />
                  </View>
                  <View style={styles.coordsCol}>
                    <Text style={styles.inputLabel}>Center Longitude</Text>
                    <TextInput
                      style={styles.input}
                      value={hotelLon}
                      onChangeText={setHotelLon}
                      keyboardType="numeric"
                    />
                  </View>
                </View>
                <View style={styles.coordsGrid}>
                  <View style={styles.coordsCol}>
                    <Text style={styles.inputLabel}>Check-In Date</Text>
                    <TextInput
                      style={styles.input}
                      value={hotelCheckIn}
                      onChangeText={setHotelCheckIn}
                      placeholder="YYYY-MM-DD"
                      placeholderTextColor="#64748B"
                    />
                  </View>
                  <View style={styles.coordsCol}>
                    <Text style={styles.inputLabel}>Check-Out Date</Text>
                    <TextInput
                      style={styles.input}
                      value={hotelCheckOut}
                      onChangeText={setHotelCheckOut}
                      placeholder="YYYY-MM-DD"
                      placeholderTextColor="#64748B"
                    />
                  </View>
                </View>
              </View>
            )}

            <TouchableOpacity style={styles.primaryBtn} onPress={handleSearchOffers} disabled={loadingOffers}>
              {loadingOffers ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.primaryBtnText}>🔍 Search Live Offers via Duffel</Text>
              )}
            </TouchableOpacity>

            {offersError ? (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>⚠️ {offersError}</Text>
                <TouchableOpacity style={styles.retryBtn} onPress={handleSearchOffers}>
                  <Text style={styles.retryText}>Retry</Text>
                </TouchableOpacity>
              </View>
            ) : null}

            {offersList.length > 0 ? (
              <View style={styles.resultsList}>
                <Text style={styles.resultsCount}>Found {offersList.length} verified live offers:</Text>
                {offersList.map((offer, idx) => (
                  <View key={offer.offer_id || idx} style={styles.offerItem}>
                    <View style={styles.offerHeader}>
                      <Text style={styles.offerTitle}>
                        {offerType === 'flight'
                          ? `${offer.airline || 'Airline'} • ${offer.origin} → ${offer.destination}`
                          : offer.hotel_name || 'Accommodation'}
                      </Text>
                      <Text style={styles.offerPrice}>
                        {offer.currency} {offer.total_amount}
                      </Text>
                    </View>
                    <View style={styles.offerMeta}>
                      <Text style={styles.offerDetails}>
                        {offerType === 'flight'
                          ? `Stops: ${offer.stops ?? 0} • Duration: ${offer.duration_minutes ?? '--'}m • Cabin: ${offer.cabin_class || 'economy'}`
                          : `Rate: ${offer.room_type || 'Standard'} • Check-in: ${offer.check_in_date || '--'}`}
                      </Text>
                      <Text style={styles.validText}>Valid until: {offer.expires_at || 'Standard Duffel validity'}</Text>
                    </View>
                  </View>
                ))}
              </View>
            ) : !loadingOffers && !offersError ? (
              <Text style={styles.emptyText}>Tap search to query live travel data from the Duffel API.</Text>
            ) : null}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  container: {
    padding: 16,
    paddingBottom: 40,
  },
  navBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  backBtn: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#1E293B',
    borderRadius: 8,
  },
  backBtnText: {
    color: '#38BDF8',
    fontWeight: '600',
    fontSize: 14,
  },
  title: {
    color: '#F8FAFC',
    fontSize: 18,
    fontWeight: '700',
  },
  presetSection: {
    marginBottom: 16,
  },
  presetLabel: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  presetScroll: {
    flexDirection: 'row',
  },
  presetChip: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  presetChipText: {
    color: '#E2E8F0',
    fontSize: 13,
    fontWeight: '600',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 4,
    marginBottom: 20,
  },
  tabItem: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  tabItemActive: {
    backgroundColor: '#38BDF8',
  },
  tabText: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: '600',
  },
  tabTextActive: {
    color: '#0F172A',
    fontWeight: '700',
  },
  card: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: '#334155',
  },
  cardHeader: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  cardSub: {
    color: '#94A3B8',
    fontSize: 13,
    marginBottom: 16,
    lineHeight: 18,
  },
  inputGroup: {
    marginBottom: 14,
  },
  inputLabel: {
    color: '#CBD5E1',
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#F8FAFC',
    fontSize: 14,
  },
  categoryPills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  catPill: {
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#334155',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  catPillActive: {
    borderColor: '#38BDF8',
    backgroundColor: 'rgba(56, 189, 248, 0.1)',
  },
  catPillText: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '500',
  },
  catPillTextActive: {
    color: '#38BDF8',
    fontWeight: '700',
  },
  primaryBtn: {
    backgroundColor: '#0284C7',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 4,
  },
  primaryBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  errorBox: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderWidth: 1,
    borderColor: '#EF4444',
    padding: 12,
    borderRadius: 8,
    marginTop: 14,
  },
  errorText: {
    color: '#FCA5A5',
    fontSize: 13,
    lineHeight: 18,
  },
  retryBtn: {
    marginTop: 8,
    alignSelf: 'flex-start',
    backgroundColor: '#EF4444',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 6,
  },
  retryText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 12,
  },
  resultsList: {
    marginTop: 18,
    gap: 12,
  },
  resultsCount: {
    color: '#38BDF8',
    fontSize: 13,
    fontWeight: '600',
  },
  placeItem: {
    backgroundColor: '#0F172A',
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#334155',
  },
  placeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  placeName: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: '700',
    flex: 1,
  },
  providerBadge: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  providerBadgeText: {
    color: '#94A3B8',
    fontSize: 10,
    fontWeight: '600',
  },
  placeAddress: {
    color: '#CBD5E1',
    fontSize: 13,
    marginBottom: 6,
  },
  placeMetaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  placeCoords: {
    color: '#64748B',
    fontSize: 12,
  },
  placeRating: {
    color: '#FBBF24',
    fontSize: 12,
    fontWeight: '600',
  },
  openText: {
    color: '#34D399',
    fontSize: 12,
    fontWeight: '600',
    marginTop: 4,
  },
  closedText: {
    color: '#F87171',
    fontSize: 12,
    fontWeight: '600',
    marginTop: 4,
  },
  emptyText: {
    color: '#64748B',
    fontSize: 13,
    textAlign: 'center',
    marginVertical: 24,
  },
  coordsGrid: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 10,
  },
  coordsCol: {
    flex: 1,
  },
  profileRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 14,
  },
  profileBtn: {
    flex: 1,
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#334155',
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  profileBtnActive: {
    borderColor: '#38BDF8',
    backgroundColor: 'rgba(56, 189, 248, 0.1)',
  },
  profileText: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
  },
  profileTextActive: {
    color: '#38BDF8',
    fontWeight: '700',
  },
  routeResultBox: {
    marginTop: 18,
    backgroundColor: '#0F172A',
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#334155',
  },
  statRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  statBox: {
    alignItems: 'center',
  },
  statVal: {
    color: '#38BDF8',
    fontSize: 22,
    fontWeight: '700',
  },
  statLabel: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: 2,
  },
  disclaimerBox: {
    backgroundColor: '#1E293B',
    padding: 10,
    borderRadius: 8,
    marginTop: 6,
  },
  disclaimerText: {
    color: '#94A3B8',
    fontSize: 11,
    lineHeight: 16,
  },
  geomText: {
    color: '#64748B',
    fontSize: 12,
    marginTop: 8,
  },
  weatherCard: {
    marginTop: 18,
    backgroundColor: '#0F172A',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
  },
  weatherHero: {
    alignItems: 'center',
    marginBottom: 16,
  },
  tempHero: {
    color: '#F8FAFC',
    fontSize: 44,
    fontWeight: '800',
  },
  conditionHero: {
    color: '#38BDF8',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 4,
  },
  weatherDetailsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: '#1E293B',
    paddingVertical: 12,
    marginBottom: 16,
  },
  weatherDetailCol: {
    alignItems: 'center',
  },
  weatherDetailLabel: {
    color: '#64748B',
    fontSize: 11,
  },
  weatherDetailVal: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '600',
    marginTop: 2,
  },
  forecastHeader: {
    color: '#CBD5E1',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 10,
  },
  dailyScroll: {
    flexDirection: 'row',
  },
  dailyCard: {
    backgroundColor: '#1E293B',
    padding: 12,
    borderRadius: 10,
    marginRight: 10,
    alignItems: 'center',
    minWidth: 80,
    borderWidth: 1,
    borderColor: '#334155',
  },
  dailyDate: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '600',
  },
  dailyCondition: {
    color: '#38BDF8',
    fontSize: 11,
    marginVertical: 4,
    textAlign: 'center',
  },
  dailyTempMax: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '700',
  },
  dailyTempMin: {
    color: '#64748B',
    fontSize: 12,
  },
  dailyRain: {
    color: '#60A5FA',
    fontSize: 10,
    marginTop: 4,
  },
  subTabBar: {
    flexDirection: 'row',
    backgroundColor: '#0F172A',
    borderRadius: 8,
    padding: 3,
    marginBottom: 14,
  },
  subTabItem: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 6,
  },
  subTabItemActive: {
    backgroundColor: '#0284C7',
  },
  subTabText: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '600',
  },
  subTabTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  offerItem: {
    backgroundColor: '#0F172A',
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#334155',
  },
  offerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  offerTitle: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '700',
    flex: 1,
  },
  offerPrice: {
    color: '#34D399',
    fontSize: 16,
    fontWeight: '800',
  },
  offerMeta: {
    marginTop: 4,
  },
  offerDetails: {
    color: '#CBD5E1',
    fontSize: 12,
    marginBottom: 2,
  },
  validText: {
    color: '#64748B',
    fontSize: 11,
  },
});
