interface ChartData {
  name: string;
  value: number;
  breakdown?: {
    manufacturing?: number;
    shipping?: number;
    usage?: number;
    [key: string]: number | undefined;
  };
}

export function parseAnalysisForCharts(analysisText: string): ChartData[] | null {
  try {
    // Try to extract structured data from the analysis text
    const data: ChartData[] = [];
    
    // Look for emission values in the text
    const emissionPatterns = [
      // Pattern: "Product Name: X kg CO2e"
      /([A-Za-z0-9\s]+):\s*(\d+(?:\.\d+)?)\s*kg\s*CO2e/gi,
      // Pattern: "Product Name has X kg CO2e"
      /([A-Za-z0-9\s]+)\s+has\s+(\d+(?:\.\d+)?)\s*kg\s*CO2e/gi,
      // Pattern: "Product Name - X kg CO2e"
      /([A-Za-z0-9\s]+)\s*-\s*(\d+(?:\.\d+)?)\s*kg\s*CO2e/gi,
      // Pattern: "Product Name (X kg CO2e)"
      /([A-Za-z0-9\s]+)\s*\(\s*(\d+(?:\.\d+)?)\s*kg\s*CO2e\s*\)/gi
    ];

    for (const pattern of emissionPatterns) {
      let match;
      while ((match = pattern.exec(analysisText)) !== null) {
        const name = match[1].trim();
        const value = parseFloat(match[2]);
        
        if (name && !isNaN(value) && value > 0) {
          // Avoid duplicates
          if (!data.find(item => item.name.toLowerCase() === name.toLowerCase())) {
            data.push({ name, value });
          }
        }
      }
    }

    // Look for breakdown data
    data.forEach(item => {
      const namePattern = new RegExp(item.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i');
      const section = analysisText.split(namePattern)[1]?.split(/(?=[A-Z][a-z]+:|\n\n)/)[0] || '';
      
      const breakdown: any = {};
      
      // Manufacturing emissions
      const mfgMatch = section.match(/manufacturing[:\s]*(\d+(?:\.\d+)?)/i);
      if (mfgMatch) breakdown.manufacturing = parseFloat(mfgMatch[1]);
      
      // Shipping emissions
      const shipMatch = section.match(/shipping[:\s]*(\d+(?:\.\d+)?)/i);
      if (shipMatch) breakdown.shipping = parseFloat(shipMatch[1]);
      
      // Usage emissions
      const usageMatch = section.match(/usage[:\s]*(\d+(?:\.\d+)?)/i);
      if (usageMatch) breakdown.usage = parseFloat(usageMatch[1]);
      
      if (Object.keys(breakdown).length > 0) {
        item.breakdown = breakdown;
      }
    });

    return data.length > 0 ? data : null;
  } catch (error) {
    console.error('Error parsing analysis for charts:', error);
    return null;
  }
}

export function extractComparisonData(toolResults: any[]): ChartData[] | null {
  try {
    const data: ChartData[] = [];
    
    // Look for EmissionEstimatorTool results
    const emissionResults = toolResults.find(result => 
      result.tool === 'EmissionEstimatorTool' && result.result?.comparison
    );
    
    if (emissionResults?.result?.comparison) {
      const comparison = emissionResults.result.comparison;
      
      Object.entries(comparison).forEach(([name, itemData]: [string, any]) => {
        if (itemData && typeof itemData === 'object' && itemData.total_emissions) {
          const chartItem: ChartData = {
            name,
            value: itemData.total_emissions
          };
          
          // Add breakdown if available
          if (itemData.manufacturing_emissions || itemData.shipping_emissions || itemData.usage_emissions_per_year) {
            chartItem.breakdown = {
              manufacturing: itemData.manufacturing_emissions,
              shipping: itemData.shipping_emissions,
              usage: itemData.usage_emissions_per_year * (itemData.lifespan || 1)
            };
          }
          
          data.push(chartItem);
        }
      });
    }
    
    return data.length > 0 ? data : null;
  } catch (error) {
    console.error('Error extracting comparison data:', error);
    return null;
  }
}

export function generateMockChartData(analysisText: string): ChartData[] {
  // Generate realistic mock data based on the analysis text
  const products = [];
  
  // Common product patterns
  if (analysisText.toLowerCase().includes('iphone')) {
    products.push(
      { name: 'iPhone 15', value: 70.2, breakdown: { manufacturing: 55, shipping: 3.2, usage: 12 } },
      { name: 'iPhone 13', value: 68.8, breakdown: { manufacturing: 52, shipping: 3.8, usage: 13 } }
    );
  }
  
  if (analysisText.toLowerCase().includes('gaming') || analysisText.toLowerCase().includes('playstation') || analysisText.toLowerCase().includes('xbox')) {
    products.push(
      { name: 'PlayStation 5', value: 318.4, breakdown: { manufacturing: 150, shipping: 10, usage: 158.4 } },
      { name: 'Xbox Series X', value: 315.2, breakdown: { manufacturing: 148, shipping: 12, usage: 155.2 } },
      { name: 'Gaming PC', value: 736.8, breakdown: { manufacturing: 400, shipping: 20, usage: 316.8 } }
    );
  }
  
  if (analysisText.toLowerCase().includes('tv') || analysisText.toLowerCase().includes('television')) {
    products.push(
      { name: 'OLED TV', value: 425.6, breakdown: { manufacturing: 280, shipping: 25, usage: 120.6 } },
      { name: 'QLED TV', value: 398.2, breakdown: { manufacturing: 260, shipping: 22, usage: 116.2 } },
      { name: 'LED TV', value: 312.4, breakdown: { manufacturing: 200, shipping: 18, usage: 94.4 } }
    );
  }
  
  if (analysisText.toLowerCase().includes('laptop') || analysisText.toLowerCase().includes('computer')) {
    products.push(
      { name: 'MacBook Pro', value: 245.8, breakdown: { manufacturing: 180, shipping: 8, usage: 57.8 } },
      { name: 'Dell XPS', value: 238.4, breakdown: { manufacturing: 175, shipping: 9, usage: 54.4 } },
      { name: 'ThinkPad', value: 228.6, breakdown: { manufacturing: 165, shipping: 7, usage: 56.6 } }
    );
  }
  
  // If no specific products found, generate generic comparison
  if (products.length === 0) {
    products.push(
      { name: 'Option A', value: 150.5, breakdown: { manufacturing: 100, shipping: 10, usage: 40.5 } },
      { name: 'Option B', value: 180.2, breakdown: { manufacturing: 120, shipping: 12, usage: 48.2 } },
      { name: 'Option C', value: 135.8, breakdown: { manufacturing: 90, shipping: 8, usage: 37.8 } }
    );
  }
  
  return products;
}
