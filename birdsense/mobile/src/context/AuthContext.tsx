/**
 * 🐦 BirdSense Mobile - Auth Context
 * Developed by Soham
 * 
 * Authentication flow:
 * 1. Biometric/PIN unlock on device
 * 2. Auto-authenticate with backend API
 * 3. Store JWT token for API calls
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import * as LocalAuthentication from 'expo-local-authentication';
import api from '../services/api';

// Storage keys
const SESSION_KEY = 'birdsense_session';
const CREDENTIALS_KEY = 'birdsense_credentials';

// Default demo credentials for API
const DEFAULT_API_CREDENTIALS = {
  username: 'demo',
  password: 'demo123'
};

export interface UserInfo {
  username: string;
  name: string;
  email?: string;
  is_active: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

interface AuthContextType {
  user: UserInfo | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isApiAuthenticated: boolean;
  biometricType: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  loginWithBiometric: () => Promise<void>;
  loginAsDemo: () => Promise<void>;
  logout: () => Promise<void>;
  authenticateApi: () => Promise<boolean>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isApiAuthenticated, setIsApiAuthenticated] = useState(false);
  const [biometricType, setBiometricType] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      // Check biometric availability
      const biometricAvailable = await LocalAuthentication.hasHardwareAsync();
      if (biometricAvailable) {
        const supportedTypes = await LocalAuthentication.supportedAuthenticationTypesAsync();
        if (supportedTypes.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
          setBiometricType('Face ID');
        } else if (supportedTypes.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
          setBiometricType('Fingerprint');
        } else {
          setBiometricType('PIN');
        }
      }

      // Check for saved session - but require re-auth for API
      const savedSession = await SecureStore.getItemAsync(SESSION_KEY);
      if (savedSession) {
        const sessionUser = JSON.parse(savedSession);
        console.log('📋 Found saved session for:', sessionUser.username);
        
        // Try to authenticate with API using saved credentials
        const apiSuccess = await authenticateApiInternal();
        
        if (apiSuccess) {
          setUser(sessionUser);
          console.log('✅ Session restored with API auth');
        } else {
          // Clear session if API auth fails - require fresh login
          console.log('⚠️ API auth failed, clearing session');
          await SecureStore.deleteItemAsync(SESSION_KEY);
        }
      }
    } catch (err) {
      console.log('Session restore error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Authenticate with backend API
  const authenticateApiInternal = async (): Promise<boolean> => {
    try {
      // Get stored credentials or use default
      let credentials = DEFAULT_API_CREDENTIALS;
      const savedCreds = await SecureStore.getItemAsync(CREDENTIALS_KEY);
      if (savedCreds) {
        credentials = JSON.parse(savedCreds);
      }

      console.log('🔐 Authenticating with API...');
      await api.login(credentials);
      setIsApiAuthenticated(true);
      console.log('✅ API authenticated successfully');
      return true;
    } catch (err: any) {
      console.log('❌ API authentication failed:', err?.message || err);
      setIsApiAuthenticated(false);
      return false;
    }
  };

  const authenticateApi = async (): Promise<boolean> => {
    return await authenticateApiInternal();
  };

  // Login with username/password
  const login = async (credentials: LoginCredentials) => {
    setError(null);
    setIsLoading(true);

    try {
      // Authenticate with API first
      console.log('🔐 Authenticating with API...');
      const tokenResponse = await api.login(credentials);
      
      if (!tokenResponse?.access_token) {
        throw new Error('Failed to get authentication token');
      }

      setIsApiAuthenticated(true);

      // Save credentials for future API auth
      await SecureStore.setItemAsync(CREDENTIALS_KEY, JSON.stringify(credentials));

      // Create user info
      const userInfo: UserInfo = {
        username: credentials.username,
        name: credentials.username.charAt(0).toUpperCase() + credentials.username.slice(1),
        is_active: true,
      };

      await SecureStore.setItemAsync(SESSION_KEY, JSON.stringify(userInfo));
      setUser(userInfo);
      console.log('✅ Logged in as:', credentials.username);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Login failed';
      setError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // Login with biometric (uses stored/default credentials)
  const loginWithBiometric = async () => {
    setError(null);
    setIsLoading(true);

    try {
      // Prompt for biometric
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Authenticate to access BirdSense',
        fallbackLabel: 'Use PIN',
        cancelLabel: 'Cancel',
        disableDeviceFallback: false,
      });

      if (!result.success) {
        throw new Error(result.error || 'Biometric authentication failed');
      }

      console.log('✅ Biometric verified');

      // Get stored credentials or use default demo
      let credentials = DEFAULT_API_CREDENTIALS;
      const savedCreds = await SecureStore.getItemAsync(CREDENTIALS_KEY);
      if (savedCreds) {
        credentials = JSON.parse(savedCreds);
      }

      // Authenticate with API
      console.log('🔐 Authenticating with API...');
      const tokenResponse = await api.login(credentials);
      
      if (!tokenResponse?.access_token) {
        throw new Error('Failed to get authentication token');
      }

      setIsApiAuthenticated(true);

      // Create user info
      const userInfo: UserInfo = {
        username: credentials.username,
        name: credentials.username.charAt(0).toUpperCase() + credentials.username.slice(1),
        is_active: true,
      };

      await SecureStore.setItemAsync(SESSION_KEY, JSON.stringify(userInfo));
      setUser(userInfo);
      console.log('✅ Logged in via biometric as:', credentials.username);
    } catch (err: any) {
      const msg = err?.message || 'Authentication failed';
      setError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  // Quick demo login
  const loginAsDemo = async () => {
    setError(null);
    setIsLoading(true);

    try {
      // Authenticate with API using demo credentials
      console.log('🔐 Authenticating as demo user...');
      const tokenResponse = await api.login(DEFAULT_API_CREDENTIALS);
      
      if (!tokenResponse?.access_token) {
        throw new Error('Failed to get authentication token');
      }

      setIsApiAuthenticated(true);

      // Save demo credentials
      await SecureStore.setItemAsync(CREDENTIALS_KEY, JSON.stringify(DEFAULT_API_CREDENTIALS));

      const userInfo: UserInfo = {
        username: 'demo',
        name: 'Demo User',
        is_active: true,
      };

      await SecureStore.setItemAsync(SESSION_KEY, JSON.stringify(userInfo));
      setUser(userInfo);
      console.log('✅ Logged in as demo user');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Demo login failed';
      setError(msg);
      throw new Error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    await SecureStore.deleteItemAsync(SESSION_KEY);
    await api.logout();
    setUser(null);
    setIsApiAuthenticated(false);
    console.log('✅ Logged out');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        isApiAuthenticated,
        biometricType,
        login,
        loginWithBiometric,
        loginAsDemo,
        logout,
        authenticateApi,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
