/**
 * Mock implementation of Gemini service for testing
 */

import type { IGeminiService, GeminiOptions } from './IGeminiService';
import type { AgentPlan } from '@/shared/types';
import { delay } from '@/shared/utils';

/**
 * Mock Gemini service for deterministic testing
 */
export class GeminiMock implements IGeminiService {
  private callCount = 0;
  private planResponses: AgentPlan[] = [
    {
      type: 'tool_call',
      tool: 'CarbonApiTool',
      args: { region: 'ap-south1', service: 'compute', instanceType: '8-vCPU' },
      reasoning: 'Need to get carbon factors for ap-south1 compute instances',
    },
    {
      type: 'tool_call',
      tool: 'CarbonApiTool',
      args: { region: 'eu-west1', service: 'compute', instanceType: '8-vCPU' },
      reasoning: 'Need to get carbon factors for eu-west1 compute instances for comparison',
    },
    {
      type: 'tool_call',
      tool: 'EmissionEstimatorTool',
      args: {
        scenarios: [
          { region: 'ap-south1', instances: 200, factor: 0.82 },
          { region: 'eu-west1', instances: 200, factor: 0.35 },
        ],
        samples: 1000,
      },
      reasoning: 'Performing Monte Carlo analysis to compare emissions between regions',
    },
    {
      type: 'final',
      response: `# Carbon Emission Comparison: ap-south1 vs eu-west1

## Summary
For 200 8-vCPU VM instances, eu-west1 has significantly lower carbon emissions than ap-south1.

## Results
- **ap-south1**: 164 ± 12 kg CO2e/day (95% CI: 152-176 kg)
- **eu-west1**: 70 ± 8 kg CO2e/day (95% CI: 62-78 kg)
- **Difference**: 94 kg CO2e/day (57% reduction with eu-west1)

## Recommendation
Choose eu-west1 for lower environmental impact. The carbon footprint is 57% lower due to cleaner electricity grid mix.

## Data Sources
- Carbon factors from Carbon Interface API
- Grid intensity from ElectricityMap
- Monte Carlo analysis with 1000 samples`,
      reasoning: 'Provided comprehensive comparison with quantified results and clear recommendation',
    },
  ];

  /**
   * Generate mock agent plan
   */
  public async plan(
    conversationHistory: string[],
    _options?: GeminiOptions
  ): Promise<AgentPlan> {
    // Simulate API delay
    await delay(500 + Math.random() * 1000);

    // Return different responses based on call count to simulate conversation flow
    const responseIndex = Math.min(this.callCount, this.planResponses.length - 1);
    this.callCount++;

    const response = this.planResponses[responseIndex];
    if (!response) {
      return this.planResponses[this.planResponses.length - 1]!;
    }
    return { ...response };
  }

  /**
   * Generate mock summary
   */
  public async summarize(text: string, _options?: GeminiOptions): Promise<string> {
    await delay(300 + Math.random() * 500);

    // Generate deterministic summary based on text length
    const wordCount = text.split(' ').length;
    
    if (wordCount < 100) {
      return 'This content discusses carbon emissions and environmental impact considerations for technology decisions.';
    } else if (wordCount < 500) {
      return `This ${wordCount}-word content covers carbon emission factors, regional differences in electricity grid intensity, and environmental impact assessment methodologies. Key topics include lifecycle analysis, renewable energy adoption, and sustainability metrics for technology infrastructure.`;
    } else {
      return `Comprehensive analysis of carbon emissions spanning ${wordCount} words. The content examines regional variations in carbon intensity, comparative lifecycle assessments, and decision frameworks for sustainable technology choices. Discusses grid decarbonization trends, emission factor databases, and Monte Carlo uncertainty analysis methods. Provides actionable insights for reducing environmental impact through informed technology and location decisions.`;
    }
  }

  /**
   * Stream mock agent plan
   */
  public async streamPlan(
    conversationHistory: string[],
    onDelta: (chunk: string) => void,
    options?: GeminiOptions
  ): Promise<void> {
    // Get the plan that would be returned
    const plan = await this.plan(conversationHistory, options);
    const planText = JSON.stringify(plan, null, 2);
    
    // Stream it character by character
    for (let i = 0; i < planText.length; i += 3) {
      const chunk = planText.slice(i, i + 3);
      onDelta(chunk);
      await delay(50);
    }
  }

  /**
   * Mock configuration check
   */
  public async isConfigured(): Promise<boolean> {
    return true; // Mock is always "configured"
  }

  /**
   * Reset call count for testing
   */
  public reset(): void {
    this.callCount = 0;
  }

  /**
   * Set custom plan responses for testing
   */
  public setPlanResponses(responses: AgentPlan[]): void {
    this.planResponses = responses;
    this.callCount = 0;
  }
}
