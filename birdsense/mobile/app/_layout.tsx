/**
 * 🐦 BirdSense Mobile - Root Layout
 * Developed by Soham
 */

import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { AuthProvider } from '../src/context/AuthContext';
import { SettingsProvider } from '../src/context/SettingsContext';

export default function RootLayout() {
  return (
    <SettingsProvider>
      <AuthProvider>
        <StatusBar style="light" />
        <Stack
          screenOptions={{
            headerStyle: {
              backgroundColor: '#1a472a',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          }}
        >
          <Stack.Screen
            name="index"
            options={{
              title: '🐦 BirdSense',
              headerShown: false,
            }}
          />
          <Stack.Screen
            name="login"
            options={{
              title: 'Login',
              headerShown: false,
            }}
          />
          <Stack.Screen
            name="(tabs)"
            options={{
              headerShown: false,
            }}
          />
        </Stack>
      </AuthProvider>
    </SettingsProvider>
  );
}

