import { EmissionResult, ComparisonResult } from '@/types'

export class EmissionCalculator {
  /**
   * Perform Monte Carlo simulation for emission calculations
   */
  async calculateEmissions(params: any, samples = 1000): Promise<EmissionResult> {
    const {
      activity,
      amount,
      unit,
      emissionFactor,
      uncertainty = 0.1,
      timeMultiplier = 1,
      instances = 1,
    } = params

    const results: number[] = []
    const breakdown = {
      categories: ['compute', 'storage', 'network'],
      values: [] as number[],
      compute: [] as number[],
      uncertainty: [] as number[],
    }

    // Monte Carlo simulation
    for (let i = 0; i < samples; i++) {
      // Add uncertainty to emission factor
      const factor = this.addUncertainty(emissionFactor, uncertainty)
      const emission = amount * factor * timeMultiplier * instances
      
      results.push(emission)
      breakdown.compute.push(emission)
      breakdown.uncertainty.push(Math.abs(emission - amount * emissionFactor * timeMultiplier * instances))
    }

    // Calculate statistics
    results.sort((a, b) => a - b)
    
    const mean = results.reduce((sum, val) => sum + val, 0) / results.length
    const median = results[Math.floor(results.length / 2)]
    const std = Math.sqrt(results.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / results.length)
    
    const p25 = results[Math.floor(results.length * 0.25)]
    const p75 = results[Math.floor(results.length * 0.75)]
    const p95 = results[Math.floor(results.length * 0.95)]
    
    // Calculate confidence based on uncertainty
    const confidence = Math.max(0.5, 1 - uncertainty)

    // Breakdown by categories (simplified)
    breakdown.values = [
      mean * 0.7, // compute
      mean * 0.2, // storage
      mean * 0.1, // network
    ]

    return {
      mean,
      median,
      std,
      min: results[0],
      max: results[results.length - 1],
      p25,
      p75,
      p95,
      unit: unit || 'kg CO2e',
      confidence,
      samples,
      breakdown,
    }
  }

  /**
   * Compare multiple emission scenarios
   */
  async compareScenarios(scenarios: Record<string, any>, samples = 1000): Promise<ComparisonResult> {
    const scenarioNames = Object.keys(scenarios)
    const results: Record<string, EmissionResult> = {}
    
    // Calculate emissions for each scenario
    for (const scenario of scenarioNames) {
      results[scenario] = await this.calculateEmissions(scenarios[scenario], samples)
    }

    // Pairwise comparisons
    const comparisons: Record<string, any> = {}
    for (let i = 0; i < scenarioNames.length; i++) {
      for (let j = i + 1; j < scenarioNames.length; j++) {
        const scenario1 = scenarioNames[i]
        const scenario2 = scenarioNames[j]
        const result1 = results[scenario1]
        const result2 = results[scenario2]
        
        if (!result1 || !result2) continue
        
        const difference = result2.mean - result1.mean
        const percentChange = (difference / result1.mean) * 100
        
        comparisons[`${scenario1}_vs_${scenario2}`] = {
          difference,
          percentChange,
          unit: result1.unit,
          lowerEmission: difference < 0 ? scenario2 : scenario1,
          reduction: Math.abs(percentChange),
        }
      }
    }

    // Generate recommendation
    const sortedScenarios = scenarioNames.sort((a, b) => results[a]!.mean - results[b]!.mean)
    const bestScenario = sortedScenarios[0]!
    const worstScenario = sortedScenarios[sortedScenarios.length - 1]!
    const potentialReduction = ((results[worstScenario]!.mean - results[bestScenario]!.mean) / results[worstScenario]!.mean) * 100

    const recommendation = {
      bestScenario,
      worstScenario,
      potentialReduction,
      confidence: this.calculateOverallConfidence(Object.values(results)),
      summary: this.generateRecommendationSummary(bestScenario, worstScenario, potentialReduction, results),
    }

    return {
      scenarios: scenarioNames,
      results,
      comparisons,
      recommendation,
      range: {
        min: results[sortedScenarios[0]!]!.mean,
        max: results[sortedScenarios[sortedScenarios.length - 1]!]!.mean,
        span: results[sortedScenarios[sortedScenarios.length - 1]!]!.mean - results[sortedScenarios[0]!]!.mean,
        unit: results[bestScenario]!.unit,
      },
    }
  }

  private addUncertainty(value: number, uncertainty: number): number {
    // Normal distribution with specified uncertainty
    const u1 = Math.random()
    const u2 = Math.random()
    
    // Box-Muller transform
    const z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
    
    // Apply uncertainty as percentage of value
    return value * (1 + z0 * uncertainty)
  }

  private calculateOverallConfidence(results: EmissionResult[]): string {
    const avgConfidence = results.reduce((sum, r) => sum + r.confidence, 0) / results.length
    
    if (avgConfidence > 0.9) return 'High'
    if (avgConfidence > 0.7) return 'Medium'
    return 'Low'
  }

  private generateRecommendationSummary(
    best: string,
    worst: string,
    reduction: number,
    results: Record<string, EmissionResult>
  ): string {
    const bestEmission = results[best]!.mean
    const worstEmission = results[worst]!.mean
    const unit = results[best]!.unit

    return `Choose ${best} over ${worst} to reduce emissions by ${reduction.toFixed(1)}% ` +
           `(from ${worstEmission.toFixed(2)} to ${bestEmission.toFixed(2)} ${unit}). ` +
           `This represents a significant environmental benefit with high confidence.`
  }

  /**
   * Calculate emissions for cloud computing instances
   */
  async calculateCloudEmissions(params: {
    vcpus: number
    memory: number // GB
    storage: number // GB
    instances: number
    region: string
    hoursPerMonth?: number
    pue?: number // Power Usage Effectiveness
  }): Promise<EmissionResult> {
    const {
      vcpus,
      memory,
      storage,
      instances,
      hoursPerMonth = 730, // Average hours in a month
      pue = 1.4, // Typical data center PUE
    } = params

    // Rough estimates for power consumption
    const cpuPowerPerCore = 15 // Watts per vCPU
    const memoryPowerPerGB = 0.375 // Watts per GB RAM
    const storagePowerPerGB = 0.065 // Watts per GB SSD
    
    const totalPower = (
      vcpus * cpuPowerPerCore +
      memory * memoryPowerPerGB +
      storage * storagePowerPerGB
    ) * pue // Apply PUE

    const totalEnergyKWh = (totalPower / 1000) * hoursPerMonth * instances

    // Default carbon intensity (will be replaced by real data from ElectricityMap)
    const defaultIntensity = 450 // gCO2e/kWh (US average)
    
    return this.calculateEmissions({
      activity: 'cloud_computing',
      amount: totalEnergyKWh,
      unit: 'kWh',
      emissionFactor: defaultIntensity / 1000, // Convert to kg CO2e/kWh
      uncertainty: 0.15, // 15% uncertainty
      timeMultiplier: 1,
      instances: 1, // Already accounted for in totalEnergyKWh
    })
  }
}
