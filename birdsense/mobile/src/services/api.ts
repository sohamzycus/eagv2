/**
 * 🐦 BirdSense Mobile - API Service
 * Developed by Soham
 * 
 * Handles all API communication with the BirdSense backend.
 * Requires authentication via JWT token.
 */

import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import * as SecureStore from 'expo-secure-store';

// Import API endpoints from settings
import { API_ENDPOINTS } from '../context/SettingsContext';

// API Configuration
const API_CONFIG = {
  // AWS App Runner - production (synced with SettingsContext)
  BASE_URL: API_ENDPOINTS.AWS_APP_RUNNER,
  TIMEOUT: 60000, // 60 seconds for identification
};

// Mode type
export type ApiMode = 'online' | 'offline';

// Token storage key
const TOKEN_KEY = 'birdsense_api_token';

// Types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserInfo {
  username: string;
  email?: string;
  full_name?: string;
  is_active: boolean;
}

export interface BirdResult {
  name: string;
  scientific_name?: string;
  confidence: number;
  reason?: string;
  source: string;
  image_url?: string;
  summary?: string;
  habitat?: string;
  diet?: string;
  conservation?: string;
  fun_facts?: string[];
  india_info?: {
    found_in_india: boolean;
    regions?: string;
    local_names?: Record<string, string>;
    best_season?: string;
    notable_locations?: string;
  };
  confidence_factors?: {
    acoustic_match?: string;
    visual_match?: string;
    pattern_match?: string;
    sources?: string;
    enhancement?: string;
    image_quality?: string;
  };
}

// Analysis Trail types
export interface AnalysisStep {
  step: string;
  status: string;
  details?: string;
  duration_ms?: number;
}

export interface AudioFeatures {
  duration: number;
  min_freq: number;
  max_freq: number;
  peak_freq: number;
  freq_range: number;
  pattern: string;
  complexity: string;
  syllables: number;
  rhythm: string;
  quality: string;
}

export interface ImageFeatures {
  size_estimate?: string;
  primary_colors?: string[];
  beak_description?: string;
  distinctive_features?: string[];
  pose?: string;
}

export interface AnalysisTrail {
  pipeline: string;
  steps: AnalysisStep[];
  audio_features?: AudioFeatures;
  image_features?: ImageFeatures;
  sources_used: string[];
  enhancement_applied: boolean;
}

export interface IdentificationResponse {
  success: boolean;
  birds: BirdResult[];
  total_birds: number;
  processing_time_ms: number;
  model_used: string;
  timestamp: string;
  analysis_trail?: AnalysisTrail;
}

export interface HealthStatus {
  status: string;
  version: string;
  birdnet_available: boolean;
  llm_backend: string;
  llm_status: string;
}

// Import offline service
import { offlineService } from './offline';

// Extend AxiosRequestConfig to include retry flags
interface ExtendedAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
  _networkRetry?: boolean;
}

// Create API client
class BirdSenseAPI {
  private client: AxiosInstance;
  private token: string | null = null;
  private mode: ApiMode = 'online';
  private baseUrl: string = API_CONFIG.BASE_URL;

