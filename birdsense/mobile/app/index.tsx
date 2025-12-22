/**
 * 🐦 BirdSense Mobile - Index (Auth Check)
 * Developed by Soham
 */

import { useEffect } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { router } from 'expo-router';
import { useAuth } from '../src/context/AuthContext';

export default function Index() {
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      // Small delay to ensure navigation is ready
      setTimeout(() => {
        if (isAuthenticated) {
          router.replace('/(tabs)/audio');
        } else {
          router.replace('/login');
        }
      }, 100);
    }
  }, [isLoading, isAuthenticated]);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#22c55e" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a472a',
    justifyContent: 'center',
    alignItems: 'center',
  },
});

