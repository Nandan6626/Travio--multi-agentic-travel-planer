import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { itineraryService } from '../services/itineraryService';
import { placeService } from '../services/placeService';

export default function ActivityEditScreen() {
  const router = useRouter();
  const { dayId, itemId } = useLocalSearchParams();
  const isEditing = Boolean(itemId);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form Fields
  const [activityName, setActivityName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('sightseeing');
  const [startTime, setStartTime] = useState('09:00:00');
  const [endTime, setEndTime] = useState('11:00:00');
  const [estimatedCost, setEstimatedCost] = useState('0.00');
  const [currency, setCurrency] = useState('USD');

  // Place Fields
  const [placeName, setPlaceName] = useState('');
  const [address, setAddress] = useState('');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');

  useEffect(() => {
    if (isEditing && itemId) {
      setLoading(true);
      itineraryService
        .getItem(itemId)
        .then((item) => {
          setActivityName(item.activity_name || '');
          setDescription(item.description || '');
          setCategory(item.category || 'sightseeing');
          setStartTime(item.start_time || '09:00:00');
          setEndTime(item.end_time || '11:00:00');
          setEstimatedCost(String(item.estimated_cost || '0.00'));
          setCurrency(item.currency || 'USD');

          if (item.place) {
            setPlaceName(item.place.name || '');
            setAddress(item.place.address || '');
            setLatitude(item.place.latitude != null ? String(item.place.latitude) : '');
            setLongitude(item.place.longitude != null ? String(item.place.longitude) : '');
          }
        })
        .catch((err) => {
          Alert.alert('Load Error', err.message);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [isEditing, itemId]);

  const normalizeTime = (t) => {
    const clean = t.trim();
    if (clean.length === 5) return `${clean}:00`;
    return clean;
  };

  const handleSave = async () => {
    if (!activityName.trim()) {
      Alert.alert('Required Field', 'Please enter an activity name.');
      return;
    }

    const normStart = normalizeTime(startTime);
    const normEnd = normalizeTime(endTime);

    if (normEnd <= normStart) {
      Alert.alert('Invalid Times', 'End time must be later than start time.');
      return;
    }

    const costNum = parseFloat(estimatedCost) || 0;
    if (costNum < 0) {
      Alert.alert('Invalid Cost', 'Estimated cost cannot be negative.');
      return;
    }

    // Place validation if coordinates provided
    let placeId = null;
    if (latitude.trim() || longitude.trim() || placeName.trim()) {
      const latNum = parseFloat(latitude);
      const lonNum = parseFloat(longitude);

      if (isNaN(latNum) || latNum < -90 || latNum > 90) {
        Alert.alert('Invalid Latitude', 'Latitude must be a valid number between -90 and 90.');
        return;
      }
      if (isNaN(lonNum) || lonNum < -180 || lonNum > 180) {
        Alert.alert('Invalid Longitude', 'Longitude must be a valid number between -180 and 180.');
        return;
      }
      if (!placeName.trim()) {
        Alert.alert('Place Name Required', 'Please enter a name for the location pin.');
        return;
      }

      setSubmitting(true);
      try {
        const place = await placeService.createPlace({
          name: placeName.trim(),
          address: address.trim() || null,
          latitude: latNum,
          longitude: lonNum,
          category: category,
        });
        placeId = place.id;
      } catch (err) {
        Alert.alert('Location Error', `Failed to register place: ${err.message}`);
        setSubmitting(false);
        return;
      }
    }

    setSubmitting(true);
    try {
      const payload = {
        activity_name: activityName.trim(),
        description: description.trim() || null,
        category: category.trim(),
        start_time: normStart,
        end_time: normEnd,
        estimated_cost: costNum.toFixed(2),
        currency: currency.trim().toUpperCase(),
        ...(placeId ? { place_id: placeId } : {}),
      };

      if (isEditing) {
        await itineraryService.updateItem(itemId, payload);
        Alert.alert('Success', 'Activity updated successfully!');
      } else {
        await itineraryService.createItem(dayId, payload);
        Alert.alert('Success', 'Activity added to schedule!');
      }
      router.back();
    } catch (err) {
      Alert.alert('Save Failed', err.message || 'Schedule conflict or error.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backButtonText}>← Cancel</Text>
        </TouchableOpacity>
        <Text style={styles.topBarTitle}>
          {isEditing ? 'Edit Activity' : 'New Activity'}
        </Text>
        <View style={{ width: 60 }} />
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          {loading ? (
            <View style={styles.centerBox}>
              <ActivityIndicator color="#38BDF8" size="large" />
              <Text style={styles.loadingText}>Loading activity details...</Text>
            </View>
          ) : (
            <View style={styles.formCard}>
              {/* Activity Details Section */}
              <Text style={styles.sectionHeader}>Activity Details</Text>

              <View style={styles.fieldGroup}>
                <Text style={styles.label}>Activity Name *</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g. Guided Louvre Museum Tour"
                  placeholderTextColor="#64748B"
                  value={activityName}
                  onChangeText={setActivityName}
                />
              </View>

              <View style={styles.fieldGroup}>
                <Text style={styles.label}>Description</Text>
                <TextInput
                  style={[styles.input, styles.textArea]}
                  placeholder="e.g. Meet guide at pyramid entrance. Pre-booked ticket #4819."
                  placeholderTextColor="#64748B"
                  multiline
                  numberOfLines={3}
                  value={description}
                  onChangeText={setDescription}
                />
              </View>

              <View style={styles.fieldGroup}>
                <Text style={styles.label}>Category</Text>
                <TextInput
                  style={styles.input}
                  placeholder="sightseeing, dining, museum, transport"
                  placeholderTextColor="#64748B"
                  value={category}
                  onChangeText={setCategory}
                />
              </View>

              <View style={styles.twoColRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.label}>Start Time (HH:MM:SS) *</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="09:00:00"
                    placeholderTextColor="#64748B"
                    value={startTime}
                    onChangeText={setStartTime}
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.label}>End Time (HH:MM:SS) *</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="11:30:00"
                    placeholderTextColor="#64748B"
                    value={endTime}
                    onChangeText={setEndTime}
                  />
                </View>
              </View>

              <View style={styles.twoColRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.label}>Estimated Cost</Text>
                  <TextInput
                    style={styles.input}
                    keyboardType="numeric"
                    placeholder="25.00"
                    placeholderTextColor="#64748B"
                    value={estimatedCost}
                    onChangeText={setEstimatedCost}
                  />
                </View>
                <View style={{ width: 90 }}>
                  <Text style={styles.label}>Currency</Text>
                  <TextInput
                    style={styles.input}
                    maxLength={3}
                    autoCapitalize="characters"
                    placeholder="USD"
                    placeholderTextColor="#64748B"
                    value={currency}
                    onChangeText={setCurrency}
                  />
                </View>
              </View>

              {/* Map & Coordinates Section */}
              <View style={styles.divider} />
              <Text style={styles.sectionHeader}>Location &amp; Map Coordinates</Text>
              <Text style={styles.sectionSub}>
                Provide coordinates to display this activity on the interactive map.
              </Text>

              <View style={styles.fieldGroup}>
                <Text style={styles.label}>Venue / Place Name</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g. Louvre Museum"
                  placeholderTextColor="#64748B"
                  value={placeName}
                  onChangeText={setPlaceName}
                />
              </View>

              <View style={styles.fieldGroup}>
                <Text style={styles.label}>Address</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g. Rue de Rivoli, 75001 Paris, France"
                  placeholderTextColor="#64748B"
                  value={address}
                  onChangeText={setAddress}
                />
              </View>

              <View style={styles.twoColRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.label}>Latitude (-90 to 90)</Text>
                  <TextInput
                    style={styles.input}
                    keyboardType="numeric"
                    placeholder="48.8606"
                    placeholderTextColor="#64748B"
                    value={latitude}
                    onChangeText={setLatitude}
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.label}>Longitude (-180 to 180)</Text>
                  <TextInput
                    style={styles.input}
                    keyboardType="numeric"
                    placeholder="2.3376"
                    placeholderTextColor="#64748B"
                    value={longitude}
                    onChangeText={setLongitude}
                  />
                </View>
              </View>

              {/* Save Button */}
              <TouchableOpacity
                style={[styles.saveButton, submitting && styles.buttonDisabled]}
                onPress={handleSave}
                disabled={submitting}
                activeOpacity={0.8}>
                {submitting ? (
                  <ActivityIndicator color="#FFFFFF" size="small" />
                ) : (
                  <Text style={styles.saveButtonText}>
                    {isEditing ? 'Save Activity Changes' : 'Create Activity'}
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
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
    color: '#94A3B8',
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
  formCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 14,
  },
  sectionHeader: {
    color: '#38BDF8',
    fontSize: 16,
    fontWeight: '800',
  },
  sectionSub: {
    color: '#94A3B8',
    fontSize: 12,
    marginTop: -8,
  },
  divider: {
    height: 1,
    backgroundColor: '#334155',
    marginVertical: 4,
  },
  fieldGroup: {
    gap: 6,
  },
  twoColRow: {
    flexDirection: 'row',
    gap: 10,
  },
  label: {
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
    minHeight: 70,
    textAlignVertical: 'top',
  },
  saveButton: {
    backgroundColor: '#059669',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10,
  },
  saveButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 15,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
});

