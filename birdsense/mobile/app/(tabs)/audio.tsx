/**
 * 🐦 BirdSense Mobile - Audio Identification Tab
 * Developed by Soham
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
  Platform,
} from 'react-native';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
import { Ionicons } from '@expo/vector-icons';
import api, { BirdResult } from '../../src/services/api';
import BirdCard from '../../src/components/BirdCard';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export default function AudioScreen() {
  const insets = useSafeAreaInsets();
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [location, setLocation] = useState('');
  const [month, setMonth] = useState(MONTHS[new Date().getMonth()]);
  const [birds, setBirds] = useState<BirdResult[]>([]);
  const [processingTime, setProcessingTime] = useState(0);
  const [modelUsed, setModelUsed] = useState('');
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setupAudio();
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const setupAudio = async () => {
    try {
      const { granted } = await Audio.requestPermissionsAsync();
      if (!granted) {
        Alert.alert('Permission Required', 'Microphone access is needed to record bird calls.');
        return;
      }
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        staysActiveInBackground: false,
      });
    } catch (err) {
      console.log('Audio setup error:', err);
    }
  };

  const startRecording = async () => {
    try {
      setBirds([]);
      setError(null);
      setRecordingDuration(0);

      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync({
        android: {
          extension: '.wav',
          outputFormat: Audio.AndroidOutputFormat.DEFAULT,
          audioEncoder: Audio.AndroidAudioEncoder.DEFAULT,
          sampleRate: 44100,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.wav',
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 44100,
          numberOfChannels: 1,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {},
      });
      await recording.startAsync();
      recordingRef.current = recording;
      setIsRecording(true);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } catch (err: any) {
      Alert.alert('Error', 'Failed to start recording: ' + err.message);
    }
  };

  const stopRecording = async () => {
    if (!recordingRef.current) return;

    // Stop timer
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    setIsRecording(false);
    setIsAnalyzing(true);
    setError(null);

    try {
      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();
      recordingRef.current = null;

      if (uri) {
        console.log('Recording saved to:', uri);
        
        // Check file exists
        const fileInfo = await FileSystem.getInfoAsync(uri);
        console.log('File info:', fileInfo);

        if (!fileInfo.exists) {
          throw new Error('Recording file not found');
        }

        const result = await api.identifyAudioFile(
          uri,
          location || undefined,
          month || undefined
        );
        
        if (result.success === false) {
          throw new Error('Identification failed');
        }
        
        setBirds(result.birds || []);
        setProcessingTime(result.processing_time_ms || 0);
        setModelUsed(result.model_used || 'Unknown');
      }
    } catch (err: any) {
      console.error('Analysis error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to analyze audio';
      setError(errorMsg);
      Alert.alert('Analysis Error', errorMsg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <ScrollView 
      style={styles.container}
      contentContainerStyle={{ paddingBottom: insets.bottom + 20 }}
    >
      {/* Instructions */}
      <View style={styles.instructionCard}>
        <Text style={styles.instructionTitle}>🎵 Audio Identification</Text>
        <Text style={styles.instructionText}>
          Record bird calls for identification using BirdNET + AI hybrid analysis.
          Best results with 5-15 seconds of clear audio.
        </Text>
      </View>

      {/* Location & Month */}
      <View style={styles.inputRow}>
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
        <View style={[styles.inputWrapper, { flex: 0.6 }]}>
          <Text style={styles.inputLabel}>📅 Month</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g., Dec"
            placeholderTextColor="#94a3b8"
            value={month}
            onChangeText={setMonth}
          />
        </View>
      </View>

      {/* Record Button */}
      <TouchableOpacity
        style={[
          styles.recordButton,
          isRecording && styles.recordingButton,
          isAnalyzing && styles.analyzingButton,
        ]}
        onPress={isRecording ? stopRecording : startRecording}
        disabled={isAnalyzing}
        activeOpacity={0.8}
      >
        {isAnalyzing ? (
          <>
            <ActivityIndicator color="#fff" size="large" />
            <Text style={styles.recordButtonText}>Analyzing...</Text>
          </>
        ) : (
          <>
            <Ionicons
              name={isRecording ? 'stop-circle' : 'mic-circle'}
              size={64}
              color="#fff"
            />
            <Text style={styles.recordButtonText}>
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </Text>
            {isRecording && (
              <Text style={styles.durationText}>{formatDuration(recordingDuration)}</Text>
            )}
          </>
        )}
      </TouchableOpacity>

      {isRecording && (
        <View style={styles.recordingIndicator}>
          <View style={styles.recordingDot} />
          <Text style={styles.recordingText}>Recording bird sounds...</Text>
        </View>
      )}

      {/* Error */}
      {error && (
        <View style={styles.errorCard}>
          <Ionicons name="warning" size={20} color="#dc2626" />
          <Text style={styles.errorText}>{error}</Text>
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

      {/* No results */}
      {!isRecording && !isAnalyzing && birds.length === 0 && !error && (
        <View style={styles.emptyState}>
          <Text style={styles.emptyEmoji}>🎤</Text>
          <Text style={styles.emptyText}>
            Tap the button above to start recording bird sounds
          </Text>
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
    backgroundColor: '#ecfdf5',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#22c55e',
  },
  instructionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#065f46',
    marginBottom: 8,
  },
  instructionText: {
    fontSize: 14,
    color: '#047857',
    lineHeight: 20,
  },
  inputRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 12,
    marginBottom: 16,
  },
  inputWrapper: {
    flex: 1,
  },
  inputLabel: {
    fontSize: 12,
    color: '#64748b',
    marginBottom: 4,
    fontWeight: '500',
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    fontSize: 14,
    color: '#1e293b',
  },
  recordButton: {
    backgroundColor: '#22c55e',
    marginHorizontal: 40,
    marginVertical: 20,
    paddingVertical: 28,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#22c55e',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 10,
    elevation: 8,
  },
  recordingButton: {
    backgroundColor: '#dc2626',
    shadowColor: '#dc2626',
  },
  analyzingButton: {
    backgroundColor: '#3b82f6',
    shadowColor: '#3b82f6',
  },
  recordButtonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '600',
    marginTop: 8,
  },
  durationText: {
    color: 'rgba(255,255,255,0.9)',
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 8,
  },
  recordingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  recordingDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#dc2626',
    marginRight: 8,
  },
  recordingText: {
    color: '#dc2626',
    fontSize: 15,
    fontWeight: '500',
  },
  errorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fef2f2',
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 12,
    borderRadius: 10,
    gap: 10,
  },
  errorText: {
    color: '#dc2626',
    fontSize: 14,
    flex: 1,
  },
  resultsSection: {
    paddingBottom: 20,
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
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
    paddingHorizontal: 32,
  },
  emptyEmoji: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 15,
    color: '#64748b',
    textAlign: 'center',
    lineHeight: 22,
  },
});
