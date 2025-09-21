# CarbonLens Backend Service

Backend proxy service for the CarbonLens Chrome extension, providing secure API key management, caching, and rate limiting.

## Features

- **API Proxying**: Secure access to Carbon Interface, Climatiq, ElectricityMap, NewsAPI
- **Rate Limiting**: 100 requests per minute per IP
- **Caching**: 1-hour TTL for API responses
- **Security**: Helmet.js, CORS, input validation
- **Fallback**: Mock data when APIs are unavailable
- **Health Monitoring**: `/health` endpoint

## Quick Start

### Environment Setup

Create a `.env` file:

```bash
# Server Configuration
PORT=3001
NODE_ENV=production
ALLOWED_ORIGINS=chrome-extension://your-extension-id

# API Keys (optional - service works without them)
CARBON_INTERFACE_API_KEY=your_carbon_interface_key
CLIMATIQ_API_KEY=your_climatiq_key
ELECTRICITY_MAP_API_KEY=your_electricity_map_key
NEWS_API_KEY=your_news_api_key

# Notification Webhooks (optional)
SLACK_WEBHOOK_URL=your_slack_webhook
TELEGRAM_BOT_TOKEN=your_telegram_token
```

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Docker Deployment

```bash
# Build image
docker build -t carbonlens-backend .

# Run container
docker run -p 3001:3001 --env-file .env carbonlens-backend
```

## API Endpoints

### Carbon Emissions

```http
POST /api/carbon/query
Content-Type: application/json

{
  "service": "compute",
  "region": "us-east-1",
  "instanceType": "8-vCPU",
  "provider": "aws"
}
```

### Electricity Intensity

```http
POST /api/electricity/intensity
Content-Type: application/json

{
  "region": "UK",
  "forecast": false,
  "hours": 24
}
```

### News Search

```http
POST /api/news/search
Content-Type: application/json

{
  "query": "carbon pricing",
  "category": "policy",
  "days": 7,
  "limit": 10
}
```

### Notifications

```http
POST /api/notify
Content-Type: application/json

{
  "message": "Task completed",
  "title": "CarbonLens Alert",
  "channel": "slack",
  "priority": "normal"
}
```

## Security Considerations

- **API Keys**: Never expose in client-side code
- **Rate Limiting**: Prevents abuse and quota exhaustion
- **CORS**: Restricts access to authorized origins
- **Input Validation**: Sanitizes all request data
- **Caching**: Reduces API calls and improves performance

## Monitoring

Health check endpoint:

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "version": "1.0.0",
  "environment": "production"
}
```

## API Key Setup

### Carbon Interface
1. Sign up at https://carboninterface.com
2. Get free API key (1000 requests/month)
3. Set `CARBON_INTERFACE_API_KEY`

### Climatiq
1. Register at https://climatiq.io
2. Free tier: 1000 requests/month
3. Set `CLIMATIQ_API_KEY`

### ElectricityMap
1. Visit https://electricitymap.org/api
2. Academic/non-commercial use available
3. Set `ELECTRICITY_MAP_API_KEY`

### NewsAPI
1. Get key from https://newsapi.org
2. Free tier: 1000 requests/day
3. Set `NEWS_API_KEY`

## Deployment Options

### Heroku
```bash
heroku create carbonlens-backend
heroku config:set CARBON_INTERFACE_API_KEY=your_key
git push heroku main
```

### Railway
```bash
railway login
railway new
railway add
railway deploy
```

### DigitalOcean App Platform
1. Connect GitHub repository
2. Set environment variables in dashboard
3. Deploy automatically on push

### AWS Lambda
Use `serverless` framework with Express adapter for serverless deployment.

## Troubleshooting

### Common Issues

**CORS Errors**
- Add your extension ID to `ALLOWED_ORIGINS`
- Check Chrome extension manifest permissions

**Rate Limiting**
- Increase limits in `server.ts` if needed
- Implement user-specific rate limiting

**API Timeouts**
- Check network connectivity
- Verify API keys are valid
- Monitor API status pages

**Cache Issues**
- Clear cache: restart server
- Adjust TTL in `NodeCache` configuration

### Logs

Enable debug logging:
```bash
DEBUG=carbonlens:* npm start
```

### Performance

Monitor key metrics:
- Response times
- Cache hit rates
- API error rates
- Memory usage

## Contributing

1. Fork repository
2. Create feature branch
3. Add tests for new endpoints
4. Update documentation
5. Submit pull request

## License

MIT License - see main project LICENSE file.