  constructor() {
    const baseURL = API_CONFIG.BASE_URL;
    console.log('🔗 API Base URL:', baseURL);
    
    this.client = axios.create({
      baseURL: baseURL,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth interceptor - always include token if available
    this.client.interceptors.request.use(
      async (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
          console.log('🔑 Request with auth token');
        } else {
          console.log('⚠️ Request without auth token');
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Handle auth and network errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config as ExtendedAxiosRequestConfig;
        
        // Log detailed error
        if (error.response) {
          console.log('❌ API Error:', error.response.status, error.response.data?.detail || error.response.statusText);
        } else if (error.request) {
          // Network error - could be emulator issue, timeout, etc.
          console.log('❌ Network Error: No response received');
          console.log('💡 If on emulator, check: 1) Internet permission 2) WiFi enabled 3) Try "Cold Boot" emulator');
          
          // Retry once on network error
          if (!originalRequest._networkRetry) {
            console.log('🔄 Retrying request...');
            originalRequest._networkRetry = true;
            await new Promise(resolve => setTimeout(resolve, 1000));
            return this.client(originalRequest);
          }
        } else {
          console.log('❌ Request Error:', error.message);
        }

        // If 401, token is invalid/expired
        if (error.response?.status === 401 && !originalRequest._retry) {
          console.log('🔄 Token invalid, clearing...');
          await this.clearToken();
        }
        
        return Promise.reject(error);
      }
    );

    // Load any existing token
    this.loadToken();
  }

  // Mode management
  setMode(mode: ApiMode) {
    this.mode = mode;
    console.log(`API mode set to: ${mode}`);
  }

  getMode(): ApiMode {
    return this.mode;
  }

  setBaseUrl(url: string) {
    this.baseUrl = url;
    this.client.defaults.baseURL = url;
    console.log(`API base URL set to: ${url}`);
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  // Token management
  private async loadToken() {
    try {
      const token = await SecureStore.getItemAsync(TOKEN_KEY);
      if (token) {
        this.token = token;
        console.log('✅ Loaded stored token');
      }
    } catch (error) {
      console.log('Error loading token:', error);
    }
  }

  private async saveToken(token: string) {
    try {
      await SecureStore.setItemAsync(TOKEN_KEY, token);
      this.token = token;
      console.log('✅ Token saved');
    } catch (error) {
      console.log('Error saving token:', error);
    }
  }

  async clearToken() {
    try {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
      this.token = null;
      console.log('🗑️ Token cleared');
    } catch (error) {
      console.log('Error clearing token:', error);
    }
  }

  isAuthenticated(): boolean {
    return this.token !== null;
  }

  getToken(): string | null {
    return this.token;
  }

  // Health check (no auth required)
  async getHealth(): Promise<HealthStatus> {
    const response = await this.client.get<HealthStatus>('/health');
    return response.data;
  }

  // Authentication
  async login(credentials: LoginCredentials): Promise<AuthToken> {
    console.log('🔐 Logging in as:', credentials.username);
    const response = await this.client.post<AuthToken>('/auth/login', credentials);
    await this.saveToken(response.data.access_token);
    return response.data;
  }

  async logout() {
    await this.clearToken();
  }

  async getCurrentUser(): Promise<UserInfo> {
    const response = await this.client.get<UserInfo>('/auth/me');
    return response.data;
  }

  async refreshToken(): Promise<AuthToken> {
    const response = await this.client.post<AuthToken>('/auth/refresh');
    await this.saveToken(response.data.access_token);
    return response.data;
  }

  // Check if we're authenticated before API calls
  private checkAuth() {
    if (!this.token) {
      throw new Error('Not authenticated. Please login first.');
    }
  }

  // Bird Identification - Audio
  async identifyAudio(
    audioBase64: string,
    sampleRate: number = 44100,
    location?: string,
    month?: string
  ): Promise<IdentificationResponse> {
    if (this.mode === 'offline') {
      throw new Error('Base64 audio not supported in offline mode.');
    }

    this.checkAuth();

    const response = await this.client.post<IdentificationResponse>('/identify/audio/base64', {
      audio_base64: audioBase64,
      sample_rate: sampleRate,
      location,
      month,
    });
    return response.data;
  }

  async identifyAudioFile(
    audioUri: string,
    location?: string,
    month?: string
  ): Promise<IdentificationResponse> {
    if (this.mode === 'offline') {
      return offlineService.identifyAudio(audioUri, location, month);
    }

    this.checkAuth();

    // Detect file type from URI
    const uriLower = audioUri.toLowerCase();
    let mimeType = 'audio/wav';
    let fileName = 'recording.wav';
    
    if (uriLower.includes('.m4a') || uriLower.includes('.aac')) {
      mimeType = 'audio/m4a';
      fileName = 'recording.m4a';
    } else if (uriLower.includes('.mp3')) {
      mimeType = 'audio/mpeg';
      fileName = 'recording.mp3';
    } else if (uriLower.includes('.mp4')) {
      mimeType = 'audio/mp4';
      fileName = 'recording.mp4';
    } else if (uriLower.includes('.ogg')) {
      mimeType = 'audio/ogg';
      fileName = 'recording.ogg';
    } else if (uriLower.includes('.flac')) {
      mimeType = 'audio/flac';
      fileName = 'recording.flac';
    }

    console.log(`📤 Audio upload: ${mimeType}, file: ${fileName}`);

    const formData = new FormData();
    formData.append('audio_file', {
      uri: audioUri,
      type: mimeType,
      name: fileName,
    } as any);
    if (location) formData.append('location', location);
    if (month) formData.append('month', month);

    const response = await this.client.post<IdentificationResponse>('/identify/audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2 minutes for large audio files
    });
    return response.data;
  }

  // Bird Identification - Image
  async identifyImage(
    imageBase64: string,
    location?: string
  ): Promise<IdentificationResponse> {
    if (this.mode === 'offline') {
      throw new Error('Base64 image not supported in offline mode.');
    }

    this.checkAuth();

    const response = await this.client.post<IdentificationResponse>('/identify/image/base64', {
      image_base64: imageBase64,
      location,
    });
    return response.data;
  }

  async identifyImageFile(
    imageUri: string,
    location?: string
  ): Promise<IdentificationResponse> {
    if (this.mode === 'offline') {
      return offlineService.identifyImage(imageUri, location);
    }

    this.checkAuth();

    const formData = new FormData();
    formData.append('image_file', {
      uri: imageUri,
      type: 'image/jpeg',
      name: 'photo.jpg',
    } as any);
    if (location) formData.append('location', location);

    const response = await this.client.post<IdentificationResponse>('/identify/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Bird Identification - Description
  async identifyDescription(
    description: string,
    location?: string
  ): Promise<IdentificationResponse> {
    if (this.mode === 'offline') {
      return offlineService.identifyDescription(description, location);
    }

    this.checkAuth();

    const response = await this.client.post<IdentificationResponse>('/identify/description', {
      description,
      location,
    });
    return response.data;
  }

  // Live Audio Streaming - Send 3-second chunks
  async identifyLiveAudioChunk(
    audioUri: string,
    chunkIndex: number,
    location?: string,
    month?: string
  ): Promise<IdentificationResponse> {
    if (this.mode === 'offline') {
      return offlineService.identifyAudio(audioUri, location, month);
    }

    this.checkAuth();

    // Detect file type from URI
    const uriLower = audioUri.toLowerCase();
    let mimeType = 'audio/wav';
    let fileName = `chunk_${chunkIndex}.wav`;
    
    if (uriLower.includes('.m4a') || uriLower.includes('.aac')) {
      mimeType = 'audio/m4a';
      fileName = `chunk_${chunkIndex}.m4a`;
    } else if (uriLower.includes('.mp3')) {
      mimeType = 'audio/mpeg';
      fileName = `chunk_${chunkIndex}.mp3`;
    }

    console.log(`🎵 Live chunk #${chunkIndex}: ${mimeType}`);

    const formData = new FormData();
    formData.append('audio_file', {
      uri: audioUri,
      type: mimeType,
      name: fileName,
    } as any);
    if (location) formData.append('location', location);
    if (month) formData.append('month', month);

    const response = await this.client.post<IdentificationResponse>('/identify/audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 30000, // 30 seconds for quick chunks
    });
    return response.data;
  }
}

// Export singleton instance
export const api = new BirdSenseAPI();
export default api;
