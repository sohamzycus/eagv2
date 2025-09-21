/**
 * Interface for Google Gemini AI service
 */

import type { AgentPlan } from '@/shared/types';

/**
 * Options for Gemini API calls
 */
export interface GeminiOptions {
  /** Maximum tokens to generate */
  maxTokens?: number;
  /** Temperature for response randomness (0-1) */
  temperature?: number;
  /** Top-p sampling parameter */
  topP?: number;
  /** Top-k sampling parameter */
  topK?: number;
}

/**
 * Gemini service interface for AI planning and summarization
 */
export interface IGeminiService {
  /**
   * Generate an agent plan from conversation history
   * @param conversationHistory - Array of previous messages
   * @param options - Generation options
   * @returns Promise resolving to agent plan
   */
  plan(conversationHistory: string[], options?: GeminiOptions): Promise<AgentPlan>;

  /**
   * Generate a summary of provided text
   * @param text - Text to summarize
   * @param options - Generation options
   * @returns Promise resolving to summary text
   */
  summarize(text: string, options?: GeminiOptions): Promise<string>;

  /**
   * Stream an agent plan with real-time updates
   * @param conversationHistory - Array of previous messages
   * @param onDelta - Callback for streaming updates
   * @param options - Generation options
   * @returns Promise resolving when streaming completes
   */
  streamPlan(
    conversationHistory: string[],
    onDelta: (chunk: string) => void,
    options?: GeminiOptions
  ): Promise<void>;

  /**
   * Check if the service is properly configured
   * @returns Promise resolving to true if configured
   */
  isConfigured(): Promise<boolean>;
}
