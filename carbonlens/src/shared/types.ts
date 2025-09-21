/**
 * Core types for CarbonLens extension
 */

/**
 * Task request from user input
 */
export interface TaskRequest {
  /** User's natural language prompt */
  prompt: string;
  /** Number of Monte Carlo samples for estimation */
  samples?: number | undefined;
  /** Notification channel configuration */
  notifyChannel?: NotificationChannel;
  /** Whether to use backend proxy vs direct API calls */
  useBackend?: boolean;
}

/**
 * Agent plan response from LLM
 */
export interface AgentPlan {
  /** Type of response - either tool call or final answer */
  type: 'tool_call' | 'final';
  /** Tool to call (if type is tool_call) */
  tool?: string;
  /** Arguments for tool call */
  args?: Record<string, any>;
  /** Final response text (if type is final) */
  response?: string;
  /** Reasoning behind the plan */
  reasoning?: string;
}

/**
 * Tool execution result
 */
export interface ToolResult {
  /** Whether tool execution was successful */
  success: boolean;
  /** Result data from tool */
  data?: any;
  /** Error message if execution failed */
  error?: string;
  /** Metadata about the execution */
  metadata?: {
    executionTime?: number;
    source?: string;
    cached?: boolean;
  };
}

/**
 * Conversation event for logging
 */
export interface ConversationEvent {
  /** Unique event ID */
  id: string;
  /** Task ID this event belongs to */
  taskId: string;
  /** Event type */
  type: 'user_prompt' | 'llm_plan' | 'tool_call' | 'tool_result' | 'final';
  /** Event timestamp */
  timestamp: number;
  /** Event data */
  data: any;
}

/**
 * Task execution result
 */
export interface TaskResult {
  /** Unique task ID */
  taskId: string;
  /** Whether task completed successfully */
  success: boolean;
  /** Final result data */
  result?: any;
  /** Error message if task failed */
  error?: string;
  /** Execution metadata */
  metadata: {
    startTime: number;
    endTime: number;
    totalSteps: number;
    llmCalls: number;
    toolCalls: number;
  };
}

/**
 * Carbon emission factor data
 */
export interface CarbonFactor {
  /** Factor value (kg CO2e per unit) */
  value: number;
  /** Unit of measurement */
  unit: string;
  /** Source of the factor */
  source: string;
  /** Geographic region */
  region?: string;
  /** Confidence level (0-1) */
  confidence?: number;
  /** Last updated timestamp */
  updatedAt?: number;
}

/**
 * Electricity grid intensity data
 */
export interface GridIntensity {
  /** Region identifier */
  region: string;
  /** Carbon intensity (g CO2e/kWh) */
  intensity: number;
  /** Renewable percentage (0-100) */
  renewablePercent?: number;
  /** Data timestamp */
  timestamp: number;
  /** Data source */
  source: string;
}

/**
 * Emission estimation result
 */
export interface EmissionEstimate {
  /** Mean emission value */
  mean: number;
  /** Standard deviation */
  std: number;
  /** Unit of measurement */
  unit: string;
  /** Confidence interval (95%) */
  confidenceInterval: [number, number];
  /** Breakdown by component */
  breakdown: Record<string, number>;
  /** Number of Monte Carlo samples used */
  samples: number;
}

/**
 * Notification channel configuration
 */
export interface NotificationChannel {
  /** Channel type */
  type: 'slack' | 'telegram' | 'email' | 'webhook';
  /** Channel endpoint/webhook URL */
  endpoint: string;
  /** Channel name for display */
  name?: string;
}

/**
 * Extension configuration
 */
export interface ExtensionConfig {
  /** Whether to use real APIs vs mocks */
  useRealMode: boolean;
  /** Backend URL for API proxying */
  backendUrl?: string;
  /** Direct API keys (not recommended for production) */
  apiKeys?: {
    gemini?: string | undefined;
    carbonInterface?: string | undefined;
    climatiq?: string | undefined;
    electricityMap?: string | undefined;
    newsApi?: string | undefined;
    alphaVantage?: string | undefined;
  };
  /** Notification channels */
  notificationChannels?: NotificationChannel[];
}

/**
 * Page extraction result
 */
export interface PageExtraction {
  /** Page URL */
  url: string;
  /** Page title */
  title: string;
  /** Extracted structured data */
  data: {
    /** Product specifications */
    specs?: Record<string, any>;
    /** Energy/power consumption info */
    energy?: {
      power?: number;
      powerUnit?: string;
      efficiency?: string;
    };
    /** Geographic information */
    location?: {
      region?: string;
      country?: string;
      datacenter?: string;
    };
    /** Pricing information */
    pricing?: {
      cost?: number;
      currency?: string;
      period?: string;
    };
  };
}

/**
 * Streaming delta for real-time updates
 */
export interface StreamDelta {
  /** Delta type */
  type: 'plan' | 'tool_call' | 'tool_result' | 'final' | 'error';
  /** Delta content */
  content: string;
  /** Associated data */
  data?: any;
}
