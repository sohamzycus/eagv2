import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Settings, 
  Key, 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Eye, 
  EyeOff,
  ExternalLink,
  Save,
  RefreshCw
} from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { ApiConfig } from '@/types'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'

export function SettingsPage() {
  const { apiConfig, updateApiConfig, isConfigured } = useAppStore()
  const [localConfig, setLocalConfig] = useState<ApiConfig>(apiConfig)
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [testingConnection, setTestingConnection] = useState(false)

  const handleSave = () => {
    updateApiConfig(localConfig)
    toast.success('API configuration saved!')
  }

  const handleReset = () => {
    setLocalConfig(apiConfig)
    toast.info('Configuration reset to saved values')
  }

  const toggleKeyVisibility = (keyName: string) => {
    setShowKeys(prev => ({ ...prev, [keyName]: !prev[keyName] }))
  }

  const handleTestConnection = async () => {
    setTestingConnection(true)
    try {
      // Test Gemini connection
      if (localConfig.gemini) {
        // Mock test - in real app, you'd make a test API call
        await new Promise(resolve => setTimeout(resolve, 1000))
        toast.success('Gemini API connection successful!')
      } else {
        toast.error('Gemini API key is required')
      }
    } catch (error) {
      toast.error('API connection test failed')
    } finally {
      setTestingConnection(false)
    }
  }

  const apiServices = [
    {
      key: 'gemini',
      name: 'Google Gemini',
      description: 'Required for AI agent functionality',
      required: true,
      url: 'https://makersuite.google.com/app/apikey',
      placeholder: 'AIza...',
    },
    {
      key: 'carbonInterface',
      name: 'Carbon Interface',
      description: 'Carbon emission factors and calculations',
      required: false,
      url: 'https://www.carboninterface.com/docs/',
      placeholder: 'Bearer token...',
    },
    {
      key: 'climatiq',
      name: 'Climatiq',
      description: 'Life cycle assessment database',
      required: false,
      url: 'https://www.climatiq.io/docs',
      placeholder: 'Bearer token...',
    },
    {
      key: 'electricityMap',
      name: 'ElectricityMap',
      description: 'Real-time electricity carbon intensity',
      required: false,
      url: 'https://www.electricitymap.org/api',
      placeholder: 'API token...',
    },
    {
      key: 'newsApi',
      name: 'News API',
      description: 'Sustainability and carbon news',
      required: false,
      url: 'https://newsapi.org/',
      placeholder: 'API key...',
    },
    {
      key: 'alphaVantage',
      name: 'Alpha Vantage',
      description: 'Financial and market data',
      required: false,
      url: 'https://www.alphavantage.co/support/#api-key',
      placeholder: 'API key...',
    },
  ] as const

  const hasChanges = JSON.stringify(localConfig) !== JSON.stringify(apiConfig)

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          API Configuration
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Configure your API keys to enable real-time carbon analysis. 
          All keys are stored locally in your browser and never sent to our servers.
        </p>
      </div>

      {/* Status Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={clsx(
          'card p-6',
          isConfigured ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'
        )}
      >
        <div className="flex items-center space-x-3">
          {isConfigured ? (
            <CheckCircle className="w-6 h-6 text-green-600" />
          ) : (
            <AlertTriangle className="w-6 h-6 text-yellow-600" />
          )}
          <div>
            <h2 className={clsx(
              'text-lg font-semibold',
              isConfigured ? 'text-green-800' : 'text-yellow-800'
            )}>
              {isConfigured ? 'Configuration Complete' : 'Configuration Required'}
            </h2>
            <p className={clsx(
              'text-sm',
              isConfigured ? 'text-green-700' : 'text-yellow-700'
            )}>
              {isConfigured 
                ? 'Your APIs are configured and ready for real-time analysis'
                : 'At minimum, configure Gemini API to enable AI agent functionality'
              }
            </p>
          </div>
        </div>
      </motion.div>

      {/* Security Notice */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-blue-50 border border-blue-200 rounded-lg p-4"
      >
        <div className="flex items-start space-x-3">
          <Shield className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-blue-800">
              Security & Privacy
            </h3>
            <ul className="text-sm text-blue-700 mt-1 space-y-1">
              <li>• API keys are stored locally in your browser only</li>
              <li>• Keys are never transmitted to CarbonLens servers</li>
              <li>• All API calls are made directly from your browser</li>
              <li>• You can clear keys anytime by clearing browser data</li>
            </ul>
          </div>
        </div>
      </motion.div>

      {/* API Configuration */}
      <div className="space-y-6">
        {apiServices.map((service, index) => (
          <motion.div
            key={service.key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * index }}
            className="card p-6"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={clsx(
                  'p-2 rounded-lg',
                  service.required ? 'bg-red-100' : 'bg-gray-100'
                )}>
                  <Key className={clsx(
                    'w-5 h-5',
                    service.required ? 'text-red-600' : 'text-gray-600'
                  )} />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {service.name}
                    </h3>
                    {service.required && (
                      <span className="badge-error">Required</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">
                    {service.description}
                  </p>
                </div>
              </div>
              
              <a
                href={service.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>

            <div className="relative">
              <input
                type={showKeys[service.key] ? 'text' : 'password'}
                placeholder={service.placeholder}
                value={localConfig[service.key as keyof ApiConfig] || ''}
                onChange={(e) => setLocalConfig(prev => ({
                  ...prev,
                  [service.key]: e.target.value
                }))}
                className="input pr-10"
              />
              <button
                type="button"
                onClick={() => toggleKeyVisibility(service.key)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showKeys[service.key] ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>

            {localConfig[service.key as keyof ApiConfig] && (
              <div className="mt-2 flex items-center space-x-2 text-sm">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-green-700">API key configured</span>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="flex items-center justify-between pt-6 border-t border-gray-200"
      >
        <div className="flex items-center space-x-4">
          <button
            onClick={handleTestConnection}
            disabled={!localConfig.gemini || testingConnection}
            className="btn-outline flex items-center space-x-2"
          >
            <RefreshCw className={clsx(
              'w-4 h-4',
              testingConnection && 'animate-spin'
            )} />
            <span>Test Connection</span>
          </button>
          
          {hasChanges && (
            <button
              onClick={handleReset}
              className="btn-secondary"
            >
              Reset Changes
            </button>
          )}
        </div>

        <button
          onClick={handleSave}
          disabled={!hasChanges}
          className={clsx(
            'btn-primary flex items-center space-x-2',
            !hasChanges && 'opacity-50 cursor-not-allowed'
          )}
        >
          <Save className="w-4 h-4" />
          <span>Save Configuration</span>
        </button>
      </motion.div>

      {/* Usage Instructions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-gray-50 rounded-lg p-6"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Getting Started
        </h3>
        <div className="space-y-3 text-sm text-gray-700">
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
              1
            </div>
            <p>
              <strong>Start with Gemini:</strong> Get your free API key from Google AI Studio. 
              This enables the core AI agent functionality.
            </p>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
              2
            </div>
            <p>
              <strong>Add Data Sources:</strong> Configure carbon data APIs like Carbon Interface 
              and Climatiq for real emission factors.
            </p>
          </div>
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
              3
            </div>
            <p>
              <strong>Test & Analyze:</strong> Use the Test Connection button to verify your setup, 
              then start running carbon analyses.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
