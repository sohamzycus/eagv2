/**
 * Emission estimator tool for Monte Carlo calculations
 */

import { BaseToolAdapter } from './ToolAdapter';
import type { ToolResult, EmissionEstimate } from '@/shared/types';
import { calculateConfidenceInterval } from '@/shared/utils';

/**
 * Scenario for emission estimation
 */
interface EmissionScenario {
  /** Scenario name/identifier */
  name?: string;
  /** Number of instances/units */
  instances: number;
  /** Carbon factor (kg CO2e per unit per hour) */
  factor: number;
  /** Usage hours per day */
  hoursPerDay?: number;
  /** Uncertainty in factor (standard deviation as fraction) */
  uncertainty?: number;
}

/**
 * Emission estimator tool using Monte Carlo simulation
 */
export class EmissionEstimatorTool extends BaseToolAdapter {
  public readonly name = 'EmissionEstimatorTool';
  public readonly description = 'Perform Monte Carlo emission calculations with uncertainty analysis';
  public readonly schema = {
    type: 'object',
    properties: {
      scenarios: {
        type: 'array',
        description: 'Array of emission scenarios to analyze',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string', description: 'Scenario identifier' },
            instances: { type: 'integer', description: 'Number of instances/units', minimum: 1 },
            factor: { type: 'number', description: 'Carbon factor (kg CO2e/unit/hour)', minimum: 0 },
            hoursPerDay: { type: 'number', description: 'Usage hours per day', minimum: 0, maximum: 24 },
            uncertainty: { type: 'number', description: 'Uncertainty as fraction (0-1)', minimum: 0, maximum: 1 },
          },
          required: ['instances', 'factor'],
        },
      },
      samples: {
        type: 'integer',
        description: 'Number of Monte Carlo samples',
        minimum: 100,
        maximum: 100000,
        default: 10000,
      },
      timeframe: {
        type: 'string',
        description: 'Timeframe for calculation',
        enum: ['hour', 'day', 'week', 'month', 'year'],
        default: 'day',
      },
    },
    required: ['scenarios'],
  };

  /**
   * Execute emission estimation
   */
  public async execute(args: Record<string, any>): Promise<ToolResult> {
    if (!this.validateArgs(args)) {
      return this.createErrorResult('Invalid arguments provided');
    }

    const { scenarios, samples = 10000, timeframe = 'day' } = args;

    try {
      const results: Record<string, EmissionEstimate> = {};
      
      for (const scenario of scenarios) {
        const estimate = this.calculateEmissions(scenario, samples, timeframe);
        const scenarioName = scenario.name || `Scenario ${Object.keys(results).length + 1}`;
        results[scenarioName] = estimate;
      }

      // Calculate comparison metrics if multiple scenarios
      const comparison = scenarios.length > 1 ? this.calculateComparison(results) : null;

      return this.createSuccessResult({
        estimates: results,
        comparison,
        parameters: { samples, timeframe },
      }, {
        samples,
        scenarios: scenarios.length,
      });
    } catch (error) {
      return this.createErrorResult(`Emission calculation failed: ${(error as Error).message}`);
    }
  }

  /**
   * Calculate emissions for a single scenario using Monte Carlo
   */
  private calculateEmissions(
    scenario: EmissionScenario,
    samples: number,
    timeframe: string
  ): EmissionEstimate {
    const { instances, factor, hoursPerDay = 24, uncertainty = 0.1 } = scenario;
    
    // Time multiplier based on timeframe
    const timeMultipliers: Record<string, number> = {
      hour: 1,
      day: hoursPerDay,
      week: hoursPerDay * 7,
      month: hoursPerDay * 30,
      year: hoursPerDay * 365,
    };
    
    const timeMultiplier = timeMultipliers[timeframe] || hoursPerDay;
    
    // Monte Carlo simulation
    const emissions: number[] = [];
    const breakdown: Record<string, number[]> = {
      compute: [],
      uncertainty: [],
    };
    
    for (let i = 0; i < samples; i++) {
      // Sample factor with uncertainty (log-normal distribution)
      const factorSample = this.sampleLogNormal(factor, factor * uncertainty);
      
      // Calculate emission for this sample
      const emission = instances * factorSample * timeMultiplier;
      emissions.push(emission);
      
      // Track breakdown
      breakdown.compute?.push(emission);
      breakdown.uncertainty?.push(Math.abs(emission - instances * factor * timeMultiplier));
    }
    
    // Calculate statistics
    const mean = emissions.reduce((sum, val) => sum + val, 0) / samples;
    const variance = emissions.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (samples - 1);
    const std = Math.sqrt(variance);
    const confidenceInterval = calculateConfidenceInterval(mean, std);
    
    // Calculate breakdown means
    const breakdownMeans: Record<string, number> = {};
    for (const [key, values] of Object.entries(breakdown)) {
      breakdownMeans[key] = values.reduce((sum, val) => sum + val, 0) / samples;
    }
    
    return {
      mean,
      std,
      unit: `kg CO2e/${timeframe}`,
      confidenceInterval,
      breakdown: breakdownMeans,
      samples,
    };
  }

  /**
   * Sample from log-normal distribution
   */
  private sampleLogNormal(mean: number, std: number): number {
    // Box-Muller transformation for normal distribution
    const u1 = Math.random();
    const u2 = Math.random();
    const z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    
    // Convert to log-normal
    const logMean = Math.log(mean) - 0.5 * Math.log(1 + (std / mean) ** 2);
    const logStd = Math.sqrt(Math.log(1 + (std / mean) ** 2));
    
    return Math.exp(logMean + logStd * z0);
  }

  /**
   * Calculate comparison metrics between scenarios
   */
  private calculateComparison(results: Record<string, EmissionEstimate>): any {
    const scenarios = Object.keys(results);
    if (scenarios.length < 2) return null;
    
    const comparisons: Record<string, any> = {};
    
    // Pairwise comparisons
    for (let i = 0; i < scenarios.length; i++) {
      for (let j = i + 1; j < scenarios.length; j++) {
        const scenario1 = scenarios[i];
        const scenario2 = scenarios[j];
        const result1 = results[scenario1!];
        const result2 = results[scenario2!];
        
        if (!result1 || !result2) continue;
        
        const difference = result2.mean - result1.mean;
        const percentChange = (difference / result1.mean) * 100;
        
        comparisons[`${scenario1}_vs_${scenario2}`] = {
          difference,
          percentChange,
          unit: result1.unit,
          lowerEmission: difference < 0 ? scenario2 : scenario1,
          reduction: Math.abs(percentChange),
        };
      }
    }
    
    // Find best and worst scenarios
    const sortedScenarios = scenarios.sort((a, b) => results[a]!.mean - results[b]!.mean);
    
    return {
      pairwise: comparisons,
      ranking: {
        best: sortedScenarios[0],
        worst: sortedScenarios[sortedScenarios.length - 1],
        order: sortedScenarios,
      },
      totalRange: {
        min: results[sortedScenarios[0]!]!.mean,
        max: results[sortedScenarios[sortedScenarios.length - 1]!]!.mean,
        span: results[sortedScenarios[sortedScenarios.length - 1]!]!.mean - results[sortedScenarios[0]!]!.mean,
      },
    };
  }
}
