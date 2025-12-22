/**
 * 🐦 BirdSense Mobile - Description Identification Tab
 * Developed by Soham
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import api, { BirdResult } from '../../src/services/api';
import BirdCard from '../../src/components/BirdCard';

export default function DescribeScreen() {
  const insets = useSafeAreaInsets();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [birds, setBirds] = useState<BirdResult[]>([]);
  const [processingTime, setProcessingTime] = useState(0);
  const [modelUsed, setModelUsed] = useState('');

  const analyzeDescription = async () => {
    if (description.length < 10) {
      Alert.alert('Error', 'Please provide a more detailed description (at least 10 characters)');
      return;
    }

    setBirds([]);
    setIsAnalyzing(true);

    try {
      const result = await api.identifyDescription(description, location || undefined);
      setBirds(result.birds);
      setProcessingTime(result.processing_time_ms);
      setModelUsed(result.model_used);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to analyze description');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const fillExample = () => {
    setDescription('Small bird with bright yellow body and black wings. Has a short conical beak. Seen near sunflower fields making chirping sounds.');
    setLocation('Gujarat, India');
  };

  return (
    <ScrollView 
      style={styles.container}
      contentContainerStyle={{ paddingBottom: insets.bottom + 20 }}
    >
      {/* Instructions */}
      <View style={styles.instructionCard}>
        <Text style={styles.instructionTitle}>📝 Description Identification</Text>
        <Text style={styles.instructionText}>
          Describe what you saw - colors, size, behavior, sounds - and AI will identify the bird.
        </Text>
      </View>

      {/* Description Input */}
      <View style={styles.inputWrapper}>
        <Text style={styles.inputLabel}>🐦 Bird Description</Text>
        <TextInput
          style={styles.descriptionInput}
          placeholder="Describe the bird: colors, patterns, size, beak shape, behavior, sounds..."
          placeholderTextColor="#94a3b8"
          value={description}
          onChangeText={setDescription}
          multiline
          numberOfLines={5}
          textAlignVertical="top"
        />
      </View>

      {/* Location Input */}
      <View style={styles.inputWrapper}>
        <Text style={styles.inputLabel}>📍 Location (optional)</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., Mumbai, India"
          placeholderTextColor="#94a3b8"
          value={location}
          onChangeText={setLocation}
        />
      </View>

      {/* Example Button */}
      <TouchableOpacity style={styles.exampleButton} onPress={fillExample}>
        <Ionicons name="bulb-outline" size={20} color="#f59e0b" />
        <Text style={styles.exampleButtonText}>Fill example description</Text>
      </TouchableOpacity>

      {/* Analyze Button */}
      <TouchableOpacity
        style={[styles.analyzeButton, isAnalyzing && styles.analyzingButton]}
        onPress={analyzeDescription}
        disabled={isAnalyzing}
      >
        {isAnalyzing ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <>
            <Ionicons name="search" size={24} color="#fff" />
            <Text style={styles.analyzeButtonText}>Identify Bird</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Tips */}
      <View style={styles.tipsCard}>
        <Text style={styles.tipsTitle}>💡 Description Tips</Text>
        <Text style={styles.tipItem}>• Mention colors: body, wings, head, beak</Text>
        <Text style={styles.tipItem}>• Compare size: sparrow, pigeon, crow</Text>
        <Text style={styles.tipItem}>• Note behavior: hopping, soaring, diving</Text>
        <Text style={styles.tipItem}>• Describe sounds: chirping, whistling</Text>
        <Text style={styles.tipItem}>• Include habitat: garden, lake, forest</Text>
      </View>

      {/* Results */}
      {birds.length > 0 && (
        <View style={styles.resultsSection}>
          <View style={styles.resultsHeader}>
            <Text style={styles.resultsTitle}>
              🐦 {birds.length} Match{birds.length > 1 ? 'es' : ''} Found
            </Text>
            <Text style={styles.resultsInfo}>
              {processingTime}ms • {modelUsed}
            </Text>
          </View>
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
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  instructionCard: {
    backgroundColor: '#fef3c7',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#f59e0b',
  },
  instructionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#92400e',
    marginBottom: 8,
  },
  instructionText: {
    fontSize: 14,
    color: '#a16207',
  },
  inputWrapper: {
    marginHorizontal: 16,
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 12,
    color: '#64748b',
    marginBottom: 4,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    fontSize: 14,
    color: '#1e293b',
  },
  descriptionInput: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    fontSize: 14,
    color: '#1e293b',
    minHeight: 120,
  },
  exampleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    marginHorizontal: 16,
    marginBottom: 16,
  },
  exampleButtonText: {
    color: '#f59e0b',
    fontSize: 14,
    marginLeft: 6,
  },
  analyzeButton: {
    backgroundColor: '#f59e0b',
    marginHorizontal: 16,
    paddingVertical: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    shadowColor: '#f59e0b',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  analyzingButton: {
    backgroundColor: '#fbbf24',
  },
  analyzeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  tipsCard: {
    backgroundColor: '#f1f5f9',
    margin: 16,
    padding: 16,
    borderRadius: 12,
  },
  tipsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 8,
  },
  tipItem: {
    fontSize: 13,
    color: '#64748b',
    marginBottom: 4,
  },
  resultsSection: {
    paddingBottom: 32,
  },
  resultsHeader: {
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
  },
  resultsInfo: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 4,
  },
});

