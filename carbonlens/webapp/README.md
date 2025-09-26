# 🌱 CarbonLens Web Application

**Agentic Carbon Emissions Research & Decision Assistant powered by Google Gemini 2.0 Flash**

A beautiful, modern web application that provides intelligent carbon footprint analysis through natural language interactions with AI agents and real-time data from multiple carbon APIs.

![CarbonLens Demo](https://img.shields.io/badge/Status-Ready%20for%20Testing-brightgreen)
![Gemini 2.0](https://img.shields.io/badge/AI-Gemini%202.0%20Flash-blue)
![React](https://img.shields.io/badge/Frontend-React%2018-61dafb)
![TypeScript](https://img.shields.io/badge/Code-TypeScript-3178c6)

## ✨ Features

### 🤖 **Intelligent AI Agent**
- **Gemini 2.0 Flash Integration**: Advanced reasoning and planning
- **Natural Language Interface**: Describe analysis needs in plain English
- **Real-time Agent Trace**: Watch the AI plan, execute tools, and reason through problems
- **Detailed Tool Call Visualization**: See every API call, argument, and result

### 📊 **Real-Time Carbon Analysis**
- **Live Carbon Data**: ElectricityMap for grid intensity, Carbon Interface for emission factors
- **Monte Carlo Simulation**: Uncertainty analysis with thousands of samples
- **Scenario Comparison**: Compare multiple regions, technologies, or strategies
- **Confidence Intervals**: Statistical analysis with uncertainty bounds

### 🛠️ **Comprehensive Tool Suite**
- **CarbonApiTool**: Carbon Interface API integration
- **LCADatabaseTool**: Climatiq life cycle assessment data
- **ElectricityIntensityTool**: Real-time grid carbon intensity
- **NewsSearchTool**: Latest sustainability and carbon news
- **EmissionEstimatorTool**: Advanced Monte Carlo calculations
- **PageExtractorTool**: Extract specs from web pages
- **NotifierTool**: Slack/webhook notifications

### 🎨 **Beautiful Modern UI**
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Real-time Updates**: Streaming agent execution with live progress
- **Interactive Charts**: Visualize emissions data with Recharts
- **Dark/Light Themes**: Tailwind CSS with custom design system
- **Smooth Animations**: Framer Motion for delightful interactions

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- API keys for carbon analysis (see Configuration section)

### Installation

```bash
# Navigate to the webapp directory
cd carbonlens/webapp

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## ⚙️ Configuration

### Required APIs

1. **Google Gemini 2.0 Flash** (Required)
   - Get API key: https://makersuite.google.com/app/apikey
   - Used for: AI agent reasoning and planning

2. **Carbon Interface** (Recommended)
   - Get API key: https://www.carboninterface.com/docs/
   - Used for: Carbon emission factors and calculations

3. **Climatiq** (Optional)
   - Get API key: https://www.climatiq.io/docs
   - Used for: Life cycle assessment database

4. **ElectricityMap** (Optional)
   - Get API key: https://www.electricitymap.org/api
   - Used for: Real-time electricity carbon intensity

5. **News API** (Optional)
   - Get API key: https://newsapi.org/
   - Used for: Sustainability and carbon news

### Setup Instructions

1. **Open Settings Page**: Navigate to `/settings` in the webapp
2. **Add API Keys**: Enter your API keys (stored locally in browser)
3. **Test Connection**: Use the "Test Connection" button to verify setup
4. **Start Analyzing**: Go to `/analysis` and start asking questions!

## 🧪 Example Queries

Try these natural language prompts to see CarbonLens in action:

### **Cloud Computing Analysis**
```
Compare compute carbon intensity us-east-1 vs eu-west-1 for 200 8-vCPU VMs with uncertainty analysis
```

### **Migration Planning**
```
Analyze migration of 500 servers from coal-heavy to renewable regions with cost-benefit analysis
```

### **Infrastructure Optimization**
```
Calculate annual emissions for our cloud infrastructure and find the optimal AWS regions
```

### **Scenario Comparison**
```
Compare carbon footprint of on-premises vs cloud vs edge computing for our workload
```

## 🏗️ Architecture

### Frontend Stack
- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Full type safety and excellent developer experience
- **Tailwind CSS**: Utility-first CSS framework with custom design system
- **Framer Motion**: Smooth animations and transitions
- **Zustand**: Lightweight state management
- **React Router**: Client-side routing
- **Recharts**: Beautiful, responsive charts
- **Lucide React**: Consistent icon system

### Agent System
- **AgentOrchestrator**: Manages the agent execution loop
- **GeminiService**: Handles Gemini 2.0 Flash API integration
- **Tool Adapters**: Modular tools for different carbon data sources
- **EmissionCalculator**: Monte Carlo simulation engine
- **ConversationStorage**: Persistent audit trail

### Real API Integration
- **Direct API Calls**: All API calls made from browser (no proxy needed)
- **Retry Logic**: Exponential backoff for reliability
- **Rate Limiting**: Respect API limits
- **Error Handling**: Graceful failure with user feedback
- **Caching**: Smart caching for performance

## 📱 Pages & Features

### 🏠 **Home Page**
- Feature overview and benefits
- Example query gallery
- Quick start guide
- Beautiful hero section with animations

### 📊 **Analysis Page**
- Natural language prompt input
- Real-time agent execution trace
- Tool call visualization
- Results with charts and insights
- Export functionality

### 📚 **History Page**
- Complete analysis history
- Search and filter capabilities
- Export individual or bulk analyses
- Detailed result viewer

### ⚙️ **Settings Page**
- API key configuration
- Security notices
- Connection testing
- Usage instructions

## 🔒 Security & Privacy

- **Local Storage Only**: API keys stored in browser localStorage
- **No Server Transmission**: Keys never sent to CarbonLens servers
- **Direct API Calls**: All external API calls made directly from browser
- **Clear Data**: Easy to clear all stored data
- **HTTPS Only**: Secure connections for all API calls

## 🧪 Testing

### Development Testing
```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Formatting
npm run format
```

### Example Test Scenarios

1. **Basic Analysis**
   - Enter a simple carbon comparison query
   - Watch agent trace execute step by step
   - Verify results are reasonable and well-formatted

2. **API Integration**
   - Configure real API keys in Settings
   - Run analysis requiring external data
   - Verify real data is fetched and used

3. **Error Handling**
   - Try analysis without API keys
   - Test with invalid API keys
   - Verify graceful error messages

4. **UI Responsiveness**
   - Test on different screen sizes
   - Verify mobile navigation works
   - Check loading states and animations

## 🚀 Deployment

### Static Hosting (Recommended)
```bash
# Build the application
npm run build

# Deploy the dist/ folder to:
# - Vercel
# - Netlify  
# - GitHub Pages
# - AWS S3 + CloudFront
```

### Docker Deployment
```bash
# Build Docker image
docker build -t carbonlens-webapp .

# Run container
docker run -p 3000:3000 carbonlens-webapp
```

## 🛠️ Development

### Project Structure
```
webapp/
├── public/           # Static assets
├── src/
│   ├── components/   # Reusable UI components
│   ├── pages/        # Route components
│   ├── services/     # API services and agent logic
│   ├── store/        # State management
│   ├── types/        # TypeScript type definitions
│   └── utils/        # Utility functions
├── package.json      # Dependencies and scripts
└── README.md        # This file
```

### Key Components
- **AgentTrace**: Real-time agent execution visualization
- **Layout**: Main application layout with navigation
- **HomePage**: Landing page with features and examples
- **AnalysisPage**: Main analysis interface
- **HistoryPage**: Analysis history management
- **SettingsPage**: API configuration

### Adding New Features
1. **New Tool**: Create tool adapter in `src/services/`
2. **New Page**: Add route component in `src/pages/`
3. **New API**: Add service in `src/services/api.ts`
4. **New Component**: Add reusable component in `src/components/`

## 🐛 Troubleshooting

### Common Issues

**"API not configured" error**
- Go to Settings and add required API keys
- Test connection to verify keys work
- Check browser console for detailed errors

**Agent not responding**
- Verify Gemini API key is valid
- Check network connectivity
- Look for rate limit errors in console

**Charts not displaying**
- Ensure data has proper structure
- Check for JavaScript errors
- Verify Recharts is properly installed

**Slow performance**
- Reduce Monte Carlo sample size
- Check for memory leaks in browser dev tools
- Verify API responses are reasonable size

## 📈 Performance

### Optimizations
- **Code Splitting**: Automatic route-based code splitting
- **Tree Shaking**: Unused code elimination
- **Asset Optimization**: Optimized images and fonts
- **Caching**: Smart API response caching
- **Lazy Loading**: Components loaded on demand

### Monitoring
- **Real-time Metrics**: Agent execution time tracking
- **Error Reporting**: Comprehensive error logging
- **Usage Analytics**: Optional usage tracking
- **Performance Profiling**: Built-in performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙋‍♂️ Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join community discussions
- **Email**: Contact team for enterprise support

---

**CarbonLens Web Application - Making carbon analysis intelligent, accessible, and actionable.** 🌱✨