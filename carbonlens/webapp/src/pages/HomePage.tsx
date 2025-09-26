import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Leaf, 
  Brain, 
  Zap, 
  BarChart3, 
  Shield, 
  ArrowRight,
  Play,
  CheckCircle,
  Sparkles
} from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'

export function HomePage() {
  const { isConfigured } = useAppStore()

  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Analysis',
      description: 'Advanced Gemini 2.0 Flash agent that understands complex carbon scenarios and provides intelligent recommendations.',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      icon: Zap,
      title: 'Real-Time Data',
      description: 'Live carbon intensity data from ElectricityMap, emission factors from Carbon Interface and Climatiq.',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
    },
    {
      icon: BarChart3,
      title: 'Monte Carlo Simulation',
      description: 'Uncertainty analysis with thousands of simulations to provide confidence intervals and risk assessment.',
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      icon: Shield,
      title: 'Enterprise Ready',
      description: 'Secure API handling, audit trails, and integration with notification systems for production use.',
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
  ]

  const examples = [
    "Compare compute carbon intensity us-east-1 vs eu-west-1 for 200 8-vCPU VMs",
    "Analyze migration of 500 servers from coal-heavy to renewable regions",
    "Calculate annual emissions for our cloud infrastructure with uncertainty",
    "Find the optimal AWS region for minimal carbon footprint",
  ]

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center space-y-6"
      >
        <div className="inline-flex items-center space-x-2 bg-primary-100 text-primary-700 px-4 py-2 rounded-full text-sm font-medium">
          <Sparkles className="w-4 h-4" />
          <span>Powered by Gemini 2.0 Flash</span>
        </div>
        
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight">
          Intelligent Carbon
          <span className="text-gradient block">Analysis & Decisions</span>
        </h1>
        
        <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
          CarbonLens uses advanced AI agents to analyze carbon emissions, compare scenarios, 
          and provide actionable recommendations with real-time data and uncertainty analysis.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4">
          <Link
            to="/analysis"
            className="btn-primary px-8 py-3 text-lg flex items-center space-x-2"
          >
            <Play className="w-5 h-5" />
            <span>Start Analysis</span>
          </Link>
          
          {!isConfigured && (
            <Link
              to="/settings"
              className="btn-outline px-8 py-3 text-lg flex items-center space-x-2"
            >
              <Shield className="w-5 h-5" />
              <span>Setup APIs</span>
            </Link>
          )}
        </div>
      </motion.div>

      {/* Features Grid */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {features.map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 * index }}
            className="card p-6 hover:shadow-lg transition-shadow"
          >
            <div className={`p-3 ${feature.bgColor} rounded-lg w-fit mb-4`}>
              <feature.icon className={`w-6 h-6 ${feature.color}`} />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {feature.title}
            </h3>
            <p className="text-gray-600 text-sm leading-relaxed">
              {feature.description}
            </p>
          </motion.div>
        ))}
      </motion.div>

      {/* Example Queries */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        className="bg-gradient-to-r from-primary-50 to-green-50 rounded-2xl p-8 border border-primary-200"
      >
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Try These Example Queries
          </h2>
          <p className="text-gray-600">
            Natural language prompts that showcase CarbonLens capabilities
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {examples.map((example, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.1 * index }}
              className="bg-white rounded-lg p-4 border border-gray-200 hover:border-primary-300 transition-colors cursor-pointer group"
              onClick={() => {
                // Navigate to analysis page with pre-filled query
                const searchParams = new URLSearchParams({ q: example })
                window.location.href = `/analysis?${searchParams.toString()}`
              }}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-primary-600">
                      {index + 1}
                    </span>
                  </div>
                </div>
                <div className="flex-1">
                  <p className="text-gray-700 text-sm leading-relaxed group-hover:text-gray-900 transition-colors">
                    "{example}"
                  </p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-primary-600 transition-colors" />
              </div>
            </motion.div>
          ))}
        </div>

        <div className="text-center mt-6">
          <Link
            to="/analysis"
            className="inline-flex items-center text-primary-600 hover:text-primary-700 font-medium"
          >
            Start your own analysis
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>
      </motion.div>

      {/* How It Works */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        className="text-center space-y-8"
      >
        <h2 className="text-3xl font-bold text-gray-900">
          How CarbonLens Works
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          {[
            {
              step: '1',
              title: 'Natural Language Input',
              description: 'Describe your carbon analysis needs in plain English',
              icon: Brain,
            },
            {
              step: '2',
              title: 'AI Agent Planning',
              description: 'Gemini 2.0 Flash plans the analysis and selects appropriate tools',
              icon: Zap,
            },
            {
              step: '3',
              title: 'Real Data & Results',
              description: 'Get actionable insights with uncertainty analysis and recommendations',
              icon: CheckCircle,
            },
          ].map((item, index) => (
            <motion.div
              key={item.step}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 * index }}
              className="text-center"
            >
              <div className="relative mb-4">
                <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto">
                  <item.icon className="w-8 h-8 text-primary-600" />
                </div>
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  {item.step}
                </div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {item.title}
              </h3>
              <p className="text-gray-600 text-sm">
                {item.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* CTA Section */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.8 }}
        className="bg-gray-900 rounded-2xl p-8 text-center text-white"
      >
        <Leaf className="w-12 h-12 text-primary-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold mb-4">
          Ready to Optimize Your Carbon Footprint?
        </h2>
        <p className="text-gray-300 mb-6 max-w-2xl mx-auto">
          Start making data-driven decisions about your carbon emissions with AI-powered analysis.
        </p>
        <Link
          to="/analysis"
          className="inline-flex items-center bg-primary-600 hover:bg-primary-700 text-white px-8 py-3 rounded-lg font-medium transition-colors"
        >
          Get Started Now
          <ArrowRight className="w-5 h-5 ml-2" />
        </Link>
      </motion.div>
    </div>
  )
}
