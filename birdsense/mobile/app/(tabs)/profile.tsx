/**
 * 🐦 BirdSense Mobile - Profile Tab
 * Developed by Soham
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
  Switch,
  TextInput,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '../../src/context/AuthContext';
import { useSettings, API_ENDPOINTS } from '../../src/context/SettingsContext';
import api, { HealthStatus } from '../../src/services/api';

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const { user, logout } = useAuth();
  const { mode, setMode, apiBaseUrl, setApiBaseUrl } = useSettings();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [showApiSelector, setShowApiSelector] = useState(false);
  const [customApiUrl, setCustomApiUrl] = useState('');

  useEffect(() => {
    if (mode === 'online') {
      checkHealth();
    }
  }, [mode, apiBaseUrl]);

  const checkHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const status = await api.getHealth();
      setHealth(status);
    } catch (error: any) {
      console.log('Health check failed:', error?.message || error);
      setHealth(null);
    } finally {
      setIsCheckingHealth(false);
    }
  };

  const selectApiEndpoint = async (name: string, url: string) => {
    await setApiBaseUrl(url);
    api.setBaseUrl(url);
    setShowApiSelector(false);
    checkHealth();
  };

  const setCustomApi = async () => {
    if (customApiUrl.trim()) {
      await selectApiEndpoint('Custom', customApiUrl.trim());
      setCustomApiUrl('');
    }
  };

  const getEndpointName = (url: string): string => {
    if (url === API_ENDPOINTS.AWS_APP_RUNNER) return 'AWS App Runner';
    if (url === API_ENDPOINTS.GCP_CLOUD_RUN) return 'GCP Cloud Run';
    if (url === API_ENDPOINTS.LOCAL) return 'Local';
    if (url === API_ENDPOINTS.EMULATOR_LOCAL) return 'Emulator (10.0.2.2)';
    if (url.includes('localhost') || url.includes('192.168') || url.includes('10.0.2.2')) return 'Local Network';
    return 'Custom';
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/login');
          },
        },
      ]
    );
  };

  const handleModeToggle = async (value: boolean) => {
    const newMode = value ? 'online' : 'offline';
    await setMode(newMode);
    api.setMode(newMode);
    
    if (newMode === 'online') {
      checkHealth();
    }
  };

  return (
    <ScrollView 
      style={styles.container}
      contentContainerStyle={{ paddingBottom: insets.bottom + 20 }}
    >
      {/* Mode Toggle */}
      <View style={styles.card}>
        <View style={styles.modeRow}>
          <Ionicons 
            name={mode === 'online' ? 'cloud' : 'cloud-offline'} 
            size={28} 
            color={mode === 'online' ? '#22c55e' : '#f59e0b'} 
          />
          <View style={styles.modeInfo}>
            <Text style={styles.modeTitle}>
              {mode === 'online' ? '🌐 Online Mode' : '📴 Offline Mode'}
            </Text>
            <Text style={styles.modeDescription}>
              {mode === 'online' 
                ? 'Cloud API (BirdNET + GPT-4o)' 
                : 'On-device models'}
            </Text>
          </View>
          <Switch
            value={mode === 'online'}
            onValueChange={handleModeToggle}
            trackColor={{ false: '#fcd34d', true: '#86efac' }}
            thumbColor={mode === 'online' ? '#22c55e' : '#f59e0b'}
          />
        </View>
      </View>

      {/* User Info */}
      <View style={styles.userCard}>
        <View style={styles.avatarContainer}>
          <Text style={styles.avatarEmoji}>👤</Text>
        </View>
        <Text style={styles.userName}>{user?.full_name || user?.username || 'User'}</Text>
        <Text style={styles.userEmail}>{user?.email || ''}</Text>
        <View style={styles.statusBadge}>
          <View style={styles.statusDot} />
          <Text style={styles.statusText}>Active</Text>
        </View>
      </View>

      {/* API Status */}
      {mode === 'online' && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🔌 API Configuration</Text>
          <View style={styles.card}>
            {/* Current Endpoint */}
            <TouchableOpacity 
              style={styles.apiSelectorButton}
              onPress={() => setShowApiSelector(!showApiSelector)}
            >
              <View style={styles.apiSelectorInfo}>
                <Text style={styles.apiSelectorLabel}>Active Endpoint</Text>
                <Text style={styles.apiSelectorValue}>{getEndpointName(apiBaseUrl)}</Text>
                <Text style={styles.apiSelectorUrl} numberOfLines={1}>{apiBaseUrl}</Text>
              </View>
              <Ionicons 
                name={showApiSelector ? 'chevron-up' : 'chevron-down'} 
                size={24} 
                color="#64748b" 
              />
            </TouchableOpacity>

            {/* Endpoint Selector */}
            {showApiSelector && (
              <View style={styles.apiEndpointList}>
                <Text style={styles.apiEndpointHeader}>Select API Endpoint</Text>
                
                <TouchableOpacity 
                  style={[
                    styles.apiEndpointOption,
                    apiBaseUrl === API_ENDPOINTS.AWS_APP_RUNNER && styles.apiEndpointActive
                  ]}
                  onPress={() => selectApiEndpoint('AWS', API_ENDPOINTS.AWS_APP_RUNNER)}
                >
                  <Ionicons name="cloud" size={20} color="#f97316" />
                  <View style={styles.apiEndpointTextContainer}>
                    <Text style={styles.apiEndpointName}>AWS App Runner</Text>
                    <Text style={styles.apiEndpointUrlSmall}>{API_ENDPOINTS.AWS_APP_RUNNER}</Text>
                  </View>
                  {apiBaseUrl === API_ENDPOINTS.AWS_APP_RUNNER && (
                    <Ionicons name="checkmark-circle" size={20} color="#22c55e" />
                  )}
                </TouchableOpacity>

                <TouchableOpacity 
                  style={[
                    styles.apiEndpointOption,
                    apiBaseUrl === API_ENDPOINTS.GCP_CLOUD_RUN && styles.apiEndpointActive
                  ]}
                  onPress={() => selectApiEndpoint('GCP', API_ENDPOINTS.GCP_CLOUD_RUN)}
                >
                  <Ionicons name="cloud" size={20} color="#4285f4" />
                  <View style={styles.apiEndpointTextContainer}>
                    <Text style={styles.apiEndpointName}>GCP Cloud Run</Text>
                    <Text style={styles.apiEndpointUrlSmall}>{API_ENDPOINTS.GCP_CLOUD_RUN}</Text>
                  </View>
                  {apiBaseUrl === API_ENDPOINTS.GCP_CLOUD_RUN && (
                    <Ionicons name="checkmark-circle" size={20} color="#22c55e" />
                  )}
                </TouchableOpacity>

                <TouchableOpacity 
                  style={[
                    styles.apiEndpointOption,
                    apiBaseUrl === API_ENDPOINTS.EMULATOR_LOCAL && styles.apiEndpointActive
                  ]}
                  onPress={() => selectApiEndpoint('Emulator', API_ENDPOINTS.EMULATOR_LOCAL)}
                >
                  <Ionicons name="phone-portrait" size={20} color="#22c55e" />
                  <View style={styles.apiEndpointTextContainer}>
                    <Text style={styles.apiEndpointName}>Emulator Local (10.0.2.2)</Text>
                    <Text style={styles.apiEndpointUrlSmall}>{API_ENDPOINTS.EMULATOR_LOCAL}</Text>
                  </View>
                  {apiBaseUrl === API_ENDPOINTS.EMULATOR_LOCAL && (
                    <Ionicons name="checkmark-circle" size={20} color="#22c55e" />
                  )}
                </TouchableOpacity>

                <TouchableOpacity 
                  style={[
                    styles.apiEndpointOption,
                    apiBaseUrl === API_ENDPOINTS.LOCAL && styles.apiEndpointActive
                  ]}
                  onPress={() => selectApiEndpoint('Local', API_ENDPOINTS.LOCAL)}
                >
                  <Ionicons name="desktop" size={20} color="#64748b" />
                  <View style={styles.apiEndpointTextContainer}>
                    <Text style={styles.apiEndpointName}>Local (localhost)</Text>
                    <Text style={styles.apiEndpointUrlSmall}>{API_ENDPOINTS.LOCAL}</Text>
                  </View>
                  {apiBaseUrl === API_ENDPOINTS.LOCAL && (
                    <Ionicons name="checkmark-circle" size={20} color="#22c55e" />
                  )}
                </TouchableOpacity>

                {/* Custom URL Input */}
                <View style={styles.customApiContainer}>
                  <Text style={styles.customApiLabel}>Custom URL:</Text>
                  <View style={styles.customApiInputRow}>
                    <TextInput
                      style={styles.customApiInput}
                      placeholder="http://192.168.x.x:8000"
                      value={customApiUrl}
                      onChangeText={setCustomApiUrl}
                      autoCapitalize="none"
                      autoCorrect={false}
                      keyboardType="url"
                    />
                    <TouchableOpacity 
                      style={styles.customApiButton}
                      onPress={setCustomApi}
                    >
                      <Text style={styles.customApiButtonText}>Set</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              </View>
            )}

            {/* Connection Status */}
            <View style={styles.divider} />
            {isCheckingHealth ? (
              <View style={styles.healthCheckingContainer}>
                <ActivityIndicator color="#3b82f6" size="small" />
                <Text style={styles.healthCheckingText}>Checking connection...</Text>
              </View>
            ) : health ? (
              <>
                <StatusRow label="Status" value={health.status.toUpperCase()} color="#22c55e" />
                <StatusRow label="Version" value={health.version} />
                <StatusRow 
                  label="BirdNET" 
                  value={health.birdnet_available ? '✅ Available' : '❌ Unavailable'} 
                  color={health.birdnet_available ? '#22c55e' : '#ef4444'}
                />
                <StatusRow label="LLM" value={health.llm_backend || 'Not configured'} />
                <StatusRow 
                  label="LLM Status" 
                  value={health.llm_status} 
                  color={health.llm_status === 'connected' ? '#22c55e' : '#f59e0b'}
                />
              </>
            ) : (
              <View style={styles.errorContainer}>
                <Ionicons name="warning" size={24} color="#ef4444" />
                <Text style={styles.errorText}>Unable to connect to API</Text>
                <Text style={styles.errorHint}>Check network or try another endpoint</Text>
              </View>
            )}
            <TouchableOpacity style={styles.refreshButton} onPress={checkHealth}>
              <Ionicons name="refresh" size={18} color="#3b82f6" />
              <Text style={styles.refreshText}>Test Connection</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* About */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ℹ️ About</Text>
        <View style={styles.card}>
          <Text style={styles.aboutTitle}>🐦 BirdSense Mobile</Text>
          <Text style={styles.aboutText}>AI-Powered Bird Identification</Text>
          <Text style={styles.aboutVersion}>Version 1.0.0</Text>
          <View style={styles.divider} />
          <Text style={styles.aboutDeveloper}>Developed by Soham</Text>
        </View>
      </View>

      {/* Features */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>✨ Features</Text>
        <View style={styles.card}>
          <FeatureRow icon="mic" color="#22c55e" text="Audio - BirdNET + SAM-Audio" />
          <FeatureRow icon="camera" color="#3b82f6" text="Image - Vision AI Analysis" />
          <FeatureRow icon="document-text" color="#f59e0b" text="Description - Natural Language" />
          <FeatureRow icon="flag" color="#f97316" text="India-Specific Information" />
        </View>
      </View>

      {/* Logout Button */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Ionicons name="log-out" size={20} color="#ef4444" />
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

// Helper Components
function StatusRow({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <View style={styles.statusRow}>
      <Text style={styles.statusLabel}>{label}</Text>
      <Text style={[styles.statusValue, color && { color }]}>{value}</Text>
    </View>
  );
}

function FeatureRow({ icon, color, text }: { icon: string; color: string; text: string }) {
  return (
    <View style={styles.featureRow}>
      <Ionicons name={icon as any} size={20} color={color} />
      <Text style={styles.featureText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  card: {
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginTop: 16,
    padding: 16,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  modeRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  modeInfo: {
    flex: 1,
    marginLeft: 12,
  },
  modeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  modeDescription: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 2,
  },
  userCard: {
    backgroundColor: '#1a472a',
    marginHorizontal: 16,
    marginTop: 16,
    padding: 24,
    borderRadius: 16,
    alignItems: 'center',
  },
  avatarContainer: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  avatarEmoji: {
    fontSize: 36,
  },
  userName: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  userEmail: {
    fontSize: 14,
    color: '#86efac',
    marginTop: 4,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.15)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    marginTop: 12,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#22c55e',
    marginRight: 6,
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '500',
  },
  section: {
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#475569',
    marginLeft: 16,
    marginBottom: 8,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  statusLabel: {
    color: '#64748b',
    fontSize: 14,
  },
  statusValue: {
    color: '#1e293b',
    fontSize: 14,
    fontWeight: '500',
  },
  errorText: {
    color: '#ef4444',
    textAlign: 'center',
    paddingVertical: 20,
  },
  refreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    paddingVertical: 8,
  },
  refreshText: {
    color: '#3b82f6',
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '500',
  },
  aboutTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1e293b',
    textAlign: 'center',
  },
  aboutText: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
    marginTop: 4,
  },
  aboutVersion: {
    fontSize: 12,
    color: '#94a3b8',
    textAlign: 'center',
    marginTop: 4,
  },
  divider: {
    height: 1,
    backgroundColor: '#f1f5f9',
    marginVertical: 12,
  },
  aboutDeveloper: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e293b',
    textAlign: 'center',
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    gap: 12,
  },
  featureText: {
    fontSize: 14,
    color: '#475569',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fef2f2',
    marginHorizontal: 16,
    marginTop: 24,
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  logoutText: {
    color: '#ef4444',
    fontSize: 16,
    fontWeight: '600',
  },
  // API Selector Styles
  apiSelectorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  apiSelectorInfo: {
    flex: 1,
  },
  apiSelectorLabel: {
    fontSize: 12,
    color: '#94a3b8',
    marginBottom: 2,
  },
  apiSelectorValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  apiSelectorUrl: {
    fontSize: 11,
    color: '#64748b',
    marginTop: 2,
  },
  apiEndpointList: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f1f5f9',
  },
  apiEndpointHeader: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748b',
    marginBottom: 12,
  },
  apiEndpointOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginBottom: 8,
    backgroundColor: '#f8fafc',
  },
  apiEndpointActive: {
    backgroundColor: '#ecfdf5',
    borderWidth: 1,
    borderColor: '#86efac',
  },
  apiEndpointTextContainer: {
    flex: 1,
    marginLeft: 10,
  },
  apiEndpointName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1e293b',
  },
  apiEndpointUrlSmall: {
    fontSize: 10,
    color: '#94a3b8',
    marginTop: 2,
  },
  customApiContainer: {
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f1f5f9',
  },
  customApiLabel: {
    fontSize: 12,
    color: '#64748b',
    marginBottom: 8,
  },
  customApiInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  customApiInput: {
    flex: 1,
    backgroundColor: '#f1f5f9',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#1e293b',
  },
  customApiButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  customApiButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  healthCheckingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    gap: 8,
  },
  healthCheckingText: {
    color: '#64748b',
    fontSize: 14,
  },
  errorContainer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  errorHint: {
    color: '#94a3b8',
    fontSize: 12,
    marginTop: 4,
  },
});
