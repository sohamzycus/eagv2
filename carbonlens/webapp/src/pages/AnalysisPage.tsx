import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Send, 
  Brain, 
  Loader2, 
  AlertCircle,
  Download,
  Share,
  BarChart3,
  Zap,
  Clock,
  CheckCircle
} from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { AgentTrace } from '@/components/AgentTrace'
import { AgentOrchestrator } from '@/services/agent'
import { TaskRequest, TaskResult, StreamDelta, ToolCall } from '@/types'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'

export function AnalysisPage() {
  const { apiConfig, isConfigured, setCurrentTask, addTaskToHistory } = useAppStore()
  const [prompt, setPrompt] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [currentResult, setCurrentResult] = useState<TaskResult | null>(null)
  const [deltas, setDeltas] = useState<StreamDelta[]>([])
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([])
  const [samples, setSamples] = useState(1000)
  
  const orchestratorRef = useRef<AgentOrchestrator | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Initialize orchestrator when config changes
  useEffect(() => {
    if (isConfigured) {
      orchestratorRef.current = new AgentOrchestrator(apiConfig)
    }
  }, [apiConfig, isConfigured])

  // Get query from URL params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const query = params.get('q')
    if (query) {
      setPrompt(query)
      // Clear URL params
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!prompt.trim()) {
      toast.error('Please enter a prompt')
      return
    }

    if (!isConfigured || !orchestratorRef.current) {
      toast.error('Please configure API keys in Settings first')
      return
    }

    setIsRunning(true)
    setDeltas([])
    setToolCalls([])
    setCurrentResult(null)
    
    const request: TaskRequest = {
      prompt: prompt.trim(),
      samples,
      useRealApis: true,
    }

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController()

    try {
      console.log('Starting analysis with request:', request)
      console.log('Orchestrator:', orchestratorRef.current)
      console.log('API Config:', apiConfig)
      
      const generator = orchestratorRef.current.runTask(request)
      
      for await (const delta of generator) {
        console.log('Received delta:', delta)
        
        // Check if cancelled
        if (abortControllerRef.current?.signal.aborted) {
          break
        }

        setDeltas(prev => [...prev, delta])
        
        // Update tool calls
        if (delta.type === 'tool_call') {
          setToolCalls(prev => [...prev, delta.data])
        } else if (delta.type === 'tool_result') {
          setToolCalls(prev => prev.map(tc => 
            tc.id === delta.data.toolId 
              ? { ...tc, ...delta.data, status: delta.data.success ? 'completed' : 'failed' }
              : tc
          ))
        }
        
        // Final result
        if (delta.type === 'final') {
          console.log('Final delta received:', delta)
          
          // Create complete task result
          const taskResult: TaskResult = {
            taskId: `task_${Date.now()}`,
            status: 'completed',
            result: delta.data.result || delta.data.response || 'Analysis completed',
            startTime: Date.now() - 30000, // Approximate start time
            endTime: Date.now(),
            duration: 30000, // Approximate duration
            toolCalls,
            messages: []
          }
          
          console.log('Setting task result:', taskResult)
          setCurrentResult(taskResult)
          setCurrentTask(taskResult)
          addTaskToHistory(taskResult)
          toast.success('Analysis completed!')
          
          // Stop the running state
          setIsRunning(false)
        }
      }
    } catch (error) {
      console.error('Analysis error:', error)
      console.error('Error details:', {
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
        orchestrator: orchestratorRef.current,
        apiConfig: apiConfig
      })
      toast.error(error instanceof Error ? error.message : 'Analysis failed')
    } finally {
      setIsRunning(false)
      abortControllerRef.current = null
    }
  }

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsRunning(false)
      toast.info('Analysis cancelled')
    }
  }

  const handleDownload = () => {
    if (!currentResult) return
    
    const data = {
      task: currentResult,
      deltas,
      toolCalls,
      timestamp: new Date().toISOString(),
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `carbonlens-analysis-${currentResult.taskId}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const examplePrompts = [
    "Compare compute carbon intensity us-east-1 vs eu-west-1 for 200 8-vCPU VMs",
    "Analyze migration of 500 servers from coal-heavy to renewable regions",
    "Calculate annual emissions for 100 cloud instances with uncertainty",
    "Find the optimal AWS region for minimal carbon footprint",
  ]

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Carbon Analysis
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Describe your carbon analysis needs in natural language. The AI agent will plan the analysis, 
          gather real-time data, and provide actionable insights.
        </p>
      </div>

      {/* Configuration Warning */}
      {!isConfigured && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-yellow-50 border border-yellow-200 rounded-lg p-4"
        >
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-yellow-600" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800">API Configuration Required</h3>
              <p className="text-sm text-yellow-700 mt-1">
                Please configure your API keys in Settings to use real carbon analysis.
              </p>
            </div>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Analysis Request
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Describe your carbon analysis needs
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., Compare compute carbon intensity between us-east-1 and eu-west-1 for 200 8-vCPU VMs with uncertainty analysis..."
                  className="input h-32 resize-none"
                  disabled={isRunning}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Monte Carlo Samples
                  </label>
                  <select
                    value={samples}
                    onChange={(e) => setSamples(Number(e.target.value))}
                    className="input"
                    disabled={isRunning}
                  >
                    <option value={100}>100 (Fast)</option>
                    <option value={1000}>1,000 (Standard)</option>
                    <option value={10000}>10,000 (High Precision)</option>
                  </select>
                </div>
                
                <div className="flex items-end">
                  <div className="flex space-x-2 w-full">
                    {isRunning ? (
                      <button
                        type="button"
                        onClick={handleCancel}
                        className="btn-secondary flex-1"
                      >
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Cancel
                      </button>
                    ) : (
                      <button
                        type="submit"
                        disabled={!prompt.trim() || !isConfigured}
                        className="btn-primary flex-1"
                      >
                        <Send className="w-4 h-4 mr-2" />
                        Analyze
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </form>
          </div>

          {/* Example Prompts */}
          {!isRunning && deltas.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="card p-6"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Example Queries
              </h3>
              <div className="space-y-2">
                {examplePrompts.map((example, index) => (
                  <button
                    key={index}
                    onClick={() => setPrompt(example)}
                    className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors text-sm"
                  >
                    "{example}"
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Results Summary */}
          {currentResult && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="card p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Analysis Results
                </h3>
                <div className="flex space-x-2">
                  <button
                    onClick={handleDownload}
                    className="btn-outline btn text-sm"
                  >
                    <Download className="w-4 h-4 mr-1" />
                    Export
                  </button>
                </div>
              </div>

              {/* Status */}
              <div className="flex items-center space-x-2 mb-4">
                {currentResult.status === 'completed' ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : currentResult.status === 'failed' ? (
                  <AlertCircle className="w-5 h-5 text-red-600" />
                ) : (
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                )}
                <span className={clsx(
                  'text-sm font-medium',
                  currentResult.status === 'completed' ? 'text-green-700' :
                  currentResult.status === 'failed' ? 'text-red-700' :
                  'text-blue-700'
                )}>
                  {currentResult.status === 'completed' ? 'Analysis Complete' :
                   currentResult.status === 'failed' ? 'Analysis Failed' :
                   'Running...'}
                </span>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <Clock className="w-5 h-5 text-gray-600 mx-auto mb-1" />
                  <div className="text-sm font-medium text-gray-900">
                    {currentResult.duration ? `${(currentResult.duration / 1000).toFixed(1)}s` : '-'}
                  </div>
                  <div className="text-xs text-gray-500">Duration</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <Zap className="w-5 h-5 text-gray-600 mx-auto mb-1" />
                  <div className="text-sm font-medium text-gray-900">
                    {toolCalls.length}
                  </div>
                  <div className="text-xs text-gray-500">Tool Calls</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <BarChart3 className="w-5 h-5 text-gray-600 mx-auto mb-1" />
                  <div className="text-sm font-medium text-gray-900">
                    {samples.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-500">Samples</div>
                </div>
              </div>

              {/* Result Content */}
              {currentResult.result && (
                <div className="bg-primary-50 p-4 rounded-lg border border-primary-200">
                  <h4 className="text-sm font-medium text-primary-800 mb-2">
                    Analysis Summary
                  </h4>
                  <div className="text-sm text-primary-700 whitespace-pre-wrap">
                    {typeof currentResult.result === 'string' 
                      ? currentResult.result
                      : JSON.stringify(currentResult.result, null, 2)
                    }
                  </div>
                </div>
              )}

              {/* Error */}
              {currentResult.error && (
                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                  <h4 className="text-sm font-medium text-red-800 mb-2">
                    Error Details
                  </h4>
                  <div className="text-sm text-red-700">
                    {currentResult.error}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </div>

        {/* Agent Trace */}
        <div className="space-y-6">
          <AgentTrace 
            deltas={deltas}
            toolCalls={toolCalls}
            isActive={isRunning}
          />
        </div>
      </div>
    </div>
  )
}
