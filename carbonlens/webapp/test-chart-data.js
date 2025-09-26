// Test chart data generation
const { generateMockChartData } = require('./src/utils/chartUtils.ts');

// Test gaming console analysis
const gamingAnalysis = "Compare PlayStation 5 vs Xbox Series X vs Gaming PC carbon footprint for Indian gamer, including manufacturing, shipping, and 5-year usage with local electricity rates";

console.log('🎮 Gaming Console Test:');
const gamingData = generateMockChartData(gamingAnalysis);
console.log(JSON.stringify(gamingData, null, 2));

// Test iPhone analysis  
const phoneAnalysis = "iPhone 15 vs iPhone 13 carbon analysis for India Urban region";

console.log('\n📱 iPhone Test:');
const phoneData = generateMockChartData(phoneAnalysis);
console.log(JSON.stringify(phoneData, null, 2));

// Test TV analysis
const tvAnalysis = "Compare 55-inch OLED vs QLED vs LED TV carbon footprints from Sony, Samsung, and LG";

console.log('\n📺 TV Test:');
const tvData = generateMockChartData(tvAnalysis);
console.log(JSON.stringify(tvData, null, 2));
