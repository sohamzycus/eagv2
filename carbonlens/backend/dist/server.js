"use strict";
/**
 * CarbonLens Backend Proxy Server
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const helmet_1 = __importDefault(require("helmet"));
const rate_limiter_flexible_1 = require("rate-limiter-flexible");
const node_cache_1 = __importDefault(require("node-cache"));
const axios_1 = __importDefault(require("axios"));
const dotenv_1 = __importDefault(require("dotenv"));
// Load environment variables
dotenv_1.default.config();
const app = (0, express_1.default)();
const PORT = process.env.PORT || 3001;
// Cache with 1 hour TTL
const cache = new node_cache_1.default({ stdTTL: 3600 });
// Rate limiting: 100 requests per minute per IP
const rateLimiter = new rate_limiter_flexible_1.RateLimiterMemory({
    keyPrefix: 'carbonlens',
    points: 100,
    duration: 60,
});
// Middleware
app.use((0, helmet_1.default)());
app.use((0, cors_1.default)({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ['chrome-extension://*'],
    credentials: true,
}));
app.use(express_1.default.json({ limit: '10mb' }));
// Rate limiting middleware
app.use(async (req, res, next) => {
    try {
        await rateLimiter.consume(req.ip || 'unknown');
        next();
    }
    catch {
        res.status(429).json({ error: 'Too many requests' });
    }
});
/**
 * Carbon API Proxy
 */
