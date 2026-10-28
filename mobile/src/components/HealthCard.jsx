import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { API_BASE_URL, API_V1_PREFIX } from '../constants/Config';

/**
 * HealthCard component presenting live backend API diagnostics
 * @param {Object} props
 * @param {Object} props.state
 * @param {Function} props.onRefresh
 */
export function HealthCard({ state, onRefresh }) {
  const isConnected = state?.status === 'connected';
  const isChecking = state?.status === 'checking';
  const isError = state?.status === 'error';

  const badgeColor = isConnected ? '#10B981' : isChecking ? '#3B82F6' : '#EF4444';
  const badgeBg = isConnected ? '#064E3B' : isChecking ? '#1E3A8A' : '#7F1D1D';
  const statusLabel = isConnected
    ? 'BACKEND OPERATIONAL'
    : isChecking
    ? 'CHECKING CONNECTION...'
    : 'DISCONNECTED';

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <View style={[styles.statusDot, { backgroundColor: badgeColor }]} />
          <Text style={styles.title}>API Gateway Diagnostics</Text>
        </View>
        <View style={[styles.badge, { backgroundColor: badgeBg }]}>
          <Text style={[styles.badgeText, { color: badgeColor }]}>{statusLabel}</Text>
        </View>
      </View>

      <View style={styles.content}>
        <View style={styles.infoRow}>
          <Text style={styles.label}>Target Host</Text>
          <Text style={styles.value} numberOfLines={1}>
            {API_BASE_URL}
            {API_V1_PREFIX}/health
          </Text>
        </View>

        {isConnected && state.data && (
          <>
            <View style={styles.metricsGrid}>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Environment</Text>
                <Text style={styles.metricValue}>{String(state.data.environment || '').toUpperCase()}</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Version</Text>
                <Text style={styles.metricValue}>v{state.data.version}</Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={styles.metricLabel}>Latency</Text>
                <Text style={[styles.metricValue, { color: '#10B981' }]}>
                  {state.latencyMs !== null && state.latencyMs !== undefined ? `${state.latencyMs}ms` : '—'}
                </Text>
              </View>
            </View>

            {state.data.services && (
              <View style={styles.subsystemsRow}>
                <Text style={styles.subsystemsLabel}>Services:</Text>
                {Object.entries(state.data.services).map(([name, status]) => (
                  <View key={name} style={styles.serviceChip}>
                    <Text style={styles.serviceChipText}>
                      {name}: <Text style={{ color: '#34D399' }}>{String(status)}</Text>
                    </Text>
                  </View>
                ))}
              </View>
            )}
          </>
        )}

        {isError && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{state.error}</Text>
          </View>
        )}

        {state.lastChecked && (
          <Text style={styles.timestamp}>
            Last verified: {new Date(state.lastChecked).toLocaleTimeString()}
          </Text>
        )}
      </View>

      <TouchableOpacity
        style={[styles.refreshButton, isChecking && styles.refreshButtonDisabled]}
        onPress={onRefresh}
        disabled={isChecking}
        activeOpacity={0.8}
      >
        {isChecking ? (
          <ActivityIndicator size="small" color="#FFFFFF" />
        ) : (
          <Text style={styles.refreshButtonText}>Test Connection</Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#334155',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
    width: '100%',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  title: {
    color: '#F8FAFC',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  content: {
    gap: 10,
    marginBottom: 14,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#0F172A',
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 8,
  },
  label: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '500',
  },
  value: {
    color: '#E2E8F0',
    fontSize: 12,
    fontFamily: 'monospace',
    maxWidth: '65%',
  },
  metricsGrid: {
    flexDirection: 'row',
    gap: 8,
  },
  metricItem: {
    flex: 1,
    backgroundColor: '#0F172A',
    padding: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  metricLabel: {
    color: '#64748B',
    fontSize: 10,
    fontWeight: '600',
    marginBottom: 2,
  },
  metricValue: {
    color: '#F1F5F9',
    fontSize: 13,
    fontWeight: '700',
  },
  subsystemsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flexWrap: 'wrap',
  },
  subsystemsLabel: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
  },
  serviceChip: {
    backgroundColor: '#0F172A',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  serviceChipText: {
    color: '#CBD5E1',
    fontSize: 11,
  },
  errorBox: {
    backgroundColor: '#450A0A',
    borderWidth: 1,
    borderColor: '#991B1B',
    padding: 10,
    borderRadius: 8,
  },
  errorText: {
    color: '#FCA5A5',
    fontSize: 12,
    lineHeight: 16,
  },
  timestamp: {
    color: '#64748B',
    fontSize: 11,
    textAlign: 'right',
  },
  refreshButton: {
    backgroundColor: '#2563EB',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  refreshButtonDisabled: {
    opacity: 0.6,
  },
  refreshButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 13,
  },
});
