# 🤖 Browser Agent - Automated Form Filler

An intelligent browser automation agent that uses **local LLMs** (via Ollama) to automatically fill web forms, specifically designed for Google Forms.

## 📋 Overview

This project implements a sophisticated browser agent using Python best practices and design patterns. The agent can:

- 🌐 Navigate to web forms automatically
- 🔍 Detect and extract form fields (text, radio, checkbox, dropdown)
- 🧠 Use local LLMs (llama3.2, phi4, mistral, etc.) to intelligently determine form values
- 📝 Fill forms with contextually appropriate responses
- 📤 Submit forms automatically
- 📸 Capture screenshots at each step

## 🏗️ Architecture & Design Patterns

This project demonstrates **professional Python OOP practices** using several design patterns:

### Design Patterns Used

| Pattern | Implementation | Purpose |
|---------|---------------|---------|
| **Abstract Factory** | `LLMProviderFactory` | Creates LLM provider instances (Ollama, etc.) |
| **Strategy** | `FormFillerStrategy`, `LLMGuidedStrategy`, `RuleBasedStrategy`, `HybridStrategy` | Interchangeable algorithms for form filling |
| **Observer** | `EventDispatcher`, `ConsoleLogger`, `FileLogger` | Event-driven logging and monitoring |
| **Template Method** | `BrowserAction` | Defines skeleton for browser actions with customizable steps |
| **Singleton** | `EventDispatcher` | Central event hub instance |
| **Factory Method** | `LLMProviderFactory.create_provider()` | Creates concrete LLM providers |

### Project Structure

```
browser_agent/
├── core/                    # Core abstractions and interfaces
│   ├── __init__.py
│   ├── interfaces.py        # Abstract base classes
│   └── events.py            # Event system (Observer pattern)
│
├── llm/                     # LLM integration
│   ├── __init__.py
│   ├── providers.py         # Ollama provider (Abstract Factory)
│   └── prompt_manager.py    # Prompt template management
│
├── browser/                 # Browser automation
│   ├── __init__.py
│   ├── controller.py        # High-level browser control
│   └── actions.py           # Browser actions (Template Method)
│
├── strategies/              # Form filling strategies
│   ├── __init__.py
│   ├── llm_strategy.py      # LLM-guided filling
│   ├── rule_strategy.py     # Rule-based filling
│   └── hybrid_strategy.py   # Combined approach
│
├── form_filler/             # Form-specific handlers
│   ├── __init__.py
│   └── google_forms.py      # Google Forms handler
│
├── utils/                   # Utilities
│   ├── __init__.py
│   ├── observers.py         # Logging observers
│   └── config.py            # Configuration management
│
├── prompts/                 # LLM prompt templates
│   ├── system.txt
│   ├── form_analysis.txt
│   └── field_value.txt
│
├── config/                  # Configuration files
│   └── config.yaml
│
├── agent.py                 # Main agent orchestrator
├── run.py                   # Quick-start script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+**
2. **Ollama** - For local LLM inference

### Installation

```bash
# Clone or navigate to the project
cd browser_agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Setup Ollama

```bash
# Install Ollama (if not already installed)
# macOS
brew install ollama

# Start Ollama service
ollama serve

# Pull a model (choose one)
ollama pull llama3.2    # Recommended
ollama pull phi4        # Alternative
ollama pull mistral     # Alternative
```

### Running the Agent

#### Quick Run (for Assignment)

```bash
python run.py \
    --github-url "https://github.com/yourusername/browser-agent" \
    --youtube-url "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
```

#### Advanced Usage

```bash
# Using the main agent with all options
python agent.py "https://forms.gle/6Nc6QaaJyDvePxLv7" \
    --model llama3.2 \
    --strategy hybrid \
    --name "Your Name" \
    --email "your@email.com" \
    --github-url "https://github.com/..." \
    --youtube-url "https://youtube.com/..."
```

#### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--model`, `-m` | Ollama model to use | `llama3.2` |
| `--strategy`, `-s` | Filling strategy (`llm`, `rule`, `hybrid`) | `hybrid` |
| `--headless` | Run browser in background | `false` |
| `--no-submit` | Fill form but don't submit | `false` |
| `--name` | Name for form fields | `Soham Niyogi` |
| `--email` | Email for form fields | `sohamniyogi9@gmail.com` |
| `--github-url` | GitHub repository URL | - |
| `--youtube-url` | YouTube demo video URL | - |
| `--config`, `-c` | Path to YAML config file | - |

