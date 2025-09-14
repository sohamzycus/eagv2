/**
 * Shared type definitions for GemLens extension
 */

export interface SummaryRequest {
  action: 'summarizePage' | 'summarizeVideo' | 'streamSummarize';
  text: string;
  url?: string;
}

export interface SummaryResponse {
  summary?: string;
  error?: string;
  status?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface ExtractedContent {
  text: string;
  title?: string;
  url: string;
  type: 'webpage' | 'video';
  captions?: string;
}

export interface CacheEntry {
  createdAt: number;
  ttl: number;
  value: any;
}

export interface ApiKeyStatus {
  hasKey: boolean;
  isValid?: boolean;
}
