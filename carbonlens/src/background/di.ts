/**
 * Dependency injection container for CarbonLens
 */

import { GeminiService } from './services/GeminiService';
import { GeminiMock } from './services/GeminiMock';
import type { IGeminiService } from './services/IGeminiService';
import { ToolRegistry } from '@/tools/ToolAdapter';
import { CarbonApiTool } from '@/tools/CarbonApiTool';
import { LCADatabaseTool } from '@/tools/LCADatabaseTool';
import { ElectricityIntensityTool } from '@/tools/ElectricityIntensityTool';
import { NewsSearchTool } from '@/tools/NewsSearchTool';
import { EmissionEstimatorTool } from '@/tools/EmissionEstimatorTool';
import { NotifierTool } from '@/tools/NotifierTool';
import { PageExtractorTool } from '@/tools/PageExtractorTool';
import { AgentRunner } from '@/agent/AgentRunner';
import type { ExtensionConfig } from '@/shared/types';

/**
 * Dependency injection container
 */
export interface DIContainer {
  geminiService: IGeminiService;
  toolRegistry: ToolRegistry;
  agentRunner: AgentRunner;
}

/**
 * Build DI container based on configuration
 */
export function buildContainer(config: ExtensionConfig): DIContainer {
  // Initialize Gemini service
  const geminiService: IGeminiService = config.useRealMode && config.apiKeys?.gemini
    ? new GeminiService(config.apiKeys.gemini)
    : new GeminiMock();

  // Initialize tool registry
  const toolRegistry = new ToolRegistry();

  // Register tools
  toolRegistry.register(new CarbonApiTool(
    config.backendUrl,
    config.apiKeys?.carbonInterface,
    !config.useRealMode
  ));

  toolRegistry.register(new LCADatabaseTool());

  toolRegistry.register(new ElectricityIntensityTool(
    config.backendUrl,
    config.apiKeys?.electricityMap,
    !config.useRealMode
  ));

  toolRegistry.register(new NewsSearchTool(
    config.backendUrl,
    config.apiKeys?.newsApi,
    !config.useRealMode
  ));

  toolRegistry.register(new EmissionEstimatorTool());

  toolRegistry.register(new NotifierTool(
    config.backendUrl,
    config.notificationChannels,
    !config.useRealMode
  ));

  toolRegistry.register(new PageExtractorTool());

  // Initialize agent runner
  const agentRunner = new AgentRunner(geminiService, toolRegistry);

  return {
    geminiService,
    toolRegistry,
    agentRunner,
  };
}
