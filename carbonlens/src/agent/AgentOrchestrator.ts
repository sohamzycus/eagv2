/**
 * Agent orchestrator for managing task execution flow
 */

import type { IGeminiService } from '@/background/services/IGeminiService';
import type { ToolRegistry } from '@/tools/ToolAdapter';
import type { 
  TaskRequest, 
  TaskResult, 
  AgentPlan, 
  ToolResult, 
  ConversationEvent, 
  StreamDelta 
} from '@/shared/types';
import { generateId, retryWithBackoff } from '@/shared/utils';

/**
 * Conversation storage interface
 */
export interface ConversationStorage {
  addEvent(event: ConversationEvent): Promise<void>;
  getEvents(taskId: string): Promise<ConversationEvent[]>;
  exportLogs(taskId: string): Promise<string>;
}

/**
 * Agent orchestrator implementing the main execution loop
 */
export class AgentOrchestrator {
  private readonly maxSteps = 20;
  private readonly maxRetries = 3;

  constructor(
    private geminiService: IGeminiService,
    private toolRegistry: ToolRegistry,
    private conversationStorage: ConversationStorage
  ) {}

  /**
   * Run a task with streaming updates
   */
  public async runTask(
    taskRequest: TaskRequest,
    onDelta?: (delta: StreamDelta) => void
  ): Promise<TaskResult> {
    const taskId = generateId();
    const startTime = Date.now();
    
    let totalSteps = 0;
    let llmCalls = 0;
    let toolCalls = 0;

    try {
      // Log initial user prompt
      await this.logEvent(taskId, 'user_prompt', taskRequest.prompt);
      
      // Initialize conversation history
      const conversationHistory = [
        `User Request: ${taskRequest.prompt}`,
        `Task Parameters: ${JSON.stringify({
          samples: taskRequest.samples,
          useBackend: taskRequest.useBackend,
          notifyChannel: taskRequest.notifyChannel?.name,
        })}`,
      ];

      this.emitDelta(onDelta, 'plan', 'Starting task analysis...');

      // Main execution loop
      while (totalSteps < this.maxSteps) {
        totalSteps++;
        
        // Get plan from LLM
        this.emitDelta(onDelta, 'plan', `Step ${totalSteps}: Analyzing next action...`);
        
        const plan = await retryWithBackoff(async () => {
          llmCalls++;
          return await this.geminiService.plan(conversationHistory);
        }, this.maxRetries);

        await this.logEvent(taskId, 'llm_plan', plan);
        
        // Check if this is a final response
        if (plan.type === 'final') {
          this.emitDelta(onDelta, 'final', plan.response || 'Task completed');
          
          await this.logEvent(taskId, 'final', {
            response: plan.response,
            reasoning: plan.reasoning,
          });

          // Send notification if configured
          if (taskRequest.notifyChannel) {
            await this.sendNotification(taskRequest, plan.response || 'Task completed');
          }

          return {
            taskId,
            success: true,
            result: {
              response: plan.response,
              reasoning: plan.reasoning,
              conversationHistory,
            },
            metadata: {
              startTime,
              endTime: Date.now(),
              totalSteps,
              llmCalls,
              toolCalls,
            },
          };
        }

        // Execute tool call
        if (plan.type === 'tool_call' && plan.tool && plan.args) {
          this.emitDelta(onDelta, 'tool_call', `Executing ${plan.tool}...`);
          
          await this.logEvent(taskId, 'tool_call', {
            tool: plan.tool,
            args: plan.args,
            reasoning: plan.reasoning,
          });

          const toolResult = await retryWithBackoff(async () => {
            toolCalls++;
            return await this.toolRegistry.execute(plan.tool!, plan.args!);
          }, this.maxRetries);

          await this.logEvent(taskId, 'tool_result', toolResult);

          this.emitDelta(onDelta, 'tool_result', 
            toolResult.success ? 'Tool execution completed' : `Tool error: ${toolResult.error}`
          );

          // Add tool result to conversation history
          conversationHistory.push(
            `Tool Call: ${plan.tool}(${JSON.stringify(plan.args)})`,
            `Tool Result: ${JSON.stringify(toolResult, null, 2)}`
          );

          // If tool failed, add error context
          if (!toolResult.success) {
            conversationHistory.push(
              `Note: The tool call failed with error: ${toolResult.error}. Please try a different approach or tool.`
            );
          }
        } else {
          // Invalid plan format - request JSON formatting
          conversationHistory.push(
            'Error: Invalid plan format received. Please respond with valid JSON in the specified format.'
          );
          this.emitDelta(onDelta, 'plan', 'Requesting proper JSON format...');
        }
      }

      // Max steps reached without completion
      const errorMessage = `Task exceeded maximum steps (${this.maxSteps}) without completion`;
      await this.logEvent(taskId, 'final', { error: errorMessage });
      
      return {
        taskId,
        success: false,
        error: errorMessage,
        metadata: {
          startTime,
          endTime: Date.now(),
          totalSteps,
          llmCalls,
          toolCalls,
        },
      };

    } catch (error) {
      const errorMessage = `Task execution failed: ${(error as Error).message}`;
      await this.logEvent(taskId, 'final', { error: errorMessage });
      
      this.emitDelta(onDelta, 'error', errorMessage);
      
      return {
        taskId,
        success: false,
        error: errorMessage,
        metadata: {
          startTime,
          endTime: Date.now(),
          totalSteps,
          llmCalls,
          toolCalls,
        },
      };
    }
  }

  /**
   * Log conversation event
   */
  private async logEvent(
    taskId: string,
    type: ConversationEvent['type'],
    data: any
  ): Promise<void> {
    const event: ConversationEvent = {
      id: generateId(),
      taskId,
      type,
      timestamp: Date.now(),
      data,
    };

    await this.conversationStorage.addEvent(event);
  }

  /**
   * Emit streaming delta
   */
  private emitDelta(
    onDelta: ((delta: StreamDelta) => void) | undefined,
    type: StreamDelta['type'],
    content: string,
    data?: any
  ): void {
    if (onDelta) {
      onDelta({ type, content, data });
    }
  }

  /**
   * Send notification if configured
   */
  private async sendNotification(taskRequest: TaskRequest, result: string): Promise<void> {
    if (!taskRequest.notifyChannel) return;

    try {
      const notifierTool = this.toolRegistry.get('NotifierTool');
      if (notifierTool) {
        await notifierTool.execute({
          message: `CarbonLens task completed: ${result.substring(0, 200)}...`,
          title: 'CarbonLens Task Complete',
          channel: taskRequest.notifyChannel.name,
          priority: 'normal',
          data: {
            taskPrompt: taskRequest.prompt,
            completedAt: new Date().toISOString(),
          },
        });
      }
    } catch (error) {
      console.error('Failed to send notification:', error);
      // Don't fail the task if notification fails
    }
  }

  /**
   * Get task conversation history
   */
  public async getTaskHistory(taskId: string): Promise<ConversationEvent[]> {
    return await this.conversationStorage.getEvents(taskId);
  }

  /**
   * Export task logs
   */
  public async exportTaskLogs(taskId: string): Promise<string> {
    return await this.conversationStorage.exportLogs(taskId);
  }
}
