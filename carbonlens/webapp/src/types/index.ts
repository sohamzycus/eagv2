// Agent Types
export interface AgentMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: number
  metadata?: Record<string, any>
}

export interface AgentPlan {
  type: 'tool_call' | 'final'
  tool?: string
  args?: Record<string, any>
  response?: string
  reasoning?: string
}

export interface ToolCall {
  id: string
  tool: string
  args: Record<string, any>
  timestamp: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  result?: any
  error?: string
  duration?: number
}

export interface StreamDelta {
  type: 'plan' | 'tool_call' | 'tool_result' | 'final'
  data: any
  timestamp: number
}

// Task Types
export interface TaskRequest {
  prompt: string
  samples?: number
  useRealApis?: boolean
  notifyChannel?: NotificationChannel
}

export interface TaskResult {
  taskId: string
  status: 'running' | 'completed' | 'failed' | 'cancelled'
  result?: any
  error?: string
  startTime: number
  endTime?: number
  duration?: number
  toolCalls: ToolCall[]
  messages: AgentMessage[]
}

export interface NotificationChannel {
  type: 'slack' | 'webhook' | 'email'
  endpoint: string
  name: string
}

// Carbon Analysis Types
export interface CarbonFactor {
  id: string
  name: string
  category: string
  unit: string
  value: number
  source: string
  region?: string
  year?: number
  uncertainty?: number
}

export interface EmissionResult {
  mean: number
  median: number
  std: number
  min: number
  max: number
  p25: number
  p75: number
  p95: number
  unit: string
  confidence: number
  samples: number
  breakdown?: {
    categories: string[]
    values: number[]
    compute?: number[]
    uncertainty?: number[]
  }
}

export interface ComparisonResult {
  scenarios: string[]
  results: Record<string, EmissionResult>
  comparisons: Record<string, {
    difference: number
    percentChange: number
    unit: string
    lowerEmission: string
    reduction: number
  }>
  recommendation: {
    bestScenario: string
    worstScenario: string
    potentialReduction: number
    confidence: string
    summary: string
  }
  range: {
    min: number
    max: number
    span: number
    unit: string
  }
}

// API Types
export interface ApiConfig {
  gemini?: string
  carbonInterface?: string
  climatiq?: string
  electricityMap?: string
  newsApi?: string
  alphaVantage?: string
}

export interface ElectricityData {
  region: string
  intensity: number // gCO2e/kWh
  renewable_percentage: number
  fossil_percentage: number
  nuclear_percentage: number
  sources: {
    coal?: number
    gas?: number
    hydro?: number
    wind?: number
    solar?: number
    nuclear?: number
    other?: number
  }
  timestamp: string
}

export interface NewsItem {
  title: string
  description: string
  url: string
  source: string
  publishedAt: string
  relevanceScore?: number
}

export interface PageData {
  url: string
  title: string
  text: string
  specs: {
    compute?: {
      vcpus?: number
      memory?: number // GB
      storage?: number // GB
      instances?: number
    }
    energy?: {
      power?: number // Watts
      powerUnit?: string
    }
    pricing?: {
      cost?: number
      currency?: string
      period?: string // hour, month, year
    }
    regions?: string[]
  }
  extractedAt: number
}

// Store Types
export interface AppState {
  currentTask: TaskResult | null
  taskHistory: TaskResult[]
  apiConfig: ApiConfig
  isConfigured: boolean
  
  // Actions
  setCurrentTask: (task: TaskResult | null) => void
  addTaskToHistory: (task: TaskResult) => void
  updateApiConfig: (config: Partial<ApiConfig>) => void
  clearHistory: () => void
}

// UI Types
export interface TraceStep {
  id: string
  type: 'plan' | 'tool_call' | 'tool_result' | 'final'
  timestamp: number
  duration?: number
  data: any
  status: 'pending' | 'running' | 'completed' | 'failed'
  children?: TraceStep[]
}

export interface MetricCard {
  title: string
  value: string
  change?: {
    value: number
    type: 'increase' | 'decrease'
    label: string
  }
  icon?: React.ComponentType<any>
  color?: 'green' | 'red' | 'blue' | 'yellow' | 'gray'
}
