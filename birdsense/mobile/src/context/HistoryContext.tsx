/**
 * 📚 BirdSense History Context
 * Shared recording history across Audio, Image, and Description tabs
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { BirdResult } from '../services/api';

const HISTORY_STORAGE_KEY = 'birdsense_recording_history_v2';

// Recording session type for history
export interface RecordingSession {
  id: string;
  date: string;
  duration: number;
  location: string;
  birds: BirdResult[];
  chunksProcessed: number;
  mode: 'audio-live' | 'audio-record' | 'audio-upload' | 'image' | 'description';
  source?: string; // For image: image name, for description: the query
}

interface HistoryContextType {
  history: RecordingSession[];
  addSession: (session: Omit<RecordingSession, 'id' | 'date'>) => Promise<void>;
  clearHistory: () => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
  getSessionById: (id: string) => RecordingSession | undefined;
}

const HistoryContext = createContext<HistoryContextType | undefined>(undefined);

export function HistoryProvider({ children }: { children: ReactNode }) {
  const [history, setHistory] = useState<RecordingSession[]>([]);

  // Load history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const stored = await SecureStore.getItemAsync(HISTORY_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setHistory(parsed);
        console.log(`📚 Loaded ${parsed.length} sessions from history`);
      }
    } catch (error) {
      console.log('Error loading history:', error);
    }
  };

  const saveHistory = async (newHistory: RecordingSession[]) => {
    try {
      await SecureStore.setItemAsync(HISTORY_STORAGE_KEY, JSON.stringify(newHistory));
      setHistory(newHistory);
    } catch (error) {
      console.log('Error saving history:', error);
    }
  };

  const addSession = async (sessionData: Omit<RecordingSession, 'id' | 'date'>) => {
    const session: RecordingSession = {
      ...sessionData,
      id: Date.now().toString(),
      date: new Date().toISOString(),
    };
    
    const newHistory = [session, ...history].slice(0, 100); // Keep last 100 sessions
    await saveHistory(newHistory);
    console.log(`💾 Saved session: ${session.mode} with ${session.birds.length} birds`);
  };

  const clearHistory = async () => {
    try {
      await SecureStore.deleteItemAsync(HISTORY_STORAGE_KEY);
      setHistory([]);
      console.log('🗑️ History cleared');
    } catch (error) {
      console.log('Error clearing history:', error);
    }
  };

  const deleteSession = async (id: string) => {
    const newHistory = history.filter(s => s.id !== id);
    await saveHistory(newHistory);
  };

  const getSessionById = (id: string) => {
    return history.find(s => s.id === id);
  };

  return (
    <HistoryContext.Provider value={{ history, addSession, clearHistory, deleteSession, getSessionById }}>
      {children}
    </HistoryContext.Provider>
  );
}

export function useHistory() {
  const context = useContext(HistoryContext);
  if (!context) {
    throw new Error('useHistory must be used within a HistoryProvider');
  }
  return context;
}

// Helper to get mode icon
export function getModeIcon(mode: RecordingSession['mode']): string {
  switch (mode) {
    case 'audio-live': return 'radio';
    case 'audio-record': return 'mic';
    case 'audio-upload': return 'cloud-upload';
    case 'image': return 'camera';
    case 'description': return 'text';
    default: return 'help-circle';
  }
}

// Helper to get mode color
export function getModeColor(mode: RecordingSession['mode']): string {
  switch (mode) {
    case 'audio-live': return '#ef4444';
    case 'audio-record': return '#22c55e';
    case 'audio-upload': return '#8b5cf6';
    case 'image': return '#3b82f6';
    case 'description': return '#f59e0b';
    default: return '#64748b';
  }
}

// Helper to get mode label
export function getModeLabel(mode: RecordingSession['mode']): string {
  switch (mode) {
    case 'audio-live': return 'Live Audio';
    case 'audio-record': return 'Recorded';
    case 'audio-upload': return 'Uploaded';
    case 'image': return 'Image';
    case 'description': return 'Description';
    default: return 'Unknown';
  }
}


