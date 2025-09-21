/**
 * CarbonLens content script
 */

console.log('CarbonLens content script loaded');

// Listen for messages from popup or background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'extractPageData') {
    try {
      const pageData = extractPageData();
      sendResponse({ success: true, data: pageData });
    } catch (error) {
      sendResponse({ success: false, error: (error as Error).message });
    }
    return true;
  }
  return false;
});

/**
 * Extract structured data from current page
 */
function extractPageData() {
  const url = window.location.href;
  const title = document.title;
  
  // Extract basic page content
  let text = '';
  const contentSelectors = [
    'article',
    'main',
    '[role="main"]',
    '.content',
    '#content',
    '.post-content',
    '.entry-content'
  ];
  
  for (const selector of contentSelectors) {
    const element = document.querySelector(selector);
    if (element) {
      text = element.textContent || (element as HTMLElement).innerText || '';
      break;
    }
  }
  
  // Fallback to body content
  if (!text) {
    const body = document.body.cloneNode(true) as HTMLElement;
    
    // Remove non-content elements
    const removeSelectors = [
      'nav', 'header', 'footer', 'aside',
      '.navigation', '.nav', '.menu',
      '.sidebar', '.footer', '.header',
      'script', 'style', 'noscript'
    ];
    
    removeSelectors.forEach(selector => {
      const elements = body.querySelectorAll(selector);
      elements.forEach(el => el.remove());
    });
    
    text = body.textContent || body.innerText || '';
  }
  
  // Clean up text
  text = text.replace(/\s+/g, ' ').trim();
  
  // Extract structured data
  const data: any = {
    specs: extractSpecs(),
    energy: extractEnergyInfo(),
    location: extractLocationInfo(),
    pricing: extractPricingInfo(),
  };
  
  return {
    url,
    title,
    text: text.substring(0, 10000), // Limit text length
    data,
  };
}

/**
 * Extract technical specifications
 */
function extractSpecs(): Record<string, any> {
  const specs: Record<string, any> = {};
  
  // Look for common spec patterns
  const specPatterns = [
    { key: 'vcpus', pattern: /(\d+)\s*vCPU/i },
    { key: 'memory', pattern: /(\d+)\s*GB?\s*(RAM|Memory)/i },
    { key: 'storage', pattern: /(\d+)\s*GB?\s*(SSD|Storage|Disk)/i },
    { key: 'network', pattern: /(\d+)\s*(Gbps|Mbps)/i },
  ];
  
  const pageText = document.body.textContent || '';
  
  specPatterns.forEach(({ key, pattern }) => {
    const match = pageText.match(pattern);
    if (match) {
      specs[key] = match[1];
    }
  });
  
  return specs;
}

/**
 * Extract energy/power information
 */
function extractEnergyInfo(): Record<string, any> {
  const energy: Record<string, any> = {};
  const pageText = document.body.textContent || '';
  
  // Look for power consumption patterns
  const powerMatch = pageText.match(/(\d+)\s*W(att)?/i);
  if (powerMatch && powerMatch[1]) {
    energy.power = parseInt(powerMatch[1]);
    energy.powerUnit = 'watts';
  }
  
  // Look for efficiency ratings
  if (pageText.includes('Energy Star') || pageText.includes('ENERGY STAR')) {
    energy.efficiency = 'Energy Star certified';
  }
  
  return energy;
}

/**
 * Extract location/region information
 */
function extractLocationInfo(): Record<string, any> {
  const location: Record<string, any> = {};
  const pageText = document.body.textContent || '';
  const url = window.location.href;
  
  // Extract from URL patterns
  const regionPatterns = [
    /us-east-1/i,
    /us-west-2/i,
    /eu-west-1/i,
    /eu-central-1/i,
    /ap-south-1/i,
    /ap-southeast-1/i,
  ];
  
  regionPatterns.forEach(pattern => {
    const match = url.match(pattern);
    if (match) {
      location.region = match[0].toLowerCase();
    }
  });
  
  // Extract from page content
  const locationKeywords = ['Virginia', 'Ireland', 'Singapore', 'Mumbai', 'Frankfurt'];
  locationKeywords.forEach(keyword => {
    if (pageText.includes(keyword)) {
      location.datacenter = keyword;
    }
  });
  
  return location;
}

/**
 * Extract pricing information
 */
function extractPricingInfo(): Record<string, any> {
  const pricing: Record<string, any> = {};
  const pageText = document.body.textContent || '';
  
  // Look for pricing patterns
  const pricePatterns = [
    /\$(\d+\.?\d*)\s*per\s*hour/i,
    /\$(\d+\.?\d*)\s*\/\s*hour/i,
    /\$(\d+\.?\d*)\s*hourly/i,
  ];
  
  pricePatterns.forEach(pattern => {
    const match = pageText.match(pattern);
    if (match && match[1]) {
      pricing.cost = parseFloat(match[1]);
      pricing.currency = 'USD';
      pricing.period = 'hour';
    }
  });
  
  return pricing;
}
