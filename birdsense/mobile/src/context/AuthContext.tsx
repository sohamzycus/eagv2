/**
 * 🐦 BirdSense Mobile - Auth Context
 * Developed by Soham
 * 
 * LOCAL AUTHENTICATION - No API required
 * Just validates credentials locally and stores session
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';

// Local credentials - no API needed
const VALID_USERS = [
  { username: 'demo', password: 'demo123', name: 'Demo User' },
  { username: 'soham', password: 'birdsense2024', name: 'Soham' },
  { username: 'mazycus', password: 'ZycusMerlinAssist@2024', name: 'Mazycus Admin' },
  { username: 'guest', password: 'guest', name: 'Guest' },
];

// Storage key
const SESSION_KEY = 'birdsense_session';

export interface UserInfo {
  username: string;
  name: string;
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
  login: (credentials: LoginCredentials) => Promise<void>;
  loginAsGuest: () => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      // Check for saved session
      const savedSession = await SecureStore.getItemAsync(SESSION_KEY);
      if (savedSession) {
        const sessionUser = JSON.parse(savedSession);
        setUser(sessionUser);
        console.log('✅ Restored session for:', sessionUser.username);
      } else {
        // Auto-login as guest for seamless experience
        await loginAsGuestInternal();
      }
    } catch (err) {
      console.log('Session restore error:', err);
      // Auto-login as guest on any error
      await loginAsGuestInternal();
    } finally {
      setIsLoading(false);
    }
  };

  const loginAsGuestInternal = async () => {
    const guestUser: UserInfo = {
      username: 'guest',
      name: 'Guest User',
      is_active: true,
    };
    await SecureStore.setItemAsync(SESSION_KEY, JSON.stringify(guestUser));
    setUser(guestUser);
    console.log('✅ Auto-logged in as guest');
  };

  const login = async (credentials: LoginCredentials) => {
    setError(null);
    
    // Validate locally
    const validUser = VALID_USERS.find(
      u => u.username.toLowerCase() === credentials.username.toLowerCase() && 
           u.password === credentials.password
    );

    if (!validUser) {
      const msg = 'Invalid username or password';
      setError(msg);
      throw new Error(msg);
    }

    const userInfo: UserInfo = {
      username: validUser.username,
      name: validUser.name,
      is_active: true,
    };

    await SecureStore.setItemAsync(SESSION_KEY, JSON.stringify(userInfo));
    setUser(userInfo);
    console.log('✅ Logged in as:', validUser.username);
  };

  const loginAsGuest = async () => {
    await loginAsGuestInternal();
  };

  const logout = async () => {
    await SecureStore.deleteItemAsync(SESSION_KEY);
    setUser(null);
    console.log('✅ Logged out');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
        loginAsGuest,
        logout,
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