## 📊 Form Filling Strategies

### 1. LLM-Guided Strategy (`llm`)
Uses the local LLM to analyze each field and generate appropriate responses.
- Best for: Complex forms with context-dependent answers
- Slower but more intelligent

### 2. Rule-Based Strategy (`rule`)
Uses pattern matching and predefined rules.
- Best for: Simple forms with predictable fields
- Fast but less flexible

### 3. Hybrid Strategy (`hybrid`) - **Recommended**
Combines both approaches:
- Uses rules for known patterns (name, email, URLs)
- Falls back to LLM for complex fields
- Best balance of speed and intelligence

## 🔧 Configuration

### YAML Configuration

Create/edit `config/config.yaml`:

```yaml
llm:
  provider: ollama
  model: llama3.2
  temperature: 0.7

browser:
  headless: false
  slow_mo: 100

agent:
  strategy: hybrid
  user_name: "Your Name"
  user_email: "your@email.com"
```

### Environment Variables

```bash
export LLM_MODEL=llama3.2
export AGENT_STRATEGY=hybrid
export USER_NAME="Your Name"
export USER_EMAIL="your@email.com"
```

## 📸 Screenshots & Logs

The agent automatically saves:
- **Screenshots**: `screenshots/` directory
  - `01_initial.png` - Initial form view
  - `02_questions_extracted.png` - After question detection
  - `03_form_filled.png` - After filling
  - `04_submitted.png` - After submission
- **Logs**: `agent_log.json` - Complete event history in JSON format

## 🧪 Supported Models

Tested with the following Ollama models:

| Model | Size | Performance | Notes |
|-------|------|-------------|-------|
| `llama3.2` | 3B | ⭐⭐⭐⭐ | Recommended, good balance |
| `llama3.2:1b` | 1B | ⭐⭐⭐ | Faster, less accurate |
| `phi4` | 14B | ⭐⭐⭐⭐⭐ | Best quality, slower |
| `mistral` | 7B | ⭐⭐⭐⭐ | Good alternative |
| `qwen2.5` | 7B | ⭐⭐⭐⭐ | Good for multilingual |

## 📝 Example Output

```
============================================================
🤖 Browser Agent - Automated Form Filler
============================================================
Model: llama3.2
Strategy: hybrid
URL: https://forms.gle/6Nc6QaaJyDvePxLv7
============================================================

[10:30:15] BROWSER_LAUNCHED: Browser launched successfully
[10:30:17] NAVIGATION_COMPLETE: Navigation complete
[10:30:18] FORM_DETECTED: Google Form detected

📋 Found 3 questions:

  • GitHub Code URL (required)
  • YouTube Video URL (required)
  • Additional Comments

[10:30:20] FIELD_FILLED: Filled: GitHub Code URL
[10:30:22] FIELD_FILLED: Filled: YouTube Video URL
[10:30:24] FIELD_FILLED: Filled: Additional Comments

✅ Filled 3/3 questions

📤 Submitting form...
[10:30:26] FORM_SUBMITTED: Form submitted successfully

🎉 SUCCESS! Form has been filled and submitted!
```

## 🏆 Design Highlights

### SOLID Principles

1. **Single Responsibility**: Each class has one clear purpose
2. **Open/Closed**: Strategies can be added without modifying existing code
3. **Liskov Substitution**: All strategies implement the same interface
4. **Interface Segregation**: Small, focused interfaces
5. **Dependency Inversion**: High-level modules depend on abstractions

### Clean Code Practices

- Type hints throughout
- Comprehensive docstrings
- Meaningful variable names
- DRY (Don't Repeat Yourself)
- Separation of concerns

## 🐛 Troubleshooting

### Ollama Not Available

```bash
# Make sure Ollama is running
ollama serve

# Check if model is installed
ollama list

# Pull the model if missing
ollama pull llama3.2
```

### Browser Issues

```bash
# Reinstall Playwright browsers
playwright install chromium --force
```

### Form Detection Issues

The agent is optimized for Google Forms. For other form types:
1. Check the `form_filler/google_forms.py` for selector patterns
2. Adjust selectors if the form structure is different

## 📄 License

MIT License - See LICENSE file for details.

## 👤 Author

**Soham Niyogi**
- Email: sohamniyogi9@gmail.com

---

*This project was created as part of the EAG v2 Browser Agent assignment.*



