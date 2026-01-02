/**
 * 🐦 BirdSense Mobile - Settings Context
 * Developed by Soham
 * 
 * Manages app-wide settings including online/offline mode.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';

export type AppMode = 'online' | 'offline';

interface SettingsContextType {
  mode: AppMode;
  setMode: (mode: AppMode) => Promise<void>;
  apiBaseUrl: string;
  setApiBaseUrl: (url: string) => Promise<void>;
  isOfflineModelReady: boolean;
  offlineModelStatus: string;
}

const SETTINGS_KEYS = {
  MODE: 'birdsense_mode',
  API_URL: 'birdsense_api_url',
};

// Available API endpoints
export const API_ENDPOINTS = {
  AWS_APP_RUNNER: 'https://cqxapziyi2.ap-south-1.awsapprunner.com',
  GCP_CLOUD_RUN: 'https://birdsense-api-790428686498.asia-south1.run.app',
  LOCAL: 'http://localhost:8000',
  // Special IP for Android Emulator to access host machine
  EMULATOR_LOCAL: 'http://10.0.2.2:8000',
  // For testing on local network, set your computer's IP here
  LOCAL_NETWORK: 'http://192.168.1.21:8000',
};

// Default API URL - Use AWS App Runner for production
const DEFAULT_API_URL = API_ENDPOINTS.AWS_APP_RUNNER;

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<AppMode>('online');
  const [apiBaseUrl, setApiBaseUrlState] = useState(DEFAULT_API_URL);
  const [isOfflineModelReady, setIsOfflineModelReady] = useState(false);
  const [offlineModelStatus, setOfflineModelStatus] = useState('Not loaded');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const savedMode = await SecureStore.getItemAsync(SETTINGS_KEYS.MODE);
      if (savedMode === 'online' || savedMode === 'offline') {
        setModeState(savedMode);
      }

      const savedUrl = await SecureStore.getItemAsync(SETTINGS_KEYS.API_URL);
      if (savedUrl) {
        setApiBaseUrlState(savedUrl);
      }

      // Check offline model status
      checkOfflineModelStatus();
    } catch (error) {
      console.log('Error loading settings:', error);
    }
  };

  const checkOfflineModelStatus = async () => {
    // In a real implementation, this would check if TensorFlow Lite models are downloaded
    // For now, we'll simulate the check
    try {
      // Check if BirdNET TFLite model exists
      // This would use expo-file-system to check for model files
      setOfflineModelStatus('Available (BirdNET Lite)');
      setIsOfflineModelReady(true);
    } catch (error) {
      setOfflineModelStatus('Not available - Download required');
      setIsOfflineModelReady(false);
    }
  };

  const setMode = async (newMode: AppMode) => {
    try {
      await SecureStore.setItemAsync(SETTINGS_KEYS.MODE, newMode);
      setModeState(newMode);
    } catch (error) {
      console.log('Error saving mode:', error);
    }
  };

  const setApiBaseUrl = async (url: string) => {
    try {
      await SecureStore.setItemAsync(SETTINGS_KEYS.API_URL, url);
      setApiBaseUrlState(url);
    } catch (error) {
      console.log('Error saving API URL:', error);
    }
  };

  return (
    <SettingsContext.Provider
      value={{
        mode,
        setMode,
        apiBaseUrl,
        setApiBaseUrl,
        isOfflineModelReady,
        offlineModelStatus,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}

