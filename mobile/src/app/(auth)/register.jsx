import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../../hooks/useAuth';

export default function RegisterScreen() {
  const router = useRouter();
  const { signUp, isConfigured } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleRegister = async () => {
    if (!email.trim() || !password || !fullName.trim()) {
      setErrorMessage('Please fill in all required fields.');
      return;
    }
    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setErrorMessage('');
    setLoading(true);
    try {
      await signUp(email.trim(), password, fullName.trim());
      setSuccessMessage('Registration successful! Please check your email for confirmation or proceed to login.');
      setTimeout(() => {
        router.replace('/(auth)/login');
      }, 2000);
    } catch (err) {
      setErrorMessage(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.icon}>🌍</Text>
          <Text style={styles.title}>Create Travio Account</Text>
          <Text style={styles.subtitle}>Plan, collaborate, and save your travel itineraries</Text>
        </View>

        {!isConfigured && (
          <View style={styles.configNotice}>
            <Text style={styles.configNoticeTitle}>⚠️ Supabase Configuration Required</Text>
            <Text style={styles.configNoticeText}>
              Configure <Text style={styles.codeText}>EXPO_PUBLIC_SUPABASE_URL</Text> to enable live user registration.
            </Text>
          </View>
        )}

        {/* Form Card */}
        <View style={styles.formCard}>
          {errorMessage ? (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          ) : null}

          {successMessage ? (
            <View style={styles.successBox}>
              <Text style={styles.successText}>{successMessage}</Text>
            </View>
          ) : null}

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Full Name</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. Maya Lin"
              placeholderTextColor="#64748B"
              value={fullName}
              onChangeText={setFullName}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Email Address</Text>
            <TextInput
              style={styles.input}
              placeholder="you@example.com"
              placeholderTextColor="#64748B"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Password (min 6 chars)</Text>
            <TextInput
              style={styles.input}
              placeholder="••••••••"
              placeholderTextColor="#64748B"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              autoCapitalize="none"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Confirm Password</Text>
            <TextInput
              style={styles.input}
              placeholder="••••••••"
              placeholderTextColor="#64748B"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry
              autoCapitalize="none"
            />
          </View>

          <TouchableOpacity
            style={[styles.registerButton, loading && styles.buttonDisabled]}
            onPress={handleRegister}
            disabled={loading}
            activeOpacity={0.8}>
            {loading ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={styles.registerButtonText}>Create Account</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.loginLink}
            onPress={() => router.push('/(auth)/login')}
            activeOpacity={0.7}>
            <Text style={styles.loginLinkText}>
              Already have an account? <Text style={styles.linkHighlight}>Sign In</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A',
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
    gap: 16,
  },
  header: {
    alignItems: 'center',
    gap: 8,
  },
  icon: {
    fontSize: 40,
    marginBottom: 4,
  },
  title: {
    fontSize: 26,
    fontWeight: '800',
    color: '#F8FAFC',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 14,
    color: '#94A3B8',
    textAlign: 'center',
  },
  configNotice: {
    backgroundColor: '#1E293B',
    borderColor: '#F59E0B',
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
  },
  configNoticeTitle: {
    color: '#FBBF24',
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 2,
  },
  configNoticeText: {
    color: '#CBD5E1',
    fontSize: 12,
  },
  codeText: {
    fontFamily: 'monospace',
    color: '#38BDF8',
  },
  formCard: {
    backgroundColor: '#1E293B',
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: '#334155',
    gap: 14,
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
    fontSize: 13,
  },
  successBox: {
    backgroundColor: '#064E3B',
    borderWidth: 1,
    borderColor: '#059669',
    padding: 10,
    borderRadius: 8,
  },
  successText: {
    color: '#6EE7B7',
    fontSize: 13,
  },
  inputGroup: {
    gap: 6,
  },
  label: {
    color: '#94A3B8',
    fontSize: 13,
    fontWeight: '600',
  },
  input: {
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: '#F8FAFC',
    fontSize: 15,
  },
  registerButton: {
    backgroundColor: '#10B981',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 6,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  registerButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  loginLink: {
    alignItems: 'center',
    paddingVertical: 4,
  },
  loginLinkText: {
    color: '#94A3B8',
    fontSize: 13,
  },
  linkHighlight: {
    color: '#38BDF8',
    fontWeight: '700',
  },
});
