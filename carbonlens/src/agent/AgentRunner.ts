/**
 * Agent runner for managing multiple concurrent tasks
 */

import { AgentOrchestrator, type ConversationStorage } from './AgentOrchestrator';
import type { IGeminiService } from '@/background/services/IGeminiService';
import type { ToolRegistry } from '@/tools/ToolAdapter';
import type { TaskRequest, TaskResult, ConversationEvent, StreamDelta } from '@/shared/types';
import { generateId } from '@/shared/utils';

/**
 * Task execution context
 */
interface TaskContext {
  taskId: string;
  request: TaskRequest;
  orchestrator: AgentOrchestrator;
  startTime: number;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  result?: TaskResult;
  onDelta?: ((delta: StreamDelta) => void) | undefined;
}

/**
 * Conversation storage implementation using chrome.storage.local
 */
export class ChromeConversationStorage implements ConversationStorage {
  private readonly STORAGE_KEY = 'carbonlens_conversations';
  private readonly MAX_EVENTS = 10000; // Limit storage size

  /**
   * Add conversation event
   */
  public async addEvent(event: ConversationEvent): Promise<void> {
    return new Promise((resolve, reject) => {
      chrome.storage.local.get([this.STORAGE_KEY], (result) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }

        const events: ConversationEvent[] = result[this.STORAGE_KEY] || [];
        events.push(event);

        // Keep only recent events to prevent storage overflow
        if (events.length > this.MAX_EVENTS) {
          events.splice(0, events.length - this.MAX_EVENTS);
        }

        chrome.storage.local.set({ [this.STORAGE_KEY]: events }, () => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else {
            resolve();
          }
        });
      });
    });
  }

  /**
   * Get events for a specific task
   */
  public async getEvents(taskId: string): Promise<ConversationEvent[]> {
    return new Promise((resolve, reject) => {
      chrome.storage.local.get([this.STORAGE_KEY], (result) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }

        const events: ConversationEvent[] = result[this.STORAGE_KEY] || [];
        const taskEvents = events.filter(event => event.taskId === taskId);
        resolve(taskEvents.sort((a, b) => a.timestamp - b.timestamp));
      });
    });
  }

  /**
   * Export logs for a task as formatted text
   */
  public async exportLogs(taskId: string): Promise<string> {
    const events = await this.getEvents(taskId);
    
    let logText = `CarbonLens Task Log - ${taskId}\n`;
    logText += `Generated: ${new Date().toISOString()}\n`;
    logText += '='.repeat(80) + '\n\n';

    for (const event of events) {
      const timestamp = new Date(event.timestamp).toISOString();
      logText += `[${timestamp}] ${event.type.toUpperCase()}\n`;
      
      if (typeof event.data === 'string') {
        logText += `${event.data}\n`;
      } else {
        logText += `${JSON.stringify(event.data, null, 2)}\n`;
      }
      
      logText += '-'.repeat(40) + '\n';
    }

    return logText;
  }

  /**
   * Clear all conversation data
   */
  public async clearAll(): Promise<void> {
    return new Promise((resolve, reject) => {
      chrome.storage.local.remove([this.STORAGE_KEY], () => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve();
        }
      });
    });
  }
}

/**
 * Agent runner for managing task execution
 */
export class AgentRunner {
  private activeTasks = new Map<string, TaskContext>();
  private conversationStorage: ConversationStorage;

  constructor(
    private geminiService: IGeminiService,
    private toolRegistry: ToolRegistry
  ) {
    this.conversationStorage = new ChromeConversationStorage();
  }

  /**
   * Start a new task
   */
  public async startTask(
    request: TaskRequest,
    onDelta?: (delta: StreamDelta) => void
  ): Promise<string> {
    const taskId = generateId();
    
    const orchestrator = new AgentOrchestrator(
      this.geminiService,
      this.toolRegistry,
      this.conversationStorage
    );

    const context: TaskContext = {
      taskId,
      request,
      orchestrator,
      startTime: Date.now(),
      status: 'running',
      onDelta,
    };

    this.activeTasks.set(taskId, context);

    // Start task execution asynchronously
    this.executeTask(context).catch(error => {
      console.error(`Task ${taskId} failed:`, error);
      context.status = 'failed';
      context.result = {
        taskId,
        success: false,
        error: error.message,
        metadata: {
          startTime: context.startTime,
          endTime: Date.now(),
          totalSteps: 0,
          llmCalls: 0,
          toolCalls: 0,
        },
      };
    });

    return taskId;
  }

  /**
   * Execute task in background
   */
  private async executeTask(context: TaskContext): Promise<void> {
    try {
      const result = await context.orchestrator.runTask(context.request, context.onDelta);
      
      context.result = result;
      context.status = result.success ? 'completed' : 'failed';
      
      // Emit final delta
      if (context.onDelta) {
        context.onDelta({
          type: 'final',
          content: result.success ? 'Task completed successfully' : `Task failed: ${result.error}`,
          data: result,
        });
      }
    } catch (error) {
      context.status = 'failed';
      context.result = {
        taskId: context.taskId,
        success: false,
        error: (error as Error).message,
        metadata: {
          startTime: context.startTime,
          endTime: Date.now(),
          totalSteps: 0,
          llmCalls: 0,
          toolCalls: 0,
        },
      };

      if (context.onDelta) {
        context.onDelta({
          type: 'error',
          content: `Task execution failed: ${(error as Error).message}`,
        });
      }
    }
  }

  /**
   * Get task status
   */
  public getTaskStatus(taskId: string): TaskContext | undefined {
    return this.activeTasks.get(taskId);
  }

  /**
   * Get task result
   */
  public getTaskResult(taskId: string): TaskResult | undefined {
    const context = this.activeTasks.get(taskId);
    return context?.result;
  }

  /**
   * Cancel a running task
   */
  public cancelTask(taskId: string): boolean {
    const context = this.activeTasks.get(taskId);
    if (context && context.status === 'running') {
      context.status = 'cancelled';
      return true;
    }
    return false;
  }

  /**
   * Get all active tasks
   */
  public getActiveTasks(): TaskContext[] {
    return Array.from(this.activeTasks.values()).filter(ctx => ctx.status === 'running');
  }

  /**
   * Clean up completed tasks
   */
  public cleanupCompletedTasks(): void {
    const cutoffTime = Date.now() - 24 * 60 * 60 * 1000; // 24 hours ago
    
    for (const [taskId, context] of this.activeTasks.entries()) {
      if (context.status !== 'running' && context.startTime < cutoffTime) {
        this.activeTasks.delete(taskId);
      }
    }
  }

  /**
   * Export task logs
   */
  public async exportTaskLogs(taskId: string): Promise<string> {
    return await this.conversationStorage.exportLogs(taskId);
  }

  /**
   * Get task conversation history
   */
  public async getTaskHistory(taskId: string): Promise<ConversationEvent[]> {
    return await this.conversationStorage.getEvents(taskId);
  }
}
