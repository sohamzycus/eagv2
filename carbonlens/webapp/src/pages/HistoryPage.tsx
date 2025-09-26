import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  History, 
  Download, 
  Trash2, 
  Eye, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Search,
  Filter,
  Calendar
} from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { TaskResult } from '@/types'
import { clsx } from 'clsx'
import { format } from 'date-fns'

export function HistoryPage() {
  const { taskHistory, clearHistory } = useAppStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedTask, setSelectedTask] = useState<TaskResult | null>(null)

  // Filter tasks based on search and status
  const filteredTasks = taskHistory.filter(task => {
    const matchesSearch = task.result?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         task.messages.some(msg => msg.content.toLowerCase().includes(searchQuery.toLowerCase()))
    const matchesStatus = statusFilter === 'all' || task.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const handleDownloadTask = (task: TaskResult) => {
    const data = {
      task,
      timestamp: new Date().toISOString(),
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `carbonlens-task-${task.taskId}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleDownloadAll = () => {
    const data = {
      tasks: taskHistory,
      exportedAt: new Date().toISOString(),
      totalTasks: taskHistory.length,
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `carbonlens-history-${format(new Date(), 'yyyy-MM-dd')}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <Clock className="w-5 h-5 text-yellow-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-100'
      case 'failed':
        return 'text-red-700 bg-red-100'
      default:
        return 'text-yellow-700 bg-yellow-100'
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Analysis History
          </h1>
          <p className="text-gray-600">
            View and manage your carbon analysis history
          </p>
        </div>
        
        {taskHistory.length > 0 && (
          <div className="flex items-center space-x-3">
            <button
              onClick={handleDownloadAll}
              className="btn-outline flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Export All</span>
            </button>
            <button
              onClick={clearHistory}
              className="btn-secondary flex items-center space-x-2 text-red-600 hover:text-red-700"
            >
              <Trash2 className="w-4 h-4" />
              <span>Clear All</span>
            </button>
          </div>
        )}
      </div>

      {taskHistory.length === 0 ? (
        /* Empty State */
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-16"
        >
          <History className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            No Analysis History
          </h2>
          <p className="text-gray-600 mb-6">
            Your completed analyses will appear here
          </p>
          <a
            href="/analysis"
            className="btn-primary"
          >
            Start Your First Analysis
          </a>
        </motion.div>
      ) : (
        <div className="space-y-6">
          {/* Filters */}
          <div className="card p-4">
            <div className="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search analyses..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="input pl-10"
                />
              </div>
              
              {/* Status Filter */}
              <div className="flex items-center space-x-2">
                <Filter className="w-5 h-5 text-gray-400" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="input w-auto"
                >
                  <option value="all">All Status</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                  <option value="running">Running</option>
                </select>
              </div>
            </div>
          </div>

          {/* Task List */}
          <div className="space-y-4">
            {filteredTasks.map((task, index) => (
              <motion.div
                key={task.taskId}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="card p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-3">
                    {/* Header */}
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(task.status)}
                      <span className={clsx(
                        'px-2 py-1 rounded-full text-xs font-medium',
                        getStatusColor(task.status)
                      )}>
                        {task.status}
                      </span>
                      <span className="text-sm text-gray-500">
                        {format(task.startTime, 'MMM d, yyyy HH:mm')}
                      </span>
                      {task.duration && (
                        <span className="text-sm text-gray-500">
                          • {(task.duration / 1000).toFixed(1)}s
                        </span>
                      )}
                    </div>

                    {/* Original Prompt */}
                    <div>
                      <h3 className="font-medium text-gray-900 mb-1">
                        Original Query
                      </h3>
                      <p className="text-gray-600 text-sm line-clamp-2">
                        {task.messages.find(m => m.role === 'user')?.content || 'No query found'}
                      </p>
                    </div>

                    {/* Result Preview */}
                    {task.result && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-1">
                          Result
                        </h4>
                        <p className="text-gray-600 text-sm line-clamp-3">
                          {typeof task.result === 'string' 
                            ? task.result
                            : JSON.stringify(task.result).slice(0, 200) + '...'
                          }
                        </p>
                      </div>
                    )}

                    {/* Error */}
                    {task.error && (
                      <div className="bg-red-50 p-3 rounded-lg border border-red-200">
                        <h4 className="font-medium text-red-800 mb-1">
                          Error
                        </h4>
                        <p className="text-red-700 text-sm">
                          {task.error}
                        </p>
                      </div>
                    )}

                    {/* Metrics */}
                    <div className="flex items-center space-x-6 text-sm text-gray-500">
                      <span>
                        {task.toolCalls.length} tool calls
                      </span>
                      <span>
                        {task.messages.length} messages
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setSelectedTask(task)}
                      className="btn-outline btn text-sm"
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      View
                    </button>
                    <button
                      onClick={() => handleDownloadTask(task)}
                      className="btn-outline btn text-sm"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      Export
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* No Results */}
          {filteredTasks.length === 0 && (
            <div className="text-center py-8">
              <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600">
                No tasks match your search criteria
              </p>
            </div>
          )}
        </div>
      )}

      {/* Task Detail Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden"
          >
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Task Details
                </h2>
                <button
                  onClick={() => setSelectedTask(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <pre className="text-sm bg-gray-50 p-4 rounded-lg overflow-x-auto">
                {JSON.stringify(selectedTask, null, 2)}
              </pre>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
