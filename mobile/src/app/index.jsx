import React from 'react';
import { StyleSheet, View, Text, ScrollView, TouchableOpacity, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { HealthCard } from '../components/HealthCard';
import { TripsManager } from '../components/TripsManager';
import { useHealth } from '../hooks/useHealth';

export default function HomeScreen() {
  const router = useRouter();
  const healthState = useHealth(false);

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Brand Header */}
        <View style={styles.header}>
          <View style={styles.logoBadge}>
            <Text style={styles.logoIcon}>✈️</Text>
          </View>
          <Text style={styles.brandTitle}>Travio AI</Text>
          <Text style={styles.brandSubtitle}>
            Autonomous Multi-Agent Travel Planning &amp; Execution
          </Text>
          <View style={styles.milestonePill}>
            <Text style={styles.milestoneText}>Milestone 4 • Real Places, Routing, Weather &amp; Travel Offers</Text>
          </View>
        </View>

        {/* Milestone 4: Travel Data Hub Link Card */}
        <TouchableOpacity
          style={styles.exploreBanner}
          onPress={() => router.push('/explore')}
          activeOpacity={0.8}
        >
          <View style={styles.exploreIconCol}>
            <Text style={styles.exploreBannerIcon}>🌍</Text>
          </View>
          <View style={styles.exploreBannerTextCol}>
            <Text style={styles.exploreBannerTitle}>Explore Live Travel Data</Text>
            <Text style={styles.exploreBannerSubtitle}>
              Places (Geoapify), Routes (OSRM), Weather (Open-Meteo) &amp; Offers (Duffel API)
            </Text>
          </View>
          <Text style={styles.exploreBannerArrow}>→</Text>
        </TouchableOpacity>

        {/* Milestone 2 & 3: Authenticated Trip & Itinerary Manager */}
        <View style={styles.section}>
          <TripsManager />
        </View>

        {/* Milestone 1 Diagnostic: API Gateway Health */}
        <View style={styles.section}>
          <Text style={styles.sectionHeading}>System Diagnostics</Text>
          <HealthCard state={healthState} onRefresh={healthState.refetch} />
        </View>

        {/* Milestone 4 Verification Checklist */}
        <View style={styles.checklistCard}>
          <Text style={styles.checklistTitle}>Milestone 4 Verification Checklist</Text>
          <View style={styles.checklistItem}>
            <Text style={styles.checkIcon}>✅</Text>
            <Text style={styles.checklistText}>
              Geoapify real places &amp; destination geocoding with categories, ratings &amp; database caching
            </Text>
          </View>
          <View style={styles.checklistItem}>
            <Text style={styles.checkIcon}>✅</Text>
            <Text style={styles.checklistText}>
              OSRM routing adapter calculating distances, durations &amp; GeoJSON path geometry
            </Text>
          </View>
          <View style={styles.checklistItem}>
            <Text style={styles.checkIcon}>✅</Text>
            <Text style={styles.checklistText}>
              Open-Meteo live weather observation &amp; 7-day forecast with WMO conditions
            </Text>
          </View>
          <View style={styles.checklistItem}>
            <Text style={styles.checkIcon}>✅</Text>
            <Text style={styles.checklistText}>
              Duffel Flights &amp; Stays API integration with price and currency preservation
            </Text>
          </View>
          <View style={styles.checklistItem}>
            <Text style={styles.checkIcon}>✅</Text>
            <Text style={styles.checklistText}>
              Unified provider services &amp; Pydantic validation schemas distinguishing estimated vs verified prices
            </Text>
          </View>
          <View style={styles.checklistItem}>
            <Text style={styles.checkIcon}>✅</Text>
            <Text style={styles.checklistText}>
              Mobile Travel Hub UI for interactive place search, route calculations, weather &amp; offer queries
            </Text>
          </View>
        </View>

        {/* Platform Info */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Running on {Platform.OS.toUpperCase()} • React Native &amp; Expo Router v58
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  scrollContent: {
    padding: 20,
    gap: 20,
    alignItems: 'center',
  },
  header: {
    alignItems: 'center',
    gap: 8,
    marginTop: 6,
  },
  logoBadge: {
    width: 60,
    height: 60,
    borderRadius: 18,
    backgroundColor: '#1E293B',
    borderWidth: 1,
    borderColor: '#334155',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  logoIcon: {
    fontSize: 28,
  },
  brandTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: '#F8FAFC',
    letterSpacing: -0.5,
  },
  brandSubtitle: {
    fontSize: 13,
    color: '#94A3B8',
    textAlign: 'center',
    maxWidth: 280,
    lineHeight: 18,
  },
  milestonePill: {
    backgroundColor: '#064E3B',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 20,
    marginTop: 4,
  },
  milestoneText: {
    color: '#34D399',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  exploreBanner: {
    width: '100%',
    backgroundColor: '#1E293B',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1.5,
    borderColor: '#0284C7',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  exploreIconCol: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#0369A1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  exploreBannerIcon: {
    fontSize: 22,
  },
  exploreBannerTextCol: {
    flex: 1,
  },
  exploreBannerTitle: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: '700',
  },
  exploreBannerSubtitle: {
    color: '#94A3B8',
    fontSize: 11,
    marginTop: 2,
    lineHeight: 15,
  },
  exploreBannerArrow: {
    color: '#38BDF8',
    fontSize: 20,
    fontWeight: '700',
    paddingHorizontal: 4,
  },
  section: {
    width: '100%',
    gap: 8,
  },
  sectionHeading: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    paddingLeft: 4,
  },
  checklistCard: {
    width: '100%',
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 12,
  },
  checklistTitle: {
    color: '#F1F5F9',
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 4,
  },
  checklistItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  checkIcon: {
    fontSize: 14,
    marginTop: 2,
  },
  checklistText: {
    color: '#CBD5E1',
    fontSize: 13,
    flex: 1,
    lineHeight: 18,
  },
  footer: {
    marginTop: 10,
  },
  footerText: {
    color: '#64748B',
    fontSize: 11,
  },
});
