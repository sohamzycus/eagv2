/**
 * 🐦 BirdSense Mobile - Image Identification Tab
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
  Image,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import api, { BirdResult } from '../../src/services/api';
import BirdCard from '../../src/components/BirdCard';

export default function ImageScreen() {
  const insets = useSafeAreaInsets();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [location, setLocation] = useState('');
  const [birds, setBirds] = useState<BirdResult[]>([]);
  const [processingTime, setProcessingTime] = useState(0);
  const [modelUsed, setModelUsed] = useState('');
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
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
    setIsAnalyzing(true);

    try {
      const result = await api.identifyImageFile(uri, location || undefined);
      setBirds(result.birds);
      setProcessingTime(result.processing_time_ms);
      setModelUsed(result.model_used);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to analyze image');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <ScrollView 
      style={styles.container}
      contentContainerStyle={{ paddingBottom: insets.bottom + 20 }}
    >
      {/* Instructions */}
      <View style={styles.instructionCard}>
        <Text style={styles.instructionTitle}>📷 Image Identification</Text>
        <Text style={styles.instructionText}>
          Take a photo or select from gallery for Vision AI analysis.
        </Text>
      </View>

      {/* Location */}
      <View style={styles.inputWrapper}>
        <Text style={styles.inputLabel}>📍 Location (for India-specific info)</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., Kerala, India"
          placeholderTextColor="#94a3b8"
          value={location}
          onChangeText={setLocation}
        />
      </View>

      {/* Image Buttons */}
      <View style={styles.buttonRow}>
        <TouchableOpacity
          style={[styles.actionButton, styles.cameraButton]}
          onPress={takePhoto}
          disabled={isAnalyzing}
        >
          <Ionicons name="camera" size={28} color="#fff" />
          <Text style={styles.buttonText}>Take Photo</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.actionButton, styles.galleryButton]}
          onPress={pickImage}
          disabled={isAnalyzing}
        >
          <Ionicons name="images" size={28} color="#fff" />
          <Text style={styles.buttonText}>Gallery</Text>
        </TouchableOpacity>
      </View>

      {/* Selected Image Preview */}
      {selectedImage && (
        <View style={styles.previewContainer}>
          <Image source={{ uri: selectedImage }} style={styles.previewImage} />
        </View>
      )}

      {/* Loading */}
      {isAnalyzing && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
          <Text style={styles.loadingText}>Analyzing with Vision AI...</Text>
        </View>
      )}

      {/* Results */}
      {birds.length > 0 && (
        <View style={styles.resultsSection}>
          <View style={styles.resultsHeader}>
            <Text style={styles.resultsTitle}>
              🐦 {birds.length} Bird{birds.length > 1 ? 's' : ''} Identified
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
    backgroundColor: '#dbeafe',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#3b82f6',
  },
  instructionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e40af',
    marginBottom: 8,
  },
  instructionText: {
    fontSize: 14,
    color: '#1d4ed8',
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
  buttonRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 12,
    marginBottom: 16,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 20,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  cameraButton: {
    backgroundColor: '#3b82f6',
    shadowColor: '#3b82f6',
  },
  galleryButton: {
    backgroundColor: '#8b5cf6',
    shadowColor: '#8b5cf6',
  },
  buttonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginTop: 8,
  },
  previewContainer: {
    marginHorizontal: 16,
    marginBottom: 16,
  },
  previewImage: {
    width: '100%',
    height: 250,
    borderRadius: 12,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  loadingText: {
    color: '#3b82f6',
    fontSize: 16,
    marginTop: 12,
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

