/**
 * 🐦 BirdSense Mobile - Login Screen
 * Developed by Soham
 * 
 * Simple LOCAL authentication - no network required
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Animated,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../src/context/AuthContext';

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const { login, loginAsGuest, isAuthenticated } = useAuth();

  // Animation
  const fadeAnim = React.useRef(new Animated.Value(0)).current;
  const slideAnim = React.useRef(new Animated.Value(30)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 600, useNativeDriver: true }),
    ]).start();
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/(tabs)/audio');
    }
  }, [isAuthenticated]);

  const handleGuestLogin = async () => {
    setIsLoading(true);
    try {
      await loginAsGuest();
      router.replace('/(tabs)/audio');
    } catch (error: any) {
      Alert.alert('Error', 'Could not login');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setIsLoading(true);
    try {
      await login({ username: 'demo', password: 'demo123' });
      router.replace('/(tabs)/audio');
    } catch (error: any) {
      Alert.alert('Error', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert('Error', 'Please enter username and password');
      return;
    }

    setIsLoading(true);
    try {
      await login({ username, password });
      router.replace('/(tabs)/audio');
    } catch (error: any) {
      Alert.alert('Login Failed', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <LinearGradient colors={['#0f172a', '#1e293b', '#0f172a']} style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <Animated.View 
          style={[
            styles.content, 
            { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }
          ]}
        >
          {/* Logo */}
          <View style={styles.logoContainer}>
            <Text style={styles.logoEmoji}>🐦</Text>
            <Text style={styles.logoText}>BirdSense</Text>
            <Text style={styles.tagline}>AI Bird Identification</Text>
          </View>

          {/* Quick Access Buttons */}
          <View style={styles.quickButtons}>
            {/* Continue as Guest - Primary */}
            <TouchableOpacity
              style={styles.guestButton}
              onPress={handleGuestLogin}
              disabled={isLoading}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#22c55e', '#16a34a']}
                style={styles.buttonGradient}
              >
                {isLoading ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <>
                    <Ionicons name="arrow-forward-circle" size={28} color="#fff" />
                    <Text style={styles.guestButtonText}>Continue as Guest</Text>
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>

            {/* Demo Account */}
            <TouchableOpacity
              style={styles.demoButton}
              onPress={handleDemoLogin}
              disabled={isLoading}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#8b5cf6', '#6d28d9']}
                style={styles.buttonGradient}
              >
                <Ionicons name="flash" size={22} color="#fff" />
                <Text style={styles.demoButtonText}>Demo Account</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>

          {/* Divider */}
          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>or</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* Show/Hide Login Form */}
          <TouchableOpacity 
            style={styles.toggleForm}
            onPress={() => setShowForm(!showForm)}
          >
            <Ionicons 
              name={showForm ? 'chevron-up' : 'key'} 
              size={18} 
              color="#94a3b8" 
            />
            <Text style={styles.toggleFormText}>
              {showForm ? 'Hide login form' : 'Sign in with credentials'}
            </Text>
          </TouchableOpacity>

          {/* Login Form */}
          {showForm && (
            <View style={styles.form}>
              <View style={styles.inputWrapper}>
                <Ionicons name="person" size={20} color="#64748b" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Username"
                  placeholderTextColor="#64748b"
                  value={username}
                  onChangeText={setUsername}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>
              <View style={styles.inputWrapper}>
                <Ionicons name="lock-closed" size={20} color="#64748b" style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Password"
                  placeholderTextColor="#64748b"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                />
              </View>
              <TouchableOpacity
                style={styles.loginButton}
                onPress={handleLogin}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.loginButtonText}>Sign In</Text>
                )}
              </TouchableOpacity>

              {/* Credentials Hint */}
              <View style={styles.hint}>
                <Text style={styles.hintTitle}>Available accounts:</Text>
                <Text style={styles.hintText}>• demo / demo123</Text>
                <Text style={styles.hintText}>• soham / birdsense2024</Text>
                <Text style={styles.hintText}>• guest / guest</Text>
              </View>
            </View>
          )}

          {/* Footer */}
          <Text style={styles.footer}>Developed by Soham • v1.0</Text>
        </Animated.View>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 48,
  },
  logoEmoji: {
    fontSize: 80,
    marginBottom: 8,
  },
  logoText: {
    fontSize: 44,
    fontWeight: '800',
    color: '#fff',
    letterSpacing: -1,
  },
  tagline: {
    fontSize: 16,
    color: '#22c55e',
    marginTop: 8,
    fontWeight: '500',
  },
  quickButtons: {
    gap: 12,
  },
  guestButton: {
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#22c55e',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 8,
  },
  demoButton: {
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#8b5cf6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  buttonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    gap: 12,
  },
  guestButtonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
  },
  demoButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(148, 163, 184, 0.2)',
  },
  dividerText: {
    color: '#64748b',
    paddingHorizontal: 16,
    fontSize: 14,
  },
  toggleForm: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    gap: 8,
  },
  toggleFormText: {
    color: '#94a3b8',
    fontSize: 14,
  },
  form: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 20,
    marginTop: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  inputIcon: {
    paddingLeft: 14,
  },
  input: {
    flex: 1,
    paddingHorizontal: 12,
    paddingVertical: 14,
    fontSize: 16,
    color: '#fff',
  },
  loginButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 4,
  },
  loginButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  hint: {
    marginTop: 16,
    padding: 12,
    backgroundColor: 'rgba(34, 197, 94, 0.1)',
    borderRadius: 8,
  },
  hintTitle: {
    color: '#94a3b8',
    fontSize: 12,
    marginBottom: 6,
  },
  hintText: {
    color: '#22c55e',
    fontSize: 13,
    marginTop: 2,
  },
  footer: {
    textAlign: 'center',
    color: '#64748b',
    fontSize: 12,
    marginTop: 32,
  },
});
