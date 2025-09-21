/**
 * Unit tests for AgentOrchestrator
 */

import { AgentOrchestrator, type ConversationStorage } from '@/agent/AgentOrchestrator';
import { GeminiMock } from '@/background/services/GeminiMock';
import { ToolRegistry } from '@/tools/ToolAdapter';
import { EmissionEstimatorTool } from '@/tools/EmissionEstimatorTool';
import type { ConversationEvent, TaskRequest } from '@/shared/types';

// Mock conversation storage
class MockConversationStorage implements ConversationStorage {
  private events: ConversationEvent[] = [];

  async addEvent(event: ConversationEvent): Promise<void> {
    this.events.push(event);
  }

  async getEvents(taskId: string): Promise<ConversationEvent[]> {
    return this.events.filter(e => e.taskId === taskId);
  }

  async exportLogs(taskId: string): Promise<string> {
    const events = await this.getEvents(taskId);
    return events.map(e => `${e.type}: ${JSON.stringify(e.data)}`).join('\n');
  }

  clear(): void {
    this.events = [];
  }
}

describe('AgentOrchestrator', () => {
  let orchestrator: AgentOrchestrator;
  let geminiMock: GeminiMock;
  let toolRegistry: ToolRegistry;
  let conversationStorage: MockConversationStorage;

  beforeEach(() => {
    geminiMock = new GeminiMock();
    toolRegistry = new ToolRegistry();
    conversationStorage = new MockConversationStorage();
    
    // Register test tools
    toolRegistry.register(new EmissionEstimatorTool());
    
    orchestrator = new AgentOrchestrator(geminiMock, toolRegistry, conversationStorage);
  });

  afterEach(() => {
    conversationStorage.clear();
    geminiMock.reset();
  });

  describe('runTask', () => {
    it('should execute a simple task successfully', async () => {
      const taskRequest: TaskRequest = {
        prompt: 'Compare carbon emissions between two regions',
        samples: 1000,
      };

      const result = await orchestrator.runTask(taskRequest);

      expect(result.success).toBe(true);
      expect(result.taskId).toBeDefined();
      expect(result.result?.response).toContain('Carbon Emission Comparison');
      expect(result.metadata.totalSteps).toBeGreaterThan(0);
      expect(result.metadata.llmCalls).toBeGreaterThan(0);
    });

    it('should handle tool execution', async () => {
      const taskRequest: TaskRequest = {
        prompt: 'Calculate emissions for 100 VMs',
        samples: 500,
      };

      const deltaMessages: string[] = [];
      const result = await orchestrator.runTask(taskRequest, (delta) => {
        deltaMessages.push(delta.content);
      });

      expect(result.success).toBe(true);
      expect(deltaMessages.length).toBeGreaterThan(0);
      expect(deltaMessages.some(msg => msg.includes('Executing'))).toBe(true);
    });

    it('should log conversation events', async () => {
      const taskRequest: TaskRequest = {
        prompt: 'Test task for logging',
      };

      const result = await orchestrator.runTask(taskRequest);
      const events = await conversationStorage.getEvents(result.taskId);

      expect(events.length).toBeGreaterThan(0);
      expect(events[0].type).toBe('user_prompt');
      expect(events[0].data).toBe(taskRequest.prompt);
    });

    it('should export task logs', async () => {
      const taskRequest: TaskRequest = {
        prompt: 'Test task for export',
      };

      const result = await orchestrator.runTask(taskRequest);
      const logs = await orchestrator.exportTaskLogs(result.taskId);

      expect(logs).toContain('user_prompt');
      expect(logs).toContain(taskRequest.prompt);
    });

    it('should handle maximum steps limit', async () => {
      // Set up mock to never return final response
      geminiMock.setPlanResponses([
        {
          type: 'tool_call',
          tool: 'EmissionEstimatorTool',
          args: { scenarios: [], samples: 100 },
          reasoning: 'Infinite loop test',
        },
      ]);

      const taskRequest: TaskRequest = {
        prompt: 'Task that should hit max steps',
      };

      const result = await orchestrator.runTask(taskRequest);

      expect(result.success).toBe(false);
      expect(result.error).toContain('maximum steps');
    });

    it('should handle tool execution errors gracefully', async () => {
      // Set up mock to call non-existent tool
      geminiMock.setPlanResponses([
        {
          type: 'tool_call',
          tool: 'NonExistentTool',
          args: {},
          reasoning: 'Testing error handling',
        },
        {
          type: 'final',
          response: 'Handled error and completed',
          reasoning: 'Recovered from tool error',
        },
      ]);

      const taskRequest: TaskRequest = {
        prompt: 'Task with tool error',
      };

      const result = await orchestrator.runTask(taskRequest);

      expect(result.success).toBe(true);
      expect(result.result?.response).toContain('Handled error');
    });
  });

  describe('getTaskHistory', () => {
    it('should retrieve task conversation history', async () => {
      const taskRequest: TaskRequest = {
        prompt: 'Test task for history',
      };

      const result = await orchestrator.runTask(taskRequest);
      const history = await orchestrator.getTaskHistory(result.taskId);

      expect(history.length).toBeGreaterThan(0);
      expect(history[0].taskId).toBe(result.taskId);
      expect(history[0].type).toBe('user_prompt');
    });
  });
});
