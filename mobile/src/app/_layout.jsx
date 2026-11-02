import React from 'react';
import { Stack, DarkTheme, DefaultTheme, ThemeProvider } from 'expo-router';
import { useColorScheme } from 'react-native';
import { AuthProvider } from '../hooks/useAuth';

export default function RootLayout() {
  const colorScheme = useColorScheme();

  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <AuthProvider>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="index" options={{ headerShown: false }} />
          <Stack.Screen name="explore" options={{ title: 'Explore' }} />
          <Stack.Screen name="(auth)/login" options={{ title: 'Sign In' }} />
          <Stack.Screen name="(auth)/register" options={{ title: 'Register' }} />
          <Stack.Screen name="trip-details" options={{ title: 'Trip Details' }} />
          <Stack.Screen name="day-details" options={{ title: 'Day Itinerary' }} />
          <Stack.Screen name="activity-edit" options={{ title: 'Activity' }} />
          <Stack.Screen name="map" options={{ title: 'Interactive Map' }} />
        </Stack>
      </AuthProvider>
    </ThemeProvider>
  );
}
