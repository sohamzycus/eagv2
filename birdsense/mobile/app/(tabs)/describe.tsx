/**
 * 🐦 BirdSense Mobile - Description Identification Tab
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
  Animated,
  Easing,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import api, { BirdResult } from '../../src/services/api';
import BirdCard from '../../src/components/BirdCard';

const EXAMPLE_DESCRIPTIONS = [
  "Small yellow bird with black wings, seen near sunflowers",
  "Large brown bird with white head and curved beak",
  "Blue bird with orange chest, about 6 inches long",
  "Bright green parrot with red beak, very noisy",
];

export default function DescribeScreen() {
  const insets = useSafeAreaInsets();
  const scrollViewRef = useRef<ScrollView>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [birds, setBirds] = useState<BirdResult[]>([]);
  const [processingTime, setProcessingTime] = useState(0);
  const [modelUsed, setModelUsed] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  // Animations
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

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
    ]).start();
  }, []);

  const analyzeDescription = async () => {
    if (description.length < 10) {
      Alert.alert('More Details Needed', 'Please provide a more detailed description (at least 10 characters).');
      return;
    }

    setBirds([]);
    setError(null);
    setIsAnalyzing(true);

    try {
      const result = await api.identifyDescription(description, location || undefined);
      
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
      setModelUsed(result.model_used || 'AI');
      
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 500);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to analyze description';
      setError(errorMsg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const useExample = (example: string) => {
    setDescription(example);
  };

  return (
    <LinearGradient
      colors={['#0f172a', '#1e293b', '#0f172a']}
      style={styles.gradient}
    >
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <ScrollView 
          ref={scrollViewRef}
          style={styles.container}
          contentContainerStyle={{ paddingBottom: insets.bottom + 100 }}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <Animated.View style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
            {/* Hero Section */}
            <View style={styles.heroSection}>
              <Text style={styles.heroEmoji}>📝</Text>
              <Text style={styles.heroTitle}>Description ID</Text>
              <Text style={styles.heroSubtitle}>
                Describe a bird and let AI identify it
              </Text>
            </View>

            {/* Description Input */}
            <View style={styles.inputSection}>
              <Text style={styles.inputLabel}>Describe the bird you saw</Text>
              <View style={styles.textAreaWrapper}>
                <TextInput
                  style={styles.textArea}
                  placeholder="E.g., Small bird with bright yellow body, black wings, seen near sunflower fields..."
                  placeholderTextColor="#64748b"
                  value={description}
                  onChangeText={setDescription}
                  multiline
                  numberOfLines={4}
                  textAlignVertical="top"
                />
                <Text style={styles.charCount}>{description.length} chars</Text>
              </View>
            </View>

            {/* Example Suggestions */}
            <View style={styles.examplesSection}>
              <Text style={styles.examplesLabel}>Try an example:</Text>
              <ScrollView 
                horizontal 
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.examplesScroll}
              >
                {EXAMPLE_DESCRIPTIONS.map((example, index) => (
                  <TouchableOpacity
                    key={index}
                    style={styles.exampleChip}
                    onPress={() => useExample(example)}
                  >
                    <Text style={styles.exampleText} numberOfLines={1}>
                      {example.substring(0, 30)}...
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            {/* Location Input */}
            <View style={styles.locationSection}>
              <View style={styles.inputWrapper}>
                <View style={styles.inputIcon}>
                  <Ionicons name="location" size={18} color="#f59e0b" />
                </View>
                <TextInput
                  style={styles.input}
                  placeholder="Location (optional)"
                  placeholderTextColor="#64748b"
                  value={location}
                  onChangeText={setLocation}
                />
              </View>
            </View>

            {/* Identify Button */}
            <TouchableOpacity
              style={[styles.identifyButton, isAnalyzing && styles.identifyButtonDisabled]}
              onPress={analyzeDescription}
              disabled={isAnalyzing || description.length < 10}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={description.length >= 10 ? ['#f59e0b', '#d97706'] : ['#475569', '#334155']}
                style={styles.identifyGradient}
              >
                {isAnalyzing ? (
                  <>
                    <ActivityIndicator color="#fff" size="small" />
                    <Text style={styles.identifyText}>Analyzing...</Text>
                  </>
                ) : (
                  <>
                    <Ionicons name="search" size={24} color="#fff" />
                    <Text style={styles.identifyText}>Identify Bird</Text>
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>

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
                      {birds.length} Match{birds.length > 1 ? 'es' : ''} Found
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
            {!isAnalyzing && birds.length === 0 && !error && (
              <View style={styles.emptyState}>
                <Text style={styles.emptyEmoji}>✏️</Text>
                <Text style={styles.emptyTitle}>Describe a Bird</Text>
                <Text style={styles.emptyText}>
                  Include details like size, color, markings, behavior, and where you saw it
                </Text>
              </View>
            )}
          </Animated.View>
        </ScrollView>
      </KeyboardAvoidingView>
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
    marginBottom: 16,
  },
  inputLabel: {
    color: '#e2e8f0',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  textAreaWrapper: {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    overflow: 'hidden',
  },
  textArea: {
    padding: 16,
    fontSize: 15,
    color: '#fff',
    minHeight: 120,
  },
  charCount: {
    color: '#64748b',
    fontSize: 12,
    textAlign: 'right',
    padding: 8,
    paddingTop: 0,
  },
  examplesSection: {
    marginBottom: 16,
  },
  examplesLabel: {
    color: '#94a3b8',
    fontSize: 13,
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  examplesScroll: {
    paddingHorizontal: 16,
    gap: 8,
  },
  exampleChip: {
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(245, 158, 11, 0.3)',
    marginRight: 8,
  },
  exampleText: {
    color: '#fbbf24',
    fontSize: 13,
  },
  locationSection: {
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
  identifyButton: {
    marginHorizontal: 16,
    marginBottom: 24,
    shadowColor: '#f59e0b',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  identifyButtonDisabled: {
    shadowOpacity: 0,
  },
  identifyGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 14,
    gap: 10,
  },
  identifyText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
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
    backgroundColor: 'rgba(245, 158, 11, 0.2)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  resultsBadgeText: {
    color: '#f59e0b',
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
    paddingVertical: 40,
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
