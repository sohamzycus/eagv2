# CarbonLens 🌱

**Agentic emissions research & decision assistant Chrome extension powered by Google Gemini Flash 2.0**

CarbonLens is a production-ready Chrome extension that helps you analyze, compare, and make informed decisions about carbon emissions across different technologies, regions, and scenarios using AI-powered agents.

## ✨ Features

- **🤖 Agentic Task Composer**: Natural language prompts for complex carbon analysis
- **🔧 Tool Orchestration**: Automated tool selection and execution
- **📊 Monte Carlo Analysis**: Statistical emission estimates with uncertainty quantification
- **🌍 Regional Comparisons**: Real-time electricity grid intensity data
- **📰 News Integration**: Latest carbon/climate news and policy updates
- **🔔 Smart Notifications**: Multi-channel alerts (Slack, Telegram, Email)
- **📈 Visual Trace**: Real-time execution monitoring with expandable details
- **💾 Audit Logs**: Complete conversation history export
- **🔒 Security First**: Mock-first testing with optional real API integration

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Chrome browser
- (Optional) API keys for real-mode operation

### Installation

1. **Clone and install dependencies:**
   ```bash
   git clone <repository-url>
   cd carbonlens
   npm install
   ```

2. **Build the extension:**
   ```bash
   npm run build
   ```

3. **Load in Chrome:**
   - Open `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `dist/` folder

### Development

```bash
# Start development build with watch mode
npm run dev

# Run linting and type checking
npm run lint
npm run type-check

# Run tests
npm run test:unit
npm run test:integration
```

## 🔧 Configuration

### Mock Mode (Default)

CarbonLens runs in **mock mode** by default, using deterministic test data. This is perfect for:
- Development and testing
- Demonstrations
- Learning the interface

### Real Mode

To enable real API calls:

1. **Option A: Use Backend Proxy (Recommended)**
   - Deploy the backend service (see `backend/README.md`)
   - Set `BACKEND_URL` in Options page
   - Configure API keys as environment variables on backend

2. **Option B: Direct API Keys (Development Only)**
   - ⚠️ **Security Warning**: Only for development/testing
   - Go to Options page → Enable "Use Real Mode"
   - Enter API keys directly (stored in browser storage)

### API Keys Required

For real-mode operation, you'll need:

- **Google Gemini**: `GEMINI_API_KEY`
- **Carbon Interface**: `CARBON_INTERFACE_API_KEY` 
- **Climatiq**: `CLIMATIQ_API_KEY`
- **ElectricityMap**: `ELECTRICITY_MAP_API_KEY`
- **NewsAPI**: `NEWS_API_KEY`

## 📖 Usage Examples

### Basic Usage

1. **Click the CarbonLens extension icon**
2. **Enter a natural language prompt:**
   ```
   Compare compute carbon intensity ap-south1 vs eu-west1 for 200 8-vCPU VMs
   ```
3. **Watch the AI agent work:**
   - Plan generation
   - Tool execution
   - Data analysis
   - Final recommendations

### Advanced Prompts

```
Analyze the carbon impact of migrating our 500-server workload from us-east-1 to renewable energy regions, include Monte Carlo uncertainty analysis with 10000 samples

Find recent news about carbon pricing policies and estimate impact on our cloud costs in EU regions

Extract specs from this AWS instance page and calculate annual emissions for 24/7 operation in 3 different regions
```

### Notification Setup

Configure notifications in Options:
- **Slack**: Webhook URL
- **Telegram**: Bot token and chat ID  
- **Email**: SMTP configuration via backend

## 🏗️ Architecture

### Core Components

- **Agent Orchestrator**: Main execution loop (Query → Plan → Tool → Result → Plan...)
- **Tool Registry**: Pluggable tool system with real/mock implementations
- **Gemini Integration**: LLM planning with JSON response validation
- **Conversation Storage**: Append-only audit log in `chrome.storage.local`
- **Streaming UI**: Real-time trace visualization

### Tool Adapters

| Tool | Purpose | Real API | Mock Data |
|------|---------|----------|-----------|
| `CarbonApiTool` | Emission factors | Carbon Interface, Climatiq | Regional factors |
| `ElectricityIntensityTool` | Grid intensity | ElectricityMap, UK API | Hourly patterns |
| `NewsSearchTool` | Climate news | NewsAPI, NewsData | Sample articles |
| `EmissionEstimatorTool` | Monte Carlo calc | Client-side | Statistical simulation |
| `NotifierTool` | Alerts | Webhook forwarding | Mock delivery |
| `PageExtractorTool` | Data extraction | DOM parsing | Structured specs |
| `LCADatabaseTool` | LCA factors | Curated database | Ecoinvent data |

## 🧪 Testing

### Unit Tests

```bash
npm run test:unit
```

Tests cover:
- Agent orchestrator logic
- Tool adapter functionality  
- Monte Carlo calculations
- Mock service behavior

### Integration Tests

```bash
# Mock mode (default)
npm run test:integration

# Real mode (requires backend)
USE_REAL_MODE=true BACKEND_URL=http://localhost:3001 npm run test:integration
```

Integration tests use Playwright to:
- Load extension in Chrome
- Execute sample tasks end-to-end
- Verify complete trace output
- Test UI interactions

### CI Pipeline

GitHub Actions automatically:
- Runs linting and type checking
- Executes unit tests
- Builds extension
- Runs integration tests in mock mode
- Tests backend service separately

## 🔒 Security & Privacy

### Data Handling

- **Local Storage**: Conversation logs stored in `chrome.storage.local`
- **No External Tracking**: No analytics or telemetry
- **API Key Security**: Stored locally (browser) or backend environment variables
- **HTTPS Only**: All external API calls use secure connections

### Security Warnings

⚠️ **Client-side API Keys**: Only use for development. Production deployments should use backend proxy.

⚠️ **Storage Limits**: Chrome storage has quotas. Large conversation histories may be pruned.

⚠️ **Extension Permissions**: Requires `activeTab` and `scripting` for page data extraction.

## 📊 Backend Service

The optional backend service provides:

- **API Proxying**: Secure key management
- **Rate Limiting**: Prevents API quota exhaustion  
- **Caching**: Reduces redundant API calls
- **Webhook Forwarding**: Notification delivery
- **CORS Handling**: Cross-origin request management

See `backend/README.md` for deployment instructions.

## 🎥 Demo Recording

### Recommended Demo Script

1. **Setup**: Show extension in mock mode
2. **Simple Query**: "Compare carbon intensity of us-east-1 vs eu-west1"
3. **Show Trace**: Expand tool calls and results
4. **Complex Query**: "Analyze migration of 1000 VMs with Monte Carlo uncertainty"
5. **Export Logs**: Download audit trail
6. **Real Mode**: Switch to backend integration (if available)

### Recording Tips

- Use 1920x1080 resolution
- Record at 30fps
- Include audio narration
- Show both popup and overlay interfaces
- Demonstrate error handling

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`npm run ci`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

### Development Guidelines

- **TypeScript Strict Mode**: All code must pass `tsc --noEmit`
- **ESLint**: Follow configured rules
- **Testing**: Maintain >80% coverage
- **Documentation**: Update README for new features
- **Mock First**: All new tools need mock implementations

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini**: AI planning and reasoning
- **Carbon Interface**: Emission factor data
- **ElectricityMap**: Real-time grid intensity
- **Ecoinvent**: LCA database
- **Chrome Extensions**: Platform and APIs

## 📞 Support

- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions

---

**Built with ❤️ by Soham for a sustainable future** 🌍
