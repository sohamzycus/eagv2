/**
 * Google Gemini AI service implementation
 */

import { GoogleGenerativeAI, GenerativeModel } from '@google/generative-ai';
import type { IGeminiService, GeminiOptions } from './IGeminiService';
import type { AgentPlan } from '@/shared/types';
import { retryWithBackoff, safeJsonParse } from '@/shared/utils';

/**
 * Real Gemini service implementation using Google Generative AI SDK
 */
export class GeminiService implements IGeminiService {
  private genAI: GoogleGenerativeAI | null = null;
  private model: GenerativeModel | null = null;

  constructor(private apiKey?: string) {
    if (apiKey) {
      this.genAI = new GoogleGenerativeAI(apiKey);
      this.model = this.genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });
    }
  }

  /**
   * Initialize with API key
   */
  public initialize(apiKey: string): void {
    this.apiKey = apiKey;
    this.genAI = new GoogleGenerativeAI(apiKey);
    this.model = this.genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });
  }

  /**
   * Generate agent plan from conversation history
   */
  public async plan(
    conversationHistory: string[],
    options: GeminiOptions = {}
  ): Promise<AgentPlan> {
    if (!this.model) {
      throw new Error('Gemini service not initialized with API key');
    }

    const systemPrompt = this.buildSystemPrompt();
    const conversationText = conversationHistory.join('\n\n');
    const fullPrompt = `${systemPrompt}\n\nConversation History:\n${conversationText}\n\nProvide your response as valid JSON only:`;

    try {
      const result = await retryWithBackoff(async () => {
        const response = await this.model!.generateContent({
          contents: [{ role: 'user', parts: [{ text: fullPrompt }] }],
          generationConfig: {
            maxOutputTokens: options.maxTokens ?? 1024,
            temperature: options.temperature ?? 0.7,
            topP: options.topP ?? 0.8,
            topK: options.topK ?? 40,
          },
        });

        const text = response.response.text();
        if (!text) {
          throw new Error('Empty response from Gemini');
        }

        return text;
      });

      // Try to parse as JSON, if it fails, request JSON formatting
      const plan = this.parseAgentPlan(result);
      if (!plan) {
        // Re-request with explicit JSON formatting instruction
        const jsonPrompt = `${fullPrompt}\n\nYour previous response was not valid JSON. Please respond with ONLY valid JSON in the exact format specified above.`;
        
        const retryResult = await retryWithBackoff(async () => {
          const response = await this.model!.generateContent({
            contents: [{ role: 'user', parts: [{ text: jsonPrompt }] }],
            generationConfig: {
              maxOutputTokens: options.maxTokens ?? 1024,
              temperature: 0.3, // Lower temperature for more structured output
              topP: options.topP ?? 0.8,
              topK: options.topK ?? 40,
            },
          });

          return response.response.text();
        });

        const retryPlan = this.parseAgentPlan(retryResult);
        if (!retryPlan) {
          throw new Error('Failed to get valid JSON response from Gemini after retry');
        }
        return retryPlan;
      }

      return plan;
    } catch (error) {
      console.error('Gemini plan generation failed:', error);
      throw new Error(`Gemini API error: ${(error as Error).message}`);
    }
  }

  /**
   * Generate summary of text
   */
  public async summarize(text: string, options: GeminiOptions = {}): Promise<string> {
    if (!this.model) {
      throw new Error('Gemini service not initialized with API key');
    }

    const prompt = `Please provide a concise summary of the following text, focusing on key carbon emissions and environmental impact information:\n\n${text}`;

    try {
      const result = await retryWithBackoff(async () => {
        const response = await this.model!.generateContent({
          contents: [{ role: 'user', parts: [{ text: prompt }] }],
          generationConfig: {
            maxOutputTokens: options.maxTokens ?? 512,
            temperature: options.temperature ?? 0.5,
            topP: options.topP ?? 0.8,
            topK: options.topK ?? 40,
          },
        });

        const text = response.response.text();
        if (!text) {
          throw new Error('Empty response from Gemini');
        }

        return text;
      });

      return result;
    } catch (error) {
      console.error('Gemini summarization failed:', error);
      throw new Error(`Gemini API error: ${(error as Error).message}`);
    }
  }

  /**
   * Stream agent plan with real-time updates
   */
  public async streamPlan(
    conversationHistory: string[],
    onDelta: (chunk: string) => void,
    options: GeminiOptions = {}
  ): Promise<void> {
    if (!this.model) {
      throw new Error('Gemini service not initialized with API key');
    }

    const systemPrompt = this.buildSystemPrompt();
    const conversationText = conversationHistory.join('\n\n');
    const fullPrompt = `${systemPrompt}\n\nConversation History:\n${conversationText}\n\nProvide your response as valid JSON only:`;

    try {
      const result = await this.model.generateContentStream({
        contents: [{ role: 'user', parts: [{ text: fullPrompt }] }],
        generationConfig: {
          maxOutputTokens: options.maxTokens ?? 1024,
          temperature: options.temperature ?? 0.7,
          topP: options.topP ?? 0.8,
          topK: options.topK ?? 40,
        },
      });

      for await (const chunk of result.stream) {
        const chunkText = chunk.text();
        if (chunkText) {
          onDelta(chunkText);
        }
      }
    } catch (error) {
      console.error('Gemini streaming failed:', error);
      throw new Error(`Gemini streaming error: ${(error as Error).message}`);
    }
  }

  /**
   * Check if service is configured
   */
  public async isConfigured(): Promise<boolean> {
    return this.model !== null && this.apiKey !== undefined;
  }

  /**
   * Build system prompt for agent planning
   */
  private buildSystemPrompt(): string {
    return `You are CarbonLens, an expert carbon emissions research and decision assistant. Your role is to help users analyze, compare, and make decisions about carbon emissions across different technologies, regions, and scenarios.

Available Tools:
- CarbonApiTool: Query carbon emission factors from databases
- LCADatabaseTool: Access life cycle assessment data
- ElectricityIntensityTool: Get regional electricity grid carbon intensity
- NewsSearchTool: Search for recent carbon/climate news and reports
- EmissionEstimatorTool: Perform Monte Carlo emission calculations
- NotifierTool: Send notifications via configured channels
- PageExtractorTool: Extract structured data from current webpage

Response Format:
You must respond with valid JSON in one of these formats:

For tool calls:
{
  "type": "tool_call",
  "tool": "ToolName",
  "args": { "param1": "value1", "param2": "value2" },
  "reasoning": "Why this tool call is needed"
}

For final responses:
{
  "type": "final",
  "response": "Your final answer with analysis and recommendations",
  "reasoning": "Summary of analysis performed"
}

Guidelines:
- Always provide reasoning for your decisions
- Use multiple tools when needed for comprehensive analysis
- Focus on actionable insights and clear comparisons
- Include uncertainty ranges when available
- Cite data sources in your final responses`;
  }

  /**
   * Parse agent plan from response text
   */
  private parseAgentPlan(text: string): AgentPlan | null {
    // Try to extract JSON from response (handle cases where LLM adds extra text)
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      return null;
    }

    const plan = safeJsonParse<AgentPlan | null>(jsonMatch[0], null);
    
    // Validate plan structure
    if (!plan || !plan.type || (plan.type !== 'tool_call' && plan.type !== 'final')) {
      return null;
    }

    if (plan.type === 'tool_call' && (!plan.tool || !plan.args)) {
      return null;
    }

    if (plan.type === 'final' && !plan.response) {
      return null;
    }

    return plan;
  }
}
