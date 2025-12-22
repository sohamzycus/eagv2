/**
 * 🐦 BirdSense Mobile - Image Identification Tab
 * Developed by Soham
 * 
 * Features: Glass morphism, animations, auto-scroll
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  TextInput,
  Alert,
  ActivityIndicator,
  Image,
  Animated,
  Easing,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import api, { BirdResult } from '../../src/services/api';
import BirdCard from '../../src/components/BirdCard';

export default function ImageScreen() {
  const insets = useSafeAreaInsets();
  const scrollViewRef = useRef<ScrollView>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [location, setLocation] = useState('');
  const [birds, setBirds] = useState<BirdResult[]>([]);
  const [processingTime, setProcessingTime] = useState(0);
  const [modelUsed, setModelUsed] = useState('');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Animations
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        easing: Easing.out(Easing.back(1.2)),
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 600,
        easing: Easing.out(Easing.back(1.1)),
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsEditing: true,
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      processImage(result.assets[0].uri);
    }
  };

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Required', 'Camera access is needed to take photos');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      processImage(result.assets[0].uri);
    }
  };

  const processImage = async (uri: string) => {
    setSelectedImage(uri);
    setBirds([]);
    setError(null);
    setIsAnalyzing(true);

    try {
      const result = await api.identifyImageFile(uri, location || undefined);
      
      // Stream results
      const allBirds = result.birds || [];
      setBirds([]);
      
      for (let i = 0; i < allBirds.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 400));
        setBirds(prev => [...prev, allBirds[i]]);
        setTimeout(() => {
          scrollViewRef.current?.scrollToEnd({ animated: true });
        }, 100);
      }
      
      setProcessingTime(result.processing_time_ms || 0);
      setModelUsed(result.model_used || 'Vision AI');
      
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 500);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to analyze image';
      setError(errorMsg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <LinearGradient
      colors={['#0f172a', '#1e293b', '#0f172a']}
      style={styles.gradient}
    >
      <ScrollView 
        ref={scrollViewRef}
        style={styles.container}
        contentContainerStyle={{ paddingBottom: insets.bottom + 100 }}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
          {/* Hero Section */}
          <View style={styles.heroSection}>
            <Text style={styles.heroEmoji}>📷</Text>
            <Text style={styles.heroTitle}>Image Identification</Text>
            <Text style={styles.heroSubtitle}>
              Take a photo or select from gallery
            </Text>
          </View>

          {/* Location Input */}
          <View style={styles.inputSection}>
            <View style={styles.inputWrapper}>
              <View style={styles.inputIcon}>
                <Ionicons name="location" size={18} color="#3b82f6" />
              </View>
              <TextInput
                style={styles.input}
                placeholder="Location for India-specific info"
                placeholderTextColor="#64748b"
                value={location}
                onChangeText={setLocation}
              />
            </View>
          </View>

          {/* Action Buttons */}
          <Animated.View style={[styles.actionSection, { transform: [{ scale: scaleAnim }] }]}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={takePhoto}
              disabled={isAnalyzing}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#3b82f6', '#1d4ed8']}
                style={styles.actionGradient}
              >
                <Ionicons name="camera" size={32} color="#fff" />
                <Text style={styles.actionLabel}>Camera</Text>
              </LinearGradient>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionButton}
              onPress={pickImage}
              disabled={isAnalyzing}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#8b5cf6', '#6d28d9']}
                style={styles.actionGradient}
              >
                <Ionicons name="images" size={32} color="#fff" />
                <Text style={styles.actionLabel}>Gallery</Text>
              </LinearGradient>
            </TouchableOpacity>
          </Animated.View>

          {/* Selected Image Preview */}
          {selectedImage && (
            <View style={styles.previewSection}>
              <Image source={{ uri: selectedImage }} style={styles.previewImage} />
              {isAnalyzing && (
                <View style={styles.previewOverlay}>
                  <ActivityIndicator size="large" color="#fff" />
                  <Text style={styles.previewStatus}>Analyzing with Vision AI...</Text>
                </View>
              )}
            </View>
          )}

          {/* Error */}
          {error && (
            <View style={styles.errorCard}>
              <Ionicons name="alert-circle" size={24} color="#ef4444" />
              <View style={styles.errorContent}>
                <Text style={styles.errorTitle}>Analysis Failed</Text>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            </View>
          )}

          {/* Results */}
          {birds.length > 0 && (
            <View style={styles.resultsSection}>
              <View style={styles.resultsHeader}>
                <View style={styles.resultsHeaderLeft}>
                  <Text style={styles.resultsEmoji}>🐦</Text>
                  <Text style={styles.resultsTitle}>
                    {birds.length} Bird{birds.length > 1 ? 's' : ''} Found
                  </Text>
                </View>
                <View style={styles.resultsBadge}>
                  <Text style={styles.resultsBadgeText}>{processingTime}ms</Text>
                </View>
              </View>
              <Text style={styles.resultsModel}>{modelUsed}</Text>
              
              {birds.map((bird, index) => (
                <BirdCard
                  key={`${bird.name}-${index}`}
                  bird={bird}
                  index={index + 1}
                  expanded={index === 0}
                />
              ))}
            </View>
          )}

          {/* Empty State */}
          {!selectedImage && !isAnalyzing && birds.length === 0 && (
            <View style={styles.emptyState}>
              <Text style={styles.emptyEmoji}>📸</Text>
              <Text style={styles.emptyTitle}>No Image Selected</Text>
              <Text style={styles.emptyText}>
                Take a photo of a bird or select one from your gallery
              </Text>
            </View>
          )}
        </Animated.View>
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  heroSection: {
    alignItems: 'center',
    paddingTop: 20,
    paddingBottom: 16,
  },
  heroEmoji: {
    fontSize: 48,
    marginBottom: 8,
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: '#fff',
    letterSpacing: -0.5,
  },
  heroSubtitle: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 4,
  },
  inputSection: {
    paddingHorizontal: 16,
    marginBottom: 20,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  inputIcon: {
    paddingLeft: 12,
  },
  input: {
    flex: 1,
    padding: 14,
    fontSize: 15,
    color: '#fff',
  },
  actionSection: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  actionButton: {
    flex: 1,
    maxWidth: 160,
    shadowColor: '#3b82f6',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  actionGradient: {
    paddingVertical: 24,
    borderRadius: 16,
    alignItems: 'center',
  },
  actionLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 8,
  },
  previewSection: {
    marginHorizontal: 16,
    marginBottom: 20,
    borderRadius: 16,
    overflow: 'hidden',
  },
  previewImage: {
    width: '100%',
    height: 250,
    borderRadius: 16,
  },
  previewOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
  },
  previewStatus: {
    color: '#fff',
    fontSize: 16,
    marginTop: 12,
    fontWeight: '500',
  },
  errorCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  errorContent: {
    flex: 1,
    marginLeft: 12,
  },
  errorTitle: {
    color: '#fca5a5',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  errorText: {
    color: '#fca5a5',
    fontSize: 14,
    lineHeight: 20,
  },
  resultsSection: {
    marginTop: 8,
  },
  resultsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 4,
  },
  resultsHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  resultsEmoji: {
    fontSize: 24,
    marginRight: 8,
  },
  resultsTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  resultsBadge: {
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  resultsBadgeText: {
    color: '#3b82f6',
    fontSize: 12,
    fontWeight: '600',
  },
  resultsModel: {
    color: '#64748b',
    fontSize: 12,
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: 40,
  },
  emptyEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 15,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 22,
  },
});
