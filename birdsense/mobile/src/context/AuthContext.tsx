/**
 * 🐦 BirdSense Mobile - Auth Context
 * Developed by Soham
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api, { UserInfo, LoginCredentials } from '../services/api';

interface AuthContextType {
  user: UserInfo | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      if (api.isAuthenticated()) {
        const userInfo = await api.getCurrentUser();
        setUser(userInfo);
      }
    } catch (err) {
      // Token might be expired
      await api.clearToken();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      await api.login(credentials);
      // Set a basic user object after successful login
      setUser({
        username: credentials.username,
        is_active: true,
      });
      // Optionally fetch full user info in background
      api.getCurrentUser().then(setUser).catch(() => {});
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
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

