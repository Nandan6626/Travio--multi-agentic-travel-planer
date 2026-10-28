import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { supabase, isSupabaseConfigured } from '../services/supabase';
import { setOnUnauthorizedHandler, apiFetch } from '../services/api';

const AuthContext = createContext({
  user: null,
  session: null,
  profile: null,
  loading: true,
  error: null,
  signIn: async () => {},
  signUp: async () => {},
  signOut: async () => {},
  refreshProfile: async () => {},
});

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchBackendProfile = useCallback(async () => {
    try {
      const p = await apiFetch('/profiles/me', { requiresAuth: true });
      setProfile(p);
      return p;
    } catch (err) {
      // Backend profile might not exist yet before first sync
      setProfile(null);
    }
  }, []);

  useEffect(() => {
    // 1. Initial session check
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session) {
        fetchBackendProfile();
      }
      setLoading(false);
    });

    // 2. Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session) {
        fetchBackendProfile();
      } else {
        setProfile(null);
      }
      setLoading(false);
    });

    // 3. Register 401 unauthorized handler
    setOnUnauthorizedHandler(() => {
      setSession(null);
      setUser(null);
      setProfile(null);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [fetchBackendProfile]);

  const signIn = async (email, password) => {
    setError(null);
    setLoading(true);
    try {
      if (!isSupabaseConfigured) {
        throw new Error('Supabase URL and Anon Key are not yet set in EXPO_PUBLIC_* environment variables.');
      }
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      setSession(data.session);
      setUser(data.user);
      await fetchBackendProfile();
      return data;
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (email, password, fullName) => {
    setError(null);
    setLoading(true);
    try {
      if (!isSupabaseConfigured) {
        throw new Error('Supabase URL and Anon Key are not yet set in EXPO_PUBLIC_* environment variables.');
      }
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: fullName },
        },
      });
      if (error) throw error;
      setSession(data.session);
      setUser(data.user);
      return data;
    } catch (err) {
      setError(err.message || 'Sign up failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    setLoading(true);
    try {
      await supabase.auth.signOut();
      setSession(null);
      setUser(null);
      setProfile(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        profile,
        loading,
        error,
        signIn,
        signUp,
        signOut,
        refreshProfile: fetchBackendProfile,
        isConfigured: isSupabaseConfigured,
      }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