app.post('/api/carbon/query', async (req, res) => {
    try {
        const { service, region, instanceType, provider } = req.body;
        const cacheKey = `carbon:${service}:${region}:${instanceType}:${provider}`;
        // Check cache first
        const cached = cache.get(cacheKey);
        if (cached) {
            return res.json({ data: cached, cached: true });
        }
        // Check if API keys are configured
        const carbonKey = process.env.CARBON_INTERFACE_API_KEY;
        const climatiqKey = process.env.CLIMATIQ_API_KEY;
        if (!carbonKey && !climatiqKey) {
            return res.json({
                data: {
                    message: 'No API keys configured. Set CARBON_INTERFACE_API_KEY or CLIMATIQ_API_KEY environment variables.',
                    mockData: {
                        value: 0.5,
                        unit: 'kg CO2e/hour',
                        source: 'Backend Mock',
                        region,
                    },
                },
            });
        }
        // Try Carbon Interface API first
        if (carbonKey) {
            try {
                const response = await axios_1.default.post('https://www.carboninterface.com/api/v1/estimates', {
                    type: 'electricity',
                    electricity_unit: 'kwh',
                    electricity_value: 1,
                    country: region.substring(0, 2).toUpperCase(),
                }, {
                    headers: {
                        'Authorization': `Bearer ${carbonKey}`,
                        'Content-Type': 'application/json',
                    },
                    timeout: 10000,
                });
                const data = response.data;
                cache.set(cacheKey, data);
                return res.json({ data, cached: false });
            }
            catch (error) {
                console.error('Carbon Interface API error:', error);
            }
        }
        // Fallback to mock data
        const mockData = {
            value: 0.5,
            unit: 'kg CO2e/hour',
            source: 'Backend Fallback',
            region,
            error: 'API call failed, using fallback data',
        };
        res.json({ data: mockData, cached: false });
    }
    catch (error) {
        console.error('Carbon query error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
/**
 * Electricity Intensity Proxy
 */
app.post('/api/electricity/intensity', async (req, res) => {
    try {
        const { region, forecast, hours } = req.body;
        const cacheKey = `electricity:${region}:${forecast}:${hours}`;
        const cached = cache.get(cacheKey);
        if (cached) {
            return res.json({ data: cached, cached: true });
        }
        const electricityMapKey = process.env.ELECTRICITY_MAP_API_KEY;
        if (!electricityMapKey) {
            return res.json({
                data: {
                    message: 'No ElectricityMap API key configured. Set ELECTRICITY_MAP_API_KEY environment variable.',
                    mockData: generateMockGridData(region, hours),
                },
            });
        }
        // Try ElectricityMap API
        try {
            const response = await axios_1.default.get(`https://api.electricitymap.org/v3/carbon-intensity/latest`, {
                params: { zone: region },
                headers: {
                    'auth-token': electricityMapKey,
                },
                timeout: 10000,
            });
            const data = response.data;
            cache.set(cacheKey, data);
            return res.json({ data, cached: false });
        }
        catch (error) {
            console.error('ElectricityMap API error:', error);
        }
        // Fallback to mock data
        const mockData = generateMockGridData(region, hours);
        res.json({ data: mockData, cached: false });
    }
    catch (error) {
        console.error('Electricity intensity error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
/**
 * News Search Proxy
 */
app.post('/api/news/search', async (req, res) => {
    try {
        const { query, category, days, limit } = req.body;
        const cacheKey = `news:${query}:${category}:${days}:${limit}`;
        const cached = cache.get(cacheKey);
        if (cached) {
            return res.json({ data: cached, cached: true });
        }
        const newsApiKey = process.env.NEWS_API_KEY;
        if (!newsApiKey) {
            return res.json({
                data: {
                    message: 'No NewsAPI key configured. Set NEWS_API_KEY environment variable.',
                    mockData: generateMockNews(query, limit),
                },
            });
        }
        // Try NewsAPI
        try {
            const fromDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
            const response = await axios_1.default.get('https://newsapi.org/v2/everything', {
                params: {
                    q: `${query} AND (carbon OR climate OR emissions)`,
                    from: fromDate,
                    sortBy: 'relevancy',
                    pageSize: limit,
                    apiKey: newsApiKey,
                },
                timeout: 10000,
            });
            const data = response.data;
            cache.set(cacheKey, data);
            return res.json({ data, cached: false });
        }
        catch (error) {
            console.error('NewsAPI error:', error);
        }
        // Fallback to mock data
        const mockData = generateMockNews(query, limit);
        res.json({ data: mockData, cached: false });
    }
    catch (error) {
        console.error('News search error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
/**
 * Notification Proxy
 */
app.post('/api/notify', async (req, res) => {
    try {
        const { message, title, channel, priority, data } = req.body;
        // Log notification (in production, forward to actual services)
        console.log('Notification:', { message, title, channel, priority, timestamp: new Date().toISOString() });
        // Mock successful delivery
        res.json({
            data: {
                delivered: true,
                messageId: `notif_${Date.now()}`,
                channel,
                deliveryTime: Math.floor(Math.random() * 1000) + 500,
            },
        });
    }
    catch (error) {
        console.error('Notification error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});
/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        environment: process.env.NODE_ENV || 'development',
    });
});
/**
 * Generate mock grid data
 */
function generateMockGridData(region, hours) {
    const baseIntensity = region === 'NO' ? 20 : region === 'FR' ? 60 : 400;
    const data = [];
    for (let i = 0; i < hours; i++) {
        const hour = new Date(Date.now() + i * 3600000).getHours();
        const dailyMultiplier = 0.7 + 0.6 * Math.sin((hour - 6) * Math.PI / 12);
        const intensity = Math.round(baseIntensity * dailyMultiplier * (0.9 + 0.2 * Math.random()));
        data.push({
            region,
            intensity,
            timestamp: Date.now() + i * 3600000,
            source: 'Backend Mock',
        });
    }
    return { region, data, summary: { averageIntensity: Math.round(baseIntensity) } };
}
/**
 * Generate mock news data
 */
function generateMockNews(query, limit) {
    const articles = [
        {
            title: 'Major Cloud Providers Announce Carbon Neutral Commitments',
            description: 'Leading cloud companies pledge carbon neutrality by 2030',
            url: 'https://example.com/cloud-carbon-neutral',
            source: 'Tech Climate News',
            publishedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
            title: 'New Study Reveals Regional Carbon Intensity Variations',
            description: 'Research shows 80% difference in emissions across regions',
            url: 'https://example.com/regional-carbon-study',
            source: 'Environmental Journal',
            publishedAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
        },
    ];
    return {
        articles: articles.slice(0, limit),
        totalResults: articles.length,
        query,
    };
}
// Start server
app.listen(PORT, () => {
    console.log(`CarbonLens backend running on port ${PORT}`);
    console.log('Environment variables loaded:');
    console.log('- CARBON_INTERFACE_API_KEY:', !!process.env.CARBON_INTERFACE_API_KEY);
    console.log('- CLIMATIQ_API_KEY:', !!process.env.CLIMATIQ_API_KEY);
    console.log('- ELECTRICITY_MAP_API_KEY:', !!process.env.ELECTRICITY_MAP_API_KEY);
    console.log('- NEWS_API_KEY:', !!process.env.NEWS_API_KEY);
});
exports.default = app;
