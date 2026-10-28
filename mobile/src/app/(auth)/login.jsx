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

export default function LoginScreen() {
  const router = useRouter();
  const { signIn, isConfigured } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      setErrorMessage('Please enter both email and password.');
      return;
    }
    setErrorMessage('');
    setLoading(true);
    try {
      await signIn(email.trim(), password);
      router.replace('/');
    } catch (err) {
      setErrorMessage(err.message || 'Login failed.');
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
          <Text style={styles.icon}>✈️</Text>
          <Text style={styles.title}>Welcome to Travio AI</Text>
          <Text style={styles.subtitle}>Sign in with Supabase to manage your trips</Text>
        </View>

        {!isConfigured && (
          <View style={styles.configNotice}>
            <Text style={styles.configNoticeTitle}>⚠️ Supabase Credentials Notice</Text>
            <Text style={styles.configNoticeText}>
              Set <Text style={styles.codeText}>EXPO_PUBLIC_SUPABASE_URL</Text> and{' '}
              <Text style={styles.codeText}>EXPO_PUBLIC_SUPABASE_ANON_KEY</Text> in your mobile environment to connect live Supabase project.
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
            <Text style={styles.label}>Password</Text>
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

          <TouchableOpacity
            style={[styles.loginButton, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}
            activeOpacity={0.8}>
            {loading ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={styles.loginButtonText}>Sign In</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.registerLink}
            onPress={() => router.push('/(auth)/register')}
            activeOpacity={0.7}>
            <Text style={styles.registerLinkText}>
              Don't have an account? <Text style={styles.linkHighlight}>Register</Text>
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.skipButton}
            onPress={() => router.replace('/')}
            activeOpacity={0.7}>
            <Text style={styles.skipButtonText}>← Return to Home Screen</Text>
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
    gap: 20,
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
    gap: 4,
  },
  configNoticeTitle: {
    color: '#FBBF24',
    fontSize: 12,
    fontWeight: '700',
  },
  configNoticeText: {
    color: '#CBD5E1',
    fontSize: 12,
    lineHeight: 16,
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
    gap: 16,
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
  loginButton: {
    backgroundColor: '#2563EB',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  loginButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  registerLink: {
    alignItems: 'center',
    paddingVertical: 4,
  },
  registerLinkText: {
    color: '#94A3B8',
    fontSize: 13,
  },
  linkHighlight: {
    color: '#38BDF8',
    fontWeight: '700',
  },
  skipButton: {
    alignItems: 'center',
    paddingTop: 8,
  },
  skipButtonText: {
    color: '#64748B',
    fontSize: 13,
  },
});
