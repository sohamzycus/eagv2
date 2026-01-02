/**
 * 🐦 BirdSense Mobile - Index (Auth Check & Auto-Login)
 * Developed by Soham
 */

import { useEffect } from 'react';
import { View, Text, ActivityIndicator, StyleSheet, Animated } from 'react-native';
import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../src/context/AuthContext';

export default function Index() {
  const { isAuthenticated, isLoading } = useAuth();
  const fadeAnim = new Animated.Value(0);
  const scaleAnim = new Animated.Value(0.8);

  useEffect(() => {
    // Animate logo
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 800, useNativeDriver: true }),
      Animated.spring(scaleAnim, { toValue: 1, friction: 4, useNativeDriver: true }),
    ]).start();
  }, []);

  useEffect(() => {
    if (!isLoading) {
      // Navigate after a brief moment to show splash
      setTimeout(() => {
        if (isAuthenticated) {
          router.replace('/(tabs)/audio');
        } else {
          router.replace('/login');
        }
      }, 500);
    }
  }, [isLoading, isAuthenticated]);

  return (
    <LinearGradient colors={['#0f172a', '#1e293b', '#0f172a']} style={styles.container}>
      <Animated.View 
        style={[
          styles.content, 
          { opacity: fadeAnim, transform: [{ scale: scaleAnim }] }
        ]}
      >
        <Text style={styles.emoji}>🐦</Text>
        <Text style={styles.title}>BirdSense</Text>
        <Text style={styles.subtitle}>AI Bird Identification</Text>
        
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#22c55e" />
          <Text style={styles.loadingText}>
            {isLoading ? 'Initializing...' : 'Loading...'}
          </Text>
        </View>
      </Animated.View>

      <Text style={styles.footer}>Developed by Soham</Text>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
  },
  emoji: {
    fontSize: 80,
    marginBottom: 16,
  },
  title: {
    fontSize: 42,
    fontWeight: '800',
    color: '#fff',
    letterSpacing: -1,
  },
  subtitle: {
    fontSize: 18,
    color: '#22c55e',
    marginTop: 8,
    fontWeight: '500',
  },
  loadingContainer: {
    marginTop: 48,
    alignItems: 'center',
  },
  loadingText: {
    color: '#94a3b8',
    marginTop: 12,
    fontSize: 14,
  },
  footer: {
    position: 'absolute',
    bottom: 48,
    color: '#64748b',
    fontSize: 12,
  },
});
