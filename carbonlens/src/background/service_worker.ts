/**
 * CarbonLens service worker
 */

import { buildContainer, type DIContainer } from './di';
import type { TaskRequest, ExtensionConfig, StreamDelta } from '@/shared/types';

// Global container instance
let container: DIContainer;

// Initialize container with default mock configuration
initializeContainer();

/**
 * Initialize DI container
 */
async function initializeContainer(): Promise<void> {
  try {
    const config = await getExtensionConfig();
    container = buildContainer(config);
    console.log('CarbonLens service worker initialized');
  } catch (error) {
    console.error('Failed to initialize service worker:', error);
    // Fallback to mock configuration
    container = buildContainer({
      useRealMode: false,
      notificationChannels: [],
    });
  }
}

/**
 * Get extension configuration from storage
 */
async function getExtensionConfig(): Promise<ExtensionConfig> {
  return new Promise((resolve) => {
    chrome.storage.local.get(['carbonlens_config'], (result) => {
      const config: ExtensionConfig = result.carbonlens_config || {
        useRealMode: false,
        notificationChannels: [],
      };
      resolve(config);
    });
  });
}

/**
 * Handle runtime messages
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      switch (message.action) {
        case 'startTask':
          const taskRequest: TaskRequest = message.taskRequest;
          const taskId = await container.agentRunner.startTask(taskRequest);
          sendResponse({ success: true, taskId });
          break;

        case 'getTaskStatus':
          const status = container.agentRunner.getTaskStatus(message.taskId);
          sendResponse({ success: true, status });
          break;

        case 'getTaskResult':
          const result = container.agentRunner.getTaskResult(message.taskId);
          sendResponse({ success: true, result });
          break;

        case 'cancelTask':
          const cancelled = container.agentRunner.cancelTask(message.taskId);
          sendResponse({ success: true, cancelled });
          break;

        case 'exportTaskLogs':
          const logs = await container.agentRunner.exportTaskLogs(message.taskId);
          sendResponse({ success: true, logs });
          break;

        case 'getTaskHistory':
          const history = await container.agentRunner.getTaskHistory(message.taskId);
          sendResponse({ success: true, history });
          break;

        case 'updateConfig':
          const newConfig: ExtensionConfig = message.config;
          await saveExtensionConfig(newConfig);
          container = buildContainer(newConfig);
          sendResponse({ success: true });
          break;

        case 'getConfig':
          const currentConfig = await getExtensionConfig();
          sendResponse({ success: true, config: currentConfig });
          break;

        case 'getActiveTasks':
          const activeTasks = container.agentRunner.getActiveTasks();
          sendResponse({ success: true, tasks: activeTasks });
          break;

        default:
          sendResponse({ success: false, error: 'Unknown action' });
      }
    } catch (error) {
      console.error('Service worker message handler error:', error);
      sendResponse({ success: false, error: (error as Error).message });
    }
  })();
  
  return true; // Keep message channel open for async response
});

/**
 * Handle streaming connections
 */
chrome.runtime.onConnect.addListener((port) => {
  if (port.name === 'carbonlens-stream') {
    port.onMessage.addListener(async (message) => {
      if (message.action === 'startStreamingTask') {
        try {
          const taskRequest: TaskRequest = message.taskRequest;
          
          // Start task with streaming updates
          const taskId = await container.agentRunner.startTask(
            taskRequest,
            (delta: StreamDelta) => {
              port.postMessage({
                type: 'delta',
                taskId,
                delta,
              });
            }
          );

          port.postMessage({
            type: 'started',
            taskId,
          });
        } catch (error) {
          port.postMessage({
            type: 'error',
            error: (error as Error).message,
          });
        }
      }
    });

    port.onDisconnect.addListener(() => {
      console.log('Streaming port disconnected');
    });
  }
});

/**
 * Save extension configuration
 */
async function saveExtensionConfig(config: ExtensionConfig): Promise<void> {
  return new Promise((resolve, reject) => {
    chrome.storage.local.set({ carbonlens_config: config }, () => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve();
      }
    });
  });
}

/**
 * Periodic cleanup of completed tasks
 */
setInterval(() => {
  if (container?.agentRunner) {
    container.agentRunner.cleanupCompletedTasks();
  }
}, 60 * 60 * 1000); // Every hour

/**
 * Handle extension installation
 */
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('CarbonLens extension installed');
    // Set default configuration
    saveExtensionConfig({
      useRealMode: false,
      notificationChannels: [],
    });
  }
});
