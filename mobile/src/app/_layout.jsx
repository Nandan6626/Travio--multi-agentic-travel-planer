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
        </Stack>
      </AuthProvider>
    </ThemeProvider>
  );
}
