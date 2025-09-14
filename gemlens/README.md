# 🔍 GemLens - AI-Powered Web Summarization

[![CI](https://github.com/your-username/gemlens/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/gemlens/actions/workflows/ci.yml)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue.svg)](https://www.typescriptlang.org/)
[![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-green.svg)](https://developer.chrome.com/docs/extensions/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Transform your web browsing experience with AI-powered summarization and intelligent chat using Google Gemini.

## ✨ Features

- **🚀 Instant Summarization**: Get AI-generated summaries of any webpage in seconds
- **🎥 Video Summarization**: Extract and summarize YouTube video content and captions
- **💬 Interactive Chat**: Ask questions about any webpage with contextual AI responses
- **⚡ Streaming Responses**: Real-time AI responses with smooth streaming interface
- **🎨 Beautiful UI**: Modern, polished interface with smooth animations
- **🔒 Privacy-First**: Your API key stays local, direct communication with Google's API
- **📱 Responsive Design**: Works seamlessly across different screen sizes
- **🎯 Smart Caching**: Intelligent caching system to save API calls and improve performance

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Chrome browser (for development and testing)
- Google Gemini API key ([Get one free here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/gemlens.git
   cd gemlens
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Build the extension**
   ```bash
   npm run build
   ```

4. **Load in Chrome**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (top right toggle)
   - Click "Load unpacked" and select the `dist/` folder
   - The GemLens extension should now appear in your extensions

5. **Configure API Key**
   - Click the GemLens icon in your browser toolbar
   - Click "Settings" to open the options page
   - Enter your Google Gemini API key
   - Click "Save API Key" and test the connection

## 🛠️ Development

### Development Mode

Start the development server with hot reloading:

```bash
npm run dev
```

This will watch for file changes and automatically rebuild the extension.

### Available Scripts

- `npm run dev` - Start development server with watch mode
- `npm run build` - Build production version
- `npm run lint` - Run ESLint with auto-fix
- `npm run format` - Format code with Prettier
- `npm run test:unit` - Run Jest unit tests
- `npm run test:integration` - Run Playwright integration tests
- `npm run ci` - Run full CI pipeline (lint + test + build)

### Project Structure

```
gemlens/
├── src/
│   ├── background/          # Service worker and background services
│   │   ├── service_worker.ts
│   │   ├── di.ts           # Dependency injection container
│   │   └── services/       # Core business logic
│   ├── content/            # Content scripts and overlay
│   │   ├── contentScript.ts
│   │   └── overlay/        # In-page chat interface
│   ├── popup/              # Extension popup UI
│   ├── options/            # Settings/options page
│   └── shared/             # Shared utilities and types
├── tests/
│   ├── unit/               # Jest unit tests
│   ├── integration/        # Playwright E2E tests
│   ├── mocks/              # Test mocks and fixtures
│   └── fixtures/           # Test HTML pages
└── assets/                 # Icons and static assets
```

## 🔧 Configuration

### API Key Setup

1. **Get your API key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Open extension options**: Right-click the extension icon → "Options"
3. **Enter your key**: Paste your API key and click "Save"
4. **Test connection**: Click "Test Connection" to verify it works

### Security Considerations

⚠️ **Important Security Notes:**

- **Client-side API keys are visible to websites you visit**
- **For production use, consider implementing a server-side proxy**
- **Monitor your API usage in Google Cloud Console**
- **Rotate your API keys regularly**

#### Recommended Production Setup

For enhanced security in production environments:

1. **Server-side Proxy**: Implement a backend service that handles Gemini API calls
2. **Token Exchange**: Use short-lived tokens instead of long-lived API keys
3. **Rate Limiting**: Implement proper rate limiting and usage monitoring
4. **Environment Separation**: Use different API keys for development and production

## 🧪 Testing

### Unit Tests

Run Jest unit tests for individual components:

```bash
npm run test:unit
```

Tests cover:
- ✅ GeminiService API integration
- ✅ CacheService storage logic
- ✅ Content extraction utilities
- ✅ Mock implementations

### Integration Tests

Run Playwright end-to-end tests:

```bash
npm run test:integration
```

By default, tests use **GeminiMock** for fast, reliable testing.

#### Testing with Real API

To test against the actual Gemini API:

```bash
USE_REAL_API=true GOOGLE_API_KEY=your_key_here npm run test:integration
```

⚠️ **Note**: Real API tests consume your quota and may be slower.

### Test Coverage

- **Unit Tests**: Service layer, utilities, and business logic
- **Integration Tests**: End-to-end user workflows
- **Mock Testing**: Default mode for CI/CD pipelines
- **Real API Testing**: Optional for production validation

## 📖 Usage Guide

### Summarizing Web Pages

1. **Navigate to any webpage**
2. **Click the GemLens extension icon**
3. **Click "Summarize Page"**
4. **View the AI-generated summary**
5. **Copy or share the summary**

### Summarizing Videos

1. **Go to a YouTube video**
2. **Click the GemLens extension icon**
3. **Click "Summarize Video"**
4. **Get a summary of video content and captions**

### Interactive Chat

1. **On any webpage, click "Ask Gemini"**
2. **An overlay chat window will appear**
3. **Ask questions about the page content**
4. **Get contextual AI responses in real-time**

### Settings & Preferences

Access the options page to configure:

- ✅ **API Key Management**: Add, test, or remove your Gemini API key
- ✅ **Summary Length**: Choose between short, medium, or long summaries
- ✅ **Language Preferences**: Set your preferred response language
- ✅ **Auto-summarization**: Enable automatic summarization on page load
- ✅ **Usage Statistics**: View your summarization and chat usage

## 🏗️ Architecture

### SOLID Principles & Dependency Injection

GemLens follows SOLID principles with a clean dependency injection pattern:

```typescript
// Dependency injection container
export interface Container {
  gemini: IGeminiService;
  storage: StorageService;
  cache: CacheService;
}

// Easy testing with mocks
const container = buildContainer(true); // Uses GeminiMock
const container = buildContainer(false, apiKey); // Uses real GeminiService
```

### Service Layer

- **IGeminiService**: Interface for AI summarization (real + mock implementations)
- **StorageService**: Chrome storage API wrapper for settings persistence
- **CacheService**: Intelligent caching with TTL for API response optimization
- **PageExtractor**: Content extraction with YouTube caption support

### Communication Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Popup     │───▶│ Content      │───▶│ Service Worker  │
│   UI        │    │ Script       │    │ (Background)    │
└─────────────┘    └──────────────┘    └─────────────────┘
                           │                      │
                           ▼                      ▼
                   ┌──────────────┐    ┌─────────────────┐
                   │   Overlay    │    │ Gemini API      │
                   │   Chat       │    │ Integration     │
                   └──────────────┘    └─────────────────┘
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with tests
4. **Run the test suite**: `npm run ci`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to your branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Code Standards

- ✅ **TypeScript strict mode** - All code must pass strict type checking
- ✅ **ESLint + Prettier** - Automated code formatting and linting
- ✅ **Test Coverage** - New features require corresponding tests
- ✅ **Documentation** - Update README and inline docs for new features

## 📊 Performance & Optimization

### Caching Strategy

- **Smart TTL**: 24-hour default cache with configurable expiration
- **URL-based Keys**: Efficient cache invalidation per webpage
- **Storage Optimization**: Automatic cleanup of expired entries

### API Efficiency

- **Streaming Responses**: Real-time UI updates during AI generation
- **Exponential Backoff**: Robust retry logic for transient failures
- **Token Optimization**: Configurable response length to manage costs

### Bundle Size

- **Tree Shaking**: Vite eliminates unused code
- **Code Splitting**: Separate bundles for different extension contexts
- **Asset Optimization**: Compressed icons and optimized CSS

## 🐛 Troubleshooting

### Common Issues

**❌ "API key required" error**
- Solution: Add your Gemini API key in the extension options page

**❌ "Extension context invalidated" error**
- Solution: Reload the extension in `chrome://extensions/`

**❌ "Cannot access chrome:// URLs" error**
- Solution: GemLens doesn't work on browser internal pages (this is normal)

**❌ Summarization fails on some websites**
- Solution: Some sites block content extraction; try refreshing the page

### Debug Mode

Enable debug logging by setting `localStorage.debug = 'gemlens:*'` in the browser console.

### Getting Help

- 📖 **Documentation**: Check this README and inline code comments
- 🐛 **Bug Reports**: [Open an issue](https://github.com/your-username/gemlens/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/gemlens/discussions)
- 📧 **Contact**: [your-email@example.com](mailto:your-email@example.com)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini**: For providing the powerful AI capabilities
- **Chrome Extensions Team**: For the excellent extension platform
- **Open Source Community**: For the amazing tools and libraries used

## 🚀 Roadmap

### Upcoming Features

- 🔄 **Multi-language Support**: Full i18n for global users
- 📱 **Mobile Extension**: Support for Chrome mobile
- 🎨 **Custom Themes**: Dark mode and customizable UI themes
- 📊 **Analytics Dashboard**: Detailed usage insights and statistics
- 🔗 **Integration APIs**: Connect with note-taking and productivity apps
- 🤖 **Advanced AI Features**: Document comparison, trend analysis

### Version History

- **v1.0.0** - Initial release with core summarization and chat features
- **v0.9.0** - Beta release with YouTube video support
- **v0.8.0** - Alpha release with basic webpage summarization

---

<div align="center">

**Made with ❤️ for productivity enthusiasts**

[⭐ Star this repo](https://github.com/your-username/gemlens) • [🐛 Report Bug](https://github.com/your-username/gemlens/issues) • [💡 Request Feature](https://github.com/your-username/gemlens/issues)

</div>
