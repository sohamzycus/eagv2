console.log("CarbonLens content script loaded");
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "extractPageData") {
    try {
      const pageData = extractPageData();
      sendResponse({ success: true, data: pageData });
    } catch (error) {
      sendResponse({ success: false, error: error.message });
    }
    return true;
  }
  return false;
});
function extractPageData() {
  const url = window.location.href;
  const title = document.title;
  let text = "";
  const contentSelectors = [
    "article",
    "main",
    '[role="main"]',
    ".content",
    "#content",
    ".post-content",
    ".entry-content"
  ];
  for (const selector of contentSelectors) {
    const element = document.querySelector(selector);
    if (element) {
      text = element.textContent || element.innerText || "";
      break;
    }
  }
  if (!text) {
    const body = document.body.cloneNode(true);
    const removeSelectors = [
      "nav",
      "header",
      "footer",
      "aside",
      ".navigation",
      ".nav",
      ".menu",
      ".sidebar",
      ".footer",
      ".header",
      "script",
      "style",
      "noscript"
    ];
    removeSelectors.forEach((selector) => {
      const elements = body.querySelectorAll(selector);
      elements.forEach((el) => el.remove());
    });
    text = body.textContent || body.innerText || "";
  }
  text = text.replace(/\s+/g, " ").trim();
  const data = {
    specs: extractSpecs(),
    energy: extractEnergyInfo(),
    location: extractLocationInfo(),
    pricing: extractPricingInfo()
  };
  return {
    url,
    title,
    text: text.substring(0, 1e4),
    // Limit text length
    data
  };
}
function extractSpecs() {
  const specs = {};
  const specPatterns = [
    { key: "vcpus", pattern: /(\d+)\s*vCPU/i },
    { key: "memory", pattern: /(\d+)\s*GB?\s*(RAM|Memory)/i },
    { key: "storage", pattern: /(\d+)\s*GB?\s*(SSD|Storage|Disk)/i },
    { key: "network", pattern: /(\d+)\s*(Gbps|Mbps)/i }
  ];
  const pageText = document.body.textContent || "";
  specPatterns.forEach(({ key, pattern }) => {
    const match = pageText.match(pattern);
    if (match) {
      specs[key] = match[1];
    }
  });
  return specs;
}
function extractEnergyInfo() {
  const energy = {};
  const pageText = document.body.textContent || "";
  const powerMatch = pageText.match(/(\d+)\s*W(att)?/i);
  if (powerMatch && powerMatch[1]) {
    energy.power = parseInt(powerMatch[1]);
    energy.powerUnit = "watts";
  }
  if (pageText.includes("Energy Star") || pageText.includes("ENERGY STAR")) {
    energy.efficiency = "Energy Star certified";
  }
  return energy;
}
function extractLocationInfo() {
  const location = {};
  const pageText = document.body.textContent || "";
  const url = window.location.href;
  const regionPatterns = [
    /us-east-1/i,
    /us-west-2/i,
    /eu-west-1/i,
    /eu-central-1/i,
    /ap-south-1/i,
    /ap-southeast-1/i
  ];
  regionPatterns.forEach((pattern) => {
    const match = url.match(pattern);
    if (match) {
      location.region = match[0].toLowerCase();
    }
  });
  const locationKeywords = ["Virginia", "Ireland", "Singapore", "Mumbai", "Frankfurt"];
  locationKeywords.forEach((keyword) => {
    if (pageText.includes(keyword)) {
      location.datacenter = keyword;
    }
  });
  return location;
}
function extractPricingInfo() {
  const pricing = {};
  const pageText = document.body.textContent || "";
  const pricePatterns = [
    /\$(\d+\.?\d*)\s*per\s*hour/i,
    /\$(\d+\.?\d*)\s*\/\s*hour/i,
    /\$(\d+\.?\d*)\s*hourly/i
  ];
  pricePatterns.forEach((pattern) => {
    const match = pageText.match(pattern);
    if (match && match[1]) {
      pricing.cost = parseFloat(match[1]);
      pricing.currency = "USD";
      pricing.period = "hour";
    }
  });
  return pricing;
}
