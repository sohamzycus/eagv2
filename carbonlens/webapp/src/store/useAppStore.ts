import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { AppState, TaskResult, ApiConfig } from '@/types'

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      currentTask: null,
      taskHistory: [],
      apiConfig: {},
      isConfigured: false,

      setCurrentTask: (task) => set({ currentTask: task }),

      addTaskToHistory: (task) => {
        const { taskHistory } = get()
        set({ 
          taskHistory: [task, ...taskHistory].slice(0, 100) // Keep last 100 tasks
        })
      },

      updateApiConfig: (config) => {
        const currentConfig = get().apiConfig
        const newConfig = { ...currentConfig, ...config }
        const isConfigured = !!(newConfig.gemini && (
          newConfig.carbonInterface || 
          newConfig.climatiq || 
          newConfig.electricityMap
        ))
        
        set({ 
          apiConfig: newConfig,
          isConfigured
        })
      },

      clearHistory: () => set({ taskHistory: [] }),
    }),
    {
      name: 'carbonlens-storage',
      partialize: (state) => ({
        taskHistory: state.taskHistory,
        apiConfig: state.apiConfig,
        isConfigured: state.isConfigured,
      }),
    }
  )
)
