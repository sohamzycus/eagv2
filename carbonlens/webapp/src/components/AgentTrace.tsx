import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Brain, 
  Wrench, 
  CheckCircle, 
  XCircle, 
  Clock, 
  ChevronDown, 
  ChevronRight,
  Eye,
  Copy,
  ExternalLink
} from 'lucide-react'
import { ToolCall, StreamDelta, TraceStep } from '@/types'
import { clsx } from 'clsx'
import { format } from 'date-fns'

interface AgentTraceProps {
  deltas: StreamDelta[]
  toolCalls: ToolCall[]
  isActive: boolean
}

export function AgentTrace({ deltas, toolCalls, isActive }: AgentTraceProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())
  const [showRawData, setShowRawData] = useState<Set<string>>(new Set())

  const toggleExpanded = (stepId: string) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId)
    } else {
      newExpanded.add(stepId)
    }
    setExpandedSteps(newExpanded)
  }

  const toggleRawData = (stepId: string) => {
    const newShowRaw = new Set(showRawData)
    if (newShowRaw.has(stepId)) {
      newShowRaw.delete(stepId)
    } else {
      newShowRaw.add(stepId)
    }
    setShowRawData(newShowRaw)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const getStepIcon = (type: string, status?: string) => {
    switch (type) {
      case 'plan':
        return <Brain className="w-5 h-5 text-blue-600" />
      case 'tool_call':
        return <Wrench className="w-5 h-5 text-orange-600" />
      case 'tool_result':
        return status === 'failed' 
          ? <XCircle className="w-5 h-5 text-red-600" />
          : <CheckCircle className="w-5 h-5 text-green-600" />
      case 'final':
        return <CheckCircle className="w-5 h-5 text-primary-600" />
      default:
        return <Clock className="w-5 h-5 text-gray-400" />
    }
  }

  const getStepTitle = (delta: StreamDelta) => {
    switch (delta.type) {
      case 'plan':
        return delta.data.status === 'starting' 
          ? 'Agent Initializing'
          : delta.data.status === 'planning'
          ? 'Agent Planning'
          : 'Agent Plan'
      case 'tool_call':
        return `🔧 Executing ${delta.data.tool}`
      case 'tool_result':
        return delta.data.success 
          ? `✅ ${getToolDisplayName(delta.data.toolId)} - Success` 
          : `❌ ${getToolDisplayName(delta.data.toolId)} - Failed`
      case 'final':
        return '🎯 Final Analysis'
      default:
        return 'Step'
    }
  }

  const getToolDisplayName = (toolId?: string) => {
    const toolCall = toolCalls.find(tc => tc.id === toolId)
    if (!toolCall) return 'Tool'
    
    switch (toolCall.tool) {
      case 'CarbonApiTool':
        return 'Carbon Interface API'
      case 'LCADatabaseTool':
        return 'Climatiq LCA Database'
      case 'ElectricityIntensityTool':
        return 'ElectricityMap API'
      case 'NewsSearchTool':
        return 'News API'
      case 'EmissionEstimatorTool':
        return 'Monte Carlo Simulator'
      case 'PageExtractorTool':
        return 'Page Data Extractor'
      case 'NotifierTool':
        return 'Notification Service'
      default:
        return toolCall.tool
    }
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  const getToolDescription = (tool: string) => {
    switch (tool) {
      case 'CarbonApiTool':
        return 'Fetching carbon emission factors from Carbon Interface'
      case 'LCADatabaseTool':
        return 'Querying life cycle assessment data from Climatiq'
      case 'ElectricityIntensityTool':
        return 'Getting real-time electricity carbon intensity from ElectricityMap'
      case 'NewsSearchTool':
        return 'Searching for relevant sustainability news'
      case 'EmissionEstimatorTool':
        return 'Running Monte Carlo simulation for emission calculations'
      case 'PageExtractorTool':
        return 'Extracting specifications from web page'
      case 'NotifierTool':
        return 'Sending notification'
      default:
        return 'Executing tool'
    }
  }

  const getResultSummary = (result: any) => {
    if (!result) return 'No data returned'
    
    if (typeof result === 'string') {
      return result.length > 100 ? `${result.slice(0, 100)}...` : result
    }
    
    if (Array.isArray(result)) {
      return `Returned ${result.length} items`
    }
    
    if (typeof result === 'object') {
      const keys = Object.keys(result)
      if (keys.includes('mean') && keys.includes('unit')) {
        return `${result.mean?.toFixed(2)} ${result.unit} (Monte Carlo result)`
      }
      if (keys.includes('intensity')) {
        return `${result.intensity} gCO2e/kWh carbon intensity`
      }
      if (keys.includes('factor')) {
        return `${result.factor} kg CO2e emission factor`
      }
      return `Object with ${keys.length} properties`
    }
    
    return 'Data received'
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={clsx(
              'p-2 rounded-lg',
              isActive ? 'bg-blue-100 animate-agent-pulse' : 'bg-gray-100'
            )}>
              <Brain className={clsx(
                'w-5 h-5',
                isActive ? 'text-blue-600' : 'text-gray-500'
              )} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Agent Execution Trace
              </h3>
              <p className="text-sm text-gray-500">
                {isActive ? 'Running...' : `${deltas.length} steps completed`}
              </p>
            </div>
          </div>
          
          {isActive && (
            <div className="flex items-center space-x-2 text-sm text-blue-600">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
              <span>Active</span>
            </div>
          )}
        </div>
      </div>

      {/* Trace Steps */}
      <div className="max-h-96 overflow-y-auto">
        {deltas.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <Brain className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">Waiting for agent to start...</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {deltas.map((delta, index) => {
              const stepId = `step-${index}`
              const isExpanded = expandedSteps.has(stepId)
              const showRaw = showRawData.has(stepId)
              const toolCall = delta.type === 'tool_call' || delta.type === 'tool_result' 
                ? toolCalls.find(tc => tc.id === delta.data.toolId || tc.tool === delta.data.tool)
                : null

              return (
                <motion.div
                  key={stepId}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className="px-6 py-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start space-x-4">
                    {/* Icon */}
                    <div className="flex-shrink-0 mt-1">
                      {getStepIcon(delta.type, delta.data.success === false ? 'failed' : 'success')}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <h4 className="text-sm font-medium text-gray-900">
                            {getStepTitle(delta)}
                          </h4>
                          {toolCall?.duration && (
                            <span className="text-xs text-gray-500">
                              {formatDuration(toolCall.duration)}
                            </span>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-400">
                            {format(delta.timestamp, 'HH:mm:ss')}
                          </span>
                          {(delta.data.plan || delta.data.result || delta.data.error) && (
                            <button
                              onClick={() => toggleExpanded(stepId)}
                              className="text-gray-400 hover:text-gray-600 transition-colors"
                            >
                              {isExpanded ? (
                                <ChevronDown className="w-4 h-4" />
                              ) : (
                                <ChevronRight className="w-4 h-4" />
                              )}
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Step Summary */}
                      <div className="text-sm text-gray-600 mb-2">
                        {delta.type === 'plan' && delta.data.message && (
                          <p>{delta.data.message}</p>
                        )}
                        {delta.type === 'tool_call' && (
                          <div>
                            <p className="font-medium">🔄 Calling {getToolDisplayName(delta.data.id)}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {getToolDescription(delta.data.tool)} • {Object.keys(delta.data.args || {}).length} parameters
                            </p>
                          </div>
                        )}
                        {delta.type === 'tool_result' && (
                          <div className={clsx(
                            delta.data.success ? 'text-green-600' : 'text-red-600'
                          )}>
                            {delta.data.success ? (
                              <div>
                                <p className="font-medium">✅ API call completed successfully</p>
                                <p className="text-xs text-gray-500 mt-1">
                                  {getResultSummary(delta.data.result)}
                                </p>
                              </div>
                            ) : (
                              <div>
                                <p className="font-medium">❌ API call failed</p>
                                <p className="text-xs text-red-500 mt-1">{delta.data.error}</p>
                              </div>
                            )}
                          </div>
                        )}
                        {delta.type === 'final' && (
                          <p className="text-primary-600 font-medium">🎯 Analysis complete with recommendations</p>
                        )}
                      </div>

                      {/* Expanded Content */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                          >
                            <div className="bg-gray-50 rounded-lg p-4 mt-3 border border-gray-200">
                              {/* Reasoning */}
                              {delta.data.plan?.reasoning && (
                                <div className="mb-4">
                                  <h5 className="text-xs font-medium text-gray-700 mb-2">Reasoning</h5>
                                  <p className="text-sm text-gray-600">{delta.data.plan.reasoning}</p>
                                </div>
                              )}

                              {/* Tool Arguments */}
                              {delta.data.plan?.args && (
                                <div className="mb-4">
                                  <h5 className="text-xs font-medium text-gray-700 mb-2">Arguments</h5>
                                  <pre className="text-xs bg-white p-2 rounded border overflow-x-auto">
                                    {JSON.stringify(delta.data.plan.args, null, 2)}
                                  </pre>
                                </div>
                              )}

                              {/* Tool Result */}
                              {delta.data.result && (
                                <div className="mb-4">
                                  <div className="flex items-center justify-between mb-2">
                                    <h5 className="text-xs font-medium text-gray-700">Result</h5>
                                    <div className="flex items-center space-x-2">
                                      <button
                                        onClick={() => toggleRawData(stepId)}
                                        className="text-xs text-blue-600 hover:text-blue-800 flex items-center"
                                      >
                                        <Eye className="w-3 h-3 mr-1" />
                                        {showRaw ? 'Hide Raw' : 'Show Raw'}
                                      </button>
                                      <button
                                        onClick={() => copyToClipboard(JSON.stringify(delta.data.result, null, 2))}
                                        className="text-xs text-gray-600 hover:text-gray-800 flex items-center"
                                      >
                                        <Copy className="w-3 h-3 mr-1" />
                                        Copy
                                      </button>
                                    </div>
                                  </div>
                                  
                                  {showRaw ? (
                                    <pre className="text-xs bg-white p-2 rounded border overflow-x-auto max-h-48">
                                      {JSON.stringify(delta.data.result, null, 2)}
                                    </pre>
                                  ) : (
                                    <div className="text-sm text-gray-600">
                                      {typeof delta.data.result === 'string' 
                                        ? delta.data.result 
                                        : `${Object.keys(delta.data.result).length} properties returned`
                                      }
                                    </div>
                                  )}
                                </div>
                              )}

                              {/* Final Response */}
                              {delta.data.result && delta.type === 'final' && (
                                <div className="bg-primary-50 p-3 rounded-lg border border-primary-200">
                                  <h5 className="text-sm font-medium text-primary-800 mb-2">Final Analysis</h5>
                                  <div className="text-sm text-primary-700">
                                    {typeof delta.data.result === 'string' 
                                      ? delta.data.result
                                      : JSON.stringify(delta.data.result, null, 2)
                                    }
                                  </div>
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>

      {/* Active Indicator */}
      {isActive && (
        <div className="px-6 py-3 bg-blue-50 border-t border-blue-200">
          <div className="flex items-center space-x-2 text-sm text-blue-700">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" />
            <span>Agent is processing...</span>
          </div>
        </div>
      )}
    </div>
  )
}
