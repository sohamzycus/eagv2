/**
 * Electricity intensity tool for regional grid data
 */

import { BaseToolAdapter } from './ToolAdapter';
import type { ToolResult, GridIntensity } from '@/shared/types';
import { retryWithBackoff } from '@/shared/utils';

/**
 * Electricity intensity tool for querying regional grid carbon intensity
 */
export class ElectricityIntensityTool extends BaseToolAdapter {
  public readonly name = 'ElectricityIntensityTool';
  public readonly description = 'Get regional electricity grid carbon intensity data';
  public readonly schema = {
    type: 'object',
    properties: {
      region: {
        type: 'string',
        description: 'Region code or name (e.g., UK, DE, US-CA, etc.)',
      },
      forecast: {
        type: 'boolean',
        description: 'Whether to include forecast data',
        default: false,
      },
      hours: {
        type: 'integer',
        description: 'Number of hours of data to retrieve',
        minimum: 1,
        maximum: 168,
        default: 24,
      },
    },
    required: ['region'],
  };

  constructor(
    private backendUrl?: string,
    private apiKey?: string,
    private useMock: boolean = true
  ) {
    super();
  }

  public async execute(args: Record<string, any>): Promise<ToolResult> {
    if (!this.validateArgs(args)) {
      return this.createErrorResult('Invalid arguments provided');
    }

    const { region, forecast = false, hours = 24 } = args;

    try {
      if (this.useMock) {
        return this.getMockGridIntensity(region, forecast, hours);
      }

      if (this.backendUrl) {
        return await this.queryViaBackend(region, forecast, hours);
      } else {
        return this.createErrorResult('No backend URL configured for electricity intensity data');
      }
    } catch (error) {
      return this.createErrorResult(`Electricity intensity query failed: ${(error as Error).message}`);
    }
  }

  private async queryViaBackend(region: string, forecast: boolean, hours: number): Promise<ToolResult> {
    const response = await retryWithBackoff(async () => {
      const res = await fetch(`${this.backendUrl}/api/electricity/intensity`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ region, forecast, hours }),
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

  private getMockGridIntensity(region: string, forecast: boolean, hours: number): ToolResult {
    // Mock regional grid intensities (g CO2e/kWh)
    const regionIntensities: Record<string, { base: number; renewable: number }> = {
      'UK': { base: 180, renewable: 45 },
      'DE': { base: 350, renewable: 55 },
      'FR': { base: 60, renewable: 85 },
      'US-CA': { base: 250, renewable: 35 },
      'US-TX': { base: 450, renewable: 25 },
      'NO': { base: 20, renewable: 98 },
      'PL': { base: 650, renewable: 15 },
      'IN': { base: 820, renewable: 12 },
      'CN': { base: 550, renewable: 28 },
      'AU': { base: 480, renewable: 32 },
    };

    const regionData = regionIntensities[region.toUpperCase()] || { base: 400, renewable: 30 };
    const currentTime = Date.now();
    
    // Generate hourly data with realistic variation
    const data: GridIntensity[] = [];
    for (let i = 0; i < hours; i++) {
      const hour = new Date(currentTime + i * 3600000).getHours();
      
      // Simulate daily pattern (lower at night, higher during peak hours)
      const dailyMultiplier = 0.7 + 0.6 * Math.sin((hour - 6) * Math.PI / 12);
      
      // Add some random variation
      const randomVariation = 0.9 + 0.2 * Math.random();
      
      const intensity = Math.round(regionData.base * dailyMultiplier * randomVariation);
      
      data.push({
        region,
        intensity,
        renewablePercent: regionData.renewable + (Math.random() - 0.5) * 10,
        timestamp: currentTime + i * 3600000,
        source: 'CarbonLens Mock Grid Data',
      });
    }

    // Add forecast data if requested
    if (forecast) {
      for (let i = hours; i < hours + 24; i++) {
        const hour = new Date(currentTime + i * 3600000).getHours();
        const dailyMultiplier = 0.7 + 0.6 * Math.sin((hour - 6) * Math.PI / 12);
        const randomVariation = 0.9 + 0.2 * Math.random();
        const intensity = Math.round(regionData.base * dailyMultiplier * randomVariation);
        
        data.push({
          region,
          intensity,
          renewablePercent: regionData.renewable + (Math.random() - 0.5) * 10,
          timestamp: currentTime + i * 3600000,
          source: 'CarbonLens Mock Grid Forecast',
        });
      }
    }

    const avgIntensity = data.reduce((sum, d) => sum + d.intensity, 0) / data.length;
    const avgRenewable = data.reduce((sum, d) => sum + (d.renewablePercent || 0), 0) / data.length;

    return this.createSuccessResult({
      region,
      data,
      summary: {
        averageIntensity: Math.round(avgIntensity),
        averageRenewable: Math.round(avgRenewable),
        minIntensity: Math.min(...data.map(d => d.intensity)),
        maxIntensity: Math.max(...data.map(d => d.intensity)),
        dataPoints: data.length,
      },
    }, {
      source: 'mock',
      cached: false,
      forecast: forecast,
      hours: data.length,
    });
  }
}
