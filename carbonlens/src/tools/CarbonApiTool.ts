/**
 * Carbon API tool for querying emission factors
 */

import { BaseToolAdapter } from './ToolAdapter';
import type { ToolResult, CarbonFactor } from '@/shared/types';
import { retryWithBackoff } from '@/shared/utils';

/**
 * Carbon API tool adapter - queries Carbon Interface or Climatiq APIs
 */
export class CarbonApiTool extends BaseToolAdapter {
  public readonly name = 'CarbonApiTool';
  public readonly description = 'Query carbon emission factors from Carbon Interface or Climatiq APIs';
  public readonly schema = {
    type: 'object',
    properties: {
      service: {
        type: 'string',
        description: 'Service type (compute, storage, network, etc.)',
        enum: ['compute', 'storage', 'network', 'database', 'serverless'],
      },
      region: {
        type: 'string',
        description: 'Cloud region or geographic location',
      },
      instanceType: {
        type: 'string',
        description: 'Instance or resource type',
      },
      provider: {
        type: 'string',
        description: 'Cloud provider (aws, gcp, azure, etc.)',
        enum: ['aws', 'gcp', 'azure', 'alibaba', 'generic'],
      },
    },
    required: ['service', 'region'],
  };

  constructor(
    private backendUrl?: string,
    private apiKey?: string,
    private useMock: boolean = true
  ) {
    super();
  }

  /**
   * Execute carbon factor query
   */
  public async execute(args: Record<string, any>): Promise<ToolResult> {
    if (!this.validateArgs(args)) {
      return this.createErrorResult('Invalid arguments provided');
    }

    const { service, region, instanceType, provider = 'generic' } = args;

    try {
      if (this.useMock) {
        return this.getMockCarbonFactor(service, region, instanceType, provider);
      }

      // Try backend proxy first, then direct API
      if (this.backendUrl) {
        return await this.queryViaBackend(service, region, instanceType, provider);
      } else if (this.apiKey) {
        return await this.queryDirectly(service, region, instanceType, provider);
      } else {
        return this.createErrorResult('No API configuration available (backend URL or API key required)');
      }
    } catch (error) {
      return this.createErrorResult(`Carbon API query failed: ${(error as Error).message}`);
    }
  }

  /**
   * Query via backend proxy
   */
  private async queryViaBackend(
    service: string,
    region: string,
    instanceType: string,
    provider: string
  ): Promise<ToolResult> {
    const response = await retryWithBackoff(async () => {
      const res = await fetch(`${this.backendUrl}/api/carbon/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service, region, instanceType, provider }),
      });

      if (!res.ok) {
        throw new Error(`Backend API error: ${res.status} ${res.statusText}`);
      }

      return res.json();
    });

    return this.createSuccessResult(response.data, {
      source: 'backend-proxy',
      cached: response.cached || false,
    });
  }

  /**
   * Query API directly (not recommended for production)
   */
  private async queryDirectly(
    service: string,
    region: string,
    instanceType: string,
    provider: string
  ): Promise<ToolResult> {
    // This would implement direct Carbon Interface or Climatiq API calls
    // For security reasons, we'll return a warning instead
    return this.createErrorResult(
      'Direct API calls not implemented for security reasons. Please use backend proxy.'
    );
  }

  /**
   * Get mock carbon factor for testing
   */
  private getMockCarbonFactor(
    service: string,
    region: string,
    instanceType: string,
    provider: string
  ): ToolResult {
    // Mock data based on realistic carbon intensities
    const regionFactors: Record<string, number> = {
      'us-east-1': 0.45,
      'us-west-2': 0.25,
      'eu-west-1': 0.35,
      'eu-central-1': 0.55,
      'ap-south-1': 0.82,
      'ap-southeast-1': 0.65,
      'ap-northeast-1': 0.48,
      'ca-central-1': 0.15,
      'sa-east-1': 0.12,
    };

    const serviceMultipliers: Record<string, number> = {
      compute: 1.0,
      storage: 0.1,
      network: 0.05,
      database: 1.2,
      serverless: 0.8,
    };

    const instanceMultipliers: Record<string, number> = {
      '1-vCPU': 0.5,
      '2-vCPU': 1.0,
      '4-vCPU': 2.0,
      '8-vCPU': 4.0,
      '16-vCPU': 8.0,
      '32-vCPU': 16.0,
    };

    const baseFactor = regionFactors[region] || 0.5;
    const serviceMultiplier = serviceMultipliers[service] || 1.0;
    const instanceMultiplier = instanceMultipliers[instanceType] || 1.0;

    const factor: CarbonFactor = {
      value: baseFactor * serviceMultiplier * instanceMultiplier,
      unit: 'kg CO2e/hour',
      source: 'CarbonLens Mock Data',
      region,
      confidence: 0.85,
      updatedAt: Date.now(),
    };

    return this.createSuccessResult(factor, {
      source: 'mock',
      cached: false,
      query: { service, region, instanceType, provider },
    });
  }
}
