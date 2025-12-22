/**
 * 🐦 BirdSense Mobile - Audio Identification Tab
 * Developed by Soham
 * 
 * Features: Record audio, Upload audio file, Animated waveform, streaming results
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
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Audio } from 'expo-av';
import * as DocumentPicker from 'expo-document-picker';
import { Ionicons } from '@expo/vector-icons';
import api, { BirdResult } from '../../src/services/api';
import BirdCard from '../../src/components/BirdCard';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const { width } = Dimensions.get('window');
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const NUM_BARS = 24;

// Animated Waveform Component
function Waveform({ isActive }: { isActive: boolean }) {
  const animations = useRef(
    Array.from({ length: NUM_BARS }, () => new Animated.Value(0.2))
  ).current;

  useEffect(() => {
    if (isActive) {
      animations.forEach((anim, index) => {
        const animate = () => {
          Animated.sequence([
            Animated.timing(anim, {
              toValue: Math.random() * 0.8 + 0.2,
              duration: 100 + Math.random() * 150,
              easing: Easing.inOut(Easing.ease),
              useNativeDriver: false,
            }),
            Animated.timing(anim, {
              toValue: Math.random() * 0.4 + 0.1,
              duration: 100 + Math.random() * 150,
              easing: Easing.inOut(Easing.ease),
              useNativeDriver: false,
            }),
          ]).start(() => {
            if (isActive) animate();
          });
        };
        setTimeout(animate, index * 30);
      });
    } else {
      animations.forEach(anim => {
        Animated.timing(anim, {
          toValue: 0.2,
          duration: 400,
          easing: Easing.out(Easing.ease),
          useNativeDriver: false,
        }).start();
      });
    }
  }, [isActive]);

  return (
    <View style={styles.waveformContainer}>
      {animations.map((anim, index) => (
        <Animated.View
          key={index}
          style={[
            styles.waveformBar,
            {
              height: anim.interpolate({
                inputRange: [0, 1],
                outputRange: ['5%', '100%'],
              }),
              opacity: anim.interpolate({
                inputRange: [0, 1],
                outputRange: [0.4, 1],
              }),
            },
          ]}
        />
      ))}
    </View>
  );
}

// Analysis Progress Component
function AnalysisProgress({ stage }: { stage: string }) {
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.1, duration: 600, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const stages = [
    { key: 'uploading', label: 'Uploading audio', icon: 'cloud-upload' },
    { key: 'processing', label: 'Processing audio', icon: 'musical-notes' },
    { key: 'birdnet', label: 'BirdNET analysis', icon: 'search' },
    { key: 'llm', label: 'AI enrichment', icon: 'sparkles' },
  ];

  const currentIndex = stages.findIndex(s => s.key === stage);

  return (
    <View style={styles.progressCard}>
      {stages.map((s, index) => (
        <View key={s.key} style={styles.progressStep}>
          <Animated.View style={[
            styles.progressIcon,
            index <= currentIndex && styles.progressIconActive,
            index === currentIndex && { transform: [{ scale: pulseAnim }] },
          ]}>
            {index < currentIndex ? (
              <Ionicons name="checkmark" size={16} color="#fff" />
            ) : (
              <Ionicons name={s.icon as any} size={16} color={index <= currentIndex ? "#fff" : "#94a3b8"} />
            )}
          </Animated.View>
          <Text style={[styles.progressLabel, index <= currentIndex && styles.progressLabelActive]}>
            {s.label}
          </Text>
          {index === currentIndex && (
            <ActivityIndicator size="small" color="#22c55e" style={{ marginLeft: 8 }} />
          )}
        </View>
      ))}
    </View>
  );
}

export default function AudioScreen() {
  const insets = useSafeAreaInsets();
  const scrollViewRef = useRef<ScrollView>(null);
  const [mode, setMode] = useState<'record' | 'upload'>('record');
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStage, setAnalysisStage] = useState('');
  const [location, setLocation] = useState('');
  const [month, setMonth] = useState(MONTHS[new Date().getMonth()]);
  const [birds, setBirds] = useState<BirdResult[]>([]);
  const [processingTime, setProcessingTime] = useState(0);
  const [modelUsed, setModelUsed] = useState('');
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Animations
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    setupAudio();
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 600,
        easing: Easing.out(Easing.back(1.2)),
        useNativeDriver: true,
      }),
    ]).start();
    
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
      setSelectedFileName(null);

      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync({
        android: {
          extension: '.m4a',
          outputFormat: Audio.AndroidOutputFormat.MPEG_4,
          audioEncoder: Audio.AndroidAudioEncoder.AAC,
          sampleRate: 44100,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.m4a',
          outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 44100,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        web: {},
      });
      await recording.startAsync();
      recordingRef.current = recording;
      setIsRecording(true);

      timerRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } catch (err: any) {
      Alert.alert('Recording Error', 'Failed to start recording. Please check microphone permissions.');
    }
  };

  const stopRecording = async () => {
    if (!recordingRef.current) return;

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    setIsRecording(false);
    
    try {
      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();
      recordingRef.current = null;

      if (uri) {
        await analyzeAudio(uri);
      }
    } catch (err: any) {
      setError('Failed to stop recording');
    }
  };

  const pickAudioFile = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['audio/*', 'video/mp4'], // Include mp4 for m4a files
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets && result.assets[0]) {
        const file = result.assets[0];
        setSelectedFileName(file.name);
        setBirds([]);
        setError(null);
        await analyzeAudio(file.uri);
      }
    } catch (err: any) {
      Alert.alert('Error', 'Failed to pick audio file');
    }
  };

  const analyzeAudio = async (uri: string) => {
    setIsAnalyzing(true);
    setAnalysisStage('uploading');
    setError(null);

    try {
      console.log('Analyzing audio:', uri);
      
      setAnalysisStage('processing');
      setTimeout(() => setAnalysisStage('birdnet'), 1500);
      setTimeout(() => setAnalysisStage('llm'), 4000);

      const result = await api.identifyAudioFile(uri, location || undefined, month || undefined);
      
      if (result.success === false) {
        throw new Error(result.error || 'Identification failed');
      }
      
      // Stream results with animation
      const allBirds = result.birds || [];
      setBirds([]);
      
      for (let i = 0; i < allBirds.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 400));
        setBirds(prev => [...prev, allBirds[i]]);
        setTimeout(() => scrollViewRef.current?.scrollToEnd({ animated: true }), 100);
      }
      
      setProcessingTime(result.processing_time_ms || 0);
      setModelUsed(result.model_used || 'Unknown');
      
      setTimeout(() => scrollViewRef.current?.scrollToEnd({ animated: true }), 500);
    } catch (err: any) {
      console.error('Analysis error:', err);
      let errorMsg = 'Failed to analyze audio';
      
      if (err.response?.data?.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.message) {
        errorMsg = err.message;
      }
      
      if (errorMsg.includes('format') || errorMsg.includes('decode') || errorMsg.includes('BytesIO')) {
        errorMsg = 'Audio format not supported. Please use M4A, MP3, or WAV format.';
      }
      
      setError(errorMsg);
    } finally {
      setIsAnalyzing(false);
      setAnalysisStage('');
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <LinearGradient colors={['#0f172a', '#1e293b', '#0f172a']} style={styles.gradient}>
      <ScrollView 
        ref={scrollViewRef}
        style={styles.container}
        contentContainerStyle={{ paddingBottom: insets.bottom + 100 }}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
          {/* Hero Section */}
          <View style={styles.heroSection}>
            <Text style={styles.heroEmoji}>🎵</Text>
            <Text style={styles.heroTitle}>Audio Identification</Text>
            <Text style={styles.heroSubtitle}>Record or upload bird calls</Text>
          </View>

          {/* Mode Tabs */}
          <View style={styles.modeTabs}>
            <TouchableOpacity
              style={[styles.modeTab, mode === 'record' && styles.modeTabActive]}
              onPress={() => setMode('record')}
            >
              <Ionicons name="mic" size={20} color={mode === 'record' ? '#fff' : '#64748b'} />
              <Text style={[styles.modeTabText, mode === 'record' && styles.modeTabTextActive]}>
                Record
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modeTab, mode === 'upload' && styles.modeTabActive]}
              onPress={() => setMode('upload')}
            >
              <Ionicons name="cloud-upload" size={20} color={mode === 'upload' ? '#fff' : '#64748b'} />
              <Text style={[styles.modeTabText, mode === 'upload' && styles.modeTabTextActive]}>
                Upload File
              </Text>
            </TouchableOpacity>
          </View>

          {/* Tips Card */}
          <View style={styles.glassCard}>
            <View style={styles.tipRow}>
              <Ionicons name="bulb" size={18} color="#fbbf24" />
              <Text style={styles.tipText}>
                {mode === 'record' 
                  ? 'Best results with 5-15 seconds of clear audio'
                  : 'Supports M4A, MP3, WAV, MP4 audio files'}
              </Text>
            </View>
          </View>

          {/* Location & Month */}
          <View style={styles.inputSection}>
            <View style={styles.inputWrapper}>
              <View style={styles.inputIcon}>
                <Ionicons name="location" size={18} color="#22c55e" />
              </View>
              <TextInput
                style={styles.input}
                placeholder="Location (e.g., Mumbai)"
                placeholderTextColor="#64748b"
                value={location}
                onChangeText={setLocation}
              />
            </View>
            <View style={[styles.inputWrapper, { flex: 0.5 }]}>
              <View style={styles.inputIcon}>
                <Ionicons name="calendar" size={18} color="#22c55e" />
              </View>
              <TextInput
                style={styles.input}
                placeholder="Month"
                placeholderTextColor="#64748b"
                value={month}
                onChangeText={setMonth}
              />
            </View>
          </View>

          {/* Waveform Visualization */}
          {(isRecording || isAnalyzing) && (
            <View style={styles.waveformSection}>
              <LinearGradient
                colors={['rgba(34, 197, 94, 0.1)', 'rgba(34, 197, 94, 0.05)']}
                style={styles.waveformGradient}
              >
                <Waveform isActive={isRecording} />
                {isRecording && (
                  <Text style={styles.waveformDuration}>{formatDuration(recordingDuration)}</Text>
                )}
                {isAnalyzing && (
                  <Text style={styles.waveformStatus}>Processing...</Text>
                )}
              </LinearGradient>
            </View>
          )}

          {/* Analysis Progress */}
          {isAnalyzing && analysisStage && <AnalysisProgress stage={analysisStage} />}

          {/* Record Mode */}
          {mode === 'record' && (
            <View style={styles.recordSection}>
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
                <LinearGradient
                  colors={
                    isAnalyzing 
                      ? ['#3b82f6', '#1d4ed8'] 
                      : isRecording 
                        ? ['#ef4444', '#dc2626'] 
                        : ['#22c55e', '#16a34a']
                  }
                  style={styles.recordButtonGradient}
                >
                  {isAnalyzing ? (
                    <ActivityIndicator color="#fff" size="large" />
                  ) : (
                    <Ionicons name={isRecording ? 'stop' : 'mic'} size={40} color="#fff" />
                  )}
                </LinearGradient>
              </TouchableOpacity>
              <Text style={styles.recordLabel}>
                {isAnalyzing ? 'Analyzing...' : isRecording ? 'Tap to Stop' : 'Tap to Record'}
              </Text>
            </View>
          )}

          {/* Upload Mode */}
          {mode === 'upload' && (
            <View style={styles.uploadSection}>
              <TouchableOpacity
                style={[styles.uploadButton, isAnalyzing && styles.uploadButtonDisabled]}
                onPress={pickAudioFile}
                disabled={isAnalyzing}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={isAnalyzing ? ['#3b82f6', '#1d4ed8'] : ['#8b5cf6', '#6d28d9']}
                  style={styles.uploadButtonGradient}
                >
                  {isAnalyzing ? (
                    <ActivityIndicator color="#fff" size="large" />
                  ) : (
                    <>
                      <Ionicons name="folder-open" size={40} color="#fff" />
                      <Text style={styles.uploadButtonText}>Choose Audio File</Text>
                    </>
                  )}
                </LinearGradient>
              </TouchableOpacity>
              
              {selectedFileName && (
                <View style={styles.selectedFile}>
                  <Ionicons name="musical-notes" size={18} color="#8b5cf6" />
                  <Text style={styles.selectedFileName} numberOfLines={1}>{selectedFileName}</Text>
                </View>
              )}
              
              <Text style={styles.uploadHint}>
                Supported: M4A, MP3, WAV, AAC, MP4
              </Text>
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
          {!isRecording && !isAnalyzing && birds.length === 0 && !error && (
            <View style={styles.emptyState}>
              <Text style={styles.emptyEmoji}>{mode === 'record' ? '🎤' : '📁'}</Text>
              <Text style={styles.emptyTitle}>
                {mode === 'record' ? 'Ready to Record' : 'Upload Audio File'}
              </Text>
              <Text style={styles.emptyText}>
                {mode === 'record' 
                  ? 'Tap the microphone button to start recording bird sounds'
                  : 'Choose an audio file from your device to identify birds'}
              </Text>
            </View>
          )}
        </Animated.View>
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradient: { flex: 1 },
  container: { flex: 1 },
  heroSection: { alignItems: 'center', paddingTop: 20, paddingBottom: 12 },
  heroEmoji: { fontSize: 48, marginBottom: 8 },
  heroTitle: { fontSize: 28, fontWeight: '800', color: '#fff', letterSpacing: -0.5 },
  heroSubtitle: { fontSize: 14, color: '#94a3b8', marginTop: 4 },
  modeTabs: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: 4,
  },
  modeTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 10,
    gap: 8,
  },
  modeTabActive: {
    backgroundColor: 'rgba(34, 197, 94, 0.2)',
  },
  modeTabText: { fontSize: 14, color: '#64748b', fontWeight: '600' },
  modeTabTextActive: { color: '#fff' },
  glassCard: {
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    padding: 14,
  },
  tipRow: { flexDirection: 'row', alignItems: 'center' },
  tipText: { color: '#e2e8f0', fontSize: 14, marginLeft: 10, flex: 1 },
  inputSection: { flexDirection: 'row', paddingHorizontal: 16, gap: 12, marginBottom: 16 },
  inputWrapper: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  inputIcon: { paddingLeft: 12 },
  input: { flex: 1, padding: 12, fontSize: 14, color: '#fff' },
  waveformSection: { marginHorizontal: 16, marginBottom: 16 },
  waveformGradient: {
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(34, 197, 94, 0.3)',
  },
  waveformContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 80,
    gap: 4,
  },
  waveformBar: { width: 4, borderRadius: 2, backgroundColor: '#22c55e' },
  waveformDuration: { color: '#fff', fontSize: 40, fontWeight: '200', marginTop: 12, letterSpacing: 2 },
  waveformStatus: { color: '#94a3b8', fontSize: 16, marginTop: 12 },
  progressCard: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  progressStep: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  progressIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(148, 163, 184, 0.2)',
    marginRight: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressIconActive: { backgroundColor: '#22c55e' },
  progressLabel: { fontSize: 14, color: '#64748b', flex: 1 },
  progressLabelActive: { color: '#fff', fontWeight: '500' },
  recordSection: { alignItems: 'center', marginVertical: 20 },
  recordButton: {
    width: 100,
    height: 100,
    borderRadius: 50,
    shadowColor: '#22c55e',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 10,
  },
  recordingButton: { shadowColor: '#ef4444' },
  analyzingButton: { shadowColor: '#3b82f6' },
  recordButtonGradient: {
    width: '100%',
    height: '100%',
    borderRadius: 50,
    alignItems: 'center',
    justifyContent: 'center',
  },
  recordLabel: { color: '#94a3b8', fontSize: 14, marginTop: 12, fontWeight: '500' },
  uploadSection: { alignItems: 'center', marginVertical: 20, paddingHorizontal: 16 },
  uploadButton: {
    width: '100%',
    shadowColor: '#8b5cf6',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 10,
  },
  uploadButtonDisabled: { shadowOpacity: 0.1 },
  uploadButtonGradient: {
    paddingVertical: 32,
    borderRadius: 20,
    alignItems: 'center',
  },
  uploadButtonText: { color: '#fff', fontSize: 18, fontWeight: '600', marginTop: 12 },
  selectedFile: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(139, 92, 246, 0.15)',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
    marginTop: 16,
    gap: 10,
    maxWidth: '100%',
  },
  selectedFileName: { color: '#c4b5fd', fontSize: 14, flex: 1 },
  uploadHint: { color: '#64748b', fontSize: 13, marginTop: 12 },
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
  errorContent: { flex: 1, marginLeft: 12 },
  errorTitle: { color: '#fca5a5', fontSize: 16, fontWeight: '600', marginBottom: 4 },
  errorText: { color: '#fca5a5', fontSize: 14, lineHeight: 20 },
  resultsSection: { marginTop: 8 },
  resultsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    marginBottom: 4,
  },
  resultsHeaderLeft: { flexDirection: 'row', alignItems: 'center' },
  resultsEmoji: { fontSize: 24, marginRight: 8 },
  resultsTitle: { fontSize: 20, fontWeight: '700', color: '#fff' },
  resultsBadge: {
    backgroundColor: 'rgba(34, 197, 94, 0.2)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  resultsBadgeText: { color: '#22c55e', fontSize: 12, fontWeight: '600' },
  resultsModel: { color: '#64748b', fontSize: 12, paddingHorizontal: 16, marginBottom: 12 },
  emptyState: { alignItems: 'center', paddingVertical: 50, paddingHorizontal: 40 },
  emptyEmoji: { fontSize: 64, marginBottom: 16 },
  emptyTitle: { fontSize: 20, fontWeight: '700', color: '#fff', marginBottom: 8 },
  emptyText: { fontSize: 15, color: '#64748b', textAlign: 'center', lineHeight: 22 },
});
