# 🏗️ BirdSense Architecture

**Developed by Soham**

This document describes the novel hybrid architecture of BirdSense - an AI-powered bird identification system.

---

## Overview

BirdSense combines **specialized ML models** (BirdNET) with **large language models** (LLaVA/GPT-4o) to achieve superior accuracy compared to using either approach alone.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         BIRDSENSE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│   │   AUDIO     │    │   IMAGE     │    │ DESCRIPTION │               │
│   │   INPUT     │    │   INPUT     │    │   INPUT     │               │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘               │
│          │                  │                   │                       │
│          ▼                  ▼                   ▼                       │
│   ┌──────────────────────────────────────────────────────────┐        │
│   │              PROVIDER FACTORY (providers.py)             │        │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │        │
│   │  │ Ollama   │  │  OpenAI  │  │    Azure OpenAI      │   │        │
│   │  │ Provider │  │ Provider │  │      Provider        │   │        │
│   │  └──────────┘  └──────────┘  └──────────────────────┘   │        │
│   └──────────────────────────────────────────────────────────┘        │
│          │                  │                   │                       │
│          ▼                  ▼                   ▼                       │
│   ┌──────────────────────────────────────────────────────────┐        │
│   │              ANALYSIS ENGINE (analysis.py)               │        │
│   │                                                          │        │
│   │  ┌────────────────┐  ┌───────────────┐  ┌────────────┐  │        │
│   │  │  SAM-Audio +   │  │  Vision Model │  │   Text     │  │        │
│   │  │   BirdNET      │  │   Analysis    │  │  Analysis  │  │        │
│   │  └────────────────┘  └───────────────┘  └────────────┘  │        │
│   └──────────────────────────────────────────────────────────┘        │
│          │                  │                   │                       │
│          ▼                  ▼                   ▼                       │
│   ┌──────────────────────────────────────────────────────────┐        │
│   │                 ENRICHMENT LAYER                         │        │
│   │  • Wikipedia/iNaturalist images                         │        │
│   │  • Species facts & habitat info                         │        │
│   │  • India-specific data (local names, birding spots)     │        │
│   └──────────────────────────────────────────────────────────┘        │
│          │                                                             │
│          ▼                                                             │
│   ┌──────────────────────────────────────────────────────────┐        │
│   │                    GRADIO UI (app.py)                    │        │
│   └──────────────────────────────────────────────────────────┘        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Module Details

### 1. Provider Factory (`providers.py`)

Implements the **Factory Pattern** for LLM backend abstraction.

```python
# Abstract base class
class LLMProvider(ABC):
    def check_connection(self) -> bool
    def call_vision(self, image, prompt) -> str
    def call_text(self, prompt) -> str
    def get_status(self) -> ProviderStatus

# Concrete implementations
class OllamaProvider(LLMProvider)      # Local models
class OpenAIProvider(LLMProvider)      # Public API
class AzureOpenAIProvider(LLMProvider) # Enterprise

# Factory
class ProviderFactory:
    def set_active(provider_name)  # "auto", "ollama", "cloud"
    def call_vision(image, prompt)
    def call_text(prompt)
    def get_status_html()
```

**Benefits:**
- Switch backends without code changes
- Auto-fallback between providers
- Centralized configuration

---

### 2. Analysis Engine (`analysis.py`)

Contains all bird identification logic.

#### SAMAudio Class

META SAM-inspired audio source separation:

```python
class SAMAudio:
    FREQ_BANDS = [
        (100, 500, "very_low"),    # Owls, bitterns
        (500, 1500, "low"),        # Crows, doves
        (1500, 3000, "medium"),    # Thrushes, mynas
        (3000, 6000, "high"),      # Finches, sparrows
        (6000, 10000, "very_high") # Warblers
    ]
    
    def detect_bird_segments(audio, sr) -> List[Dict]
    def separate_multiple_birds(audio, sr) -> List[Dict]
```

#### BirdNET Integration

```python
def identify_with_birdnet(audio, sr, location, month) -> List[Dict]:
    """
    Uses Cornell's BirdNET model (6000+ species)
    - Resamples to 48kHz
    - Returns species with confidence scores
    - min_conf=0.2 for better recall
    """
```

#### Hybrid Audio Pipeline

```python
def identify_audio_streaming(audio_input, location, month):
    """
    Novel 4-stage pipeline:
    
    Stage 1: SAM-Audio
    - Detect call segments
    - Separate by frequency bands (multi-bird detection)
    
    Stage 2: BirdNET Multi-Pass
    - Analyze full audio
    - Analyze each frequency band separately
    - Merge unique species
    
    Stage 3: Feature Extraction
    - Frequency range, pattern, complexity
    - Syllable count, rhythm
    
    Stage 4: LLM Validation
    - Contextual reasoning
    - Location/season validation
    """
```

---

### 3. Prompts (`prompts.py`)

All LLM prompts externalized for easy modification.

```python
# Model-specific prompts
AUDIO_PROMPT_OLLAMA = "..."  # Concise for local models
AUDIO_PROMPT_GPT = "..."     # Detailed for GPT

IMAGE_PROMPT_OLLAMA = "..."
IMAGE_PROMPT_GPT = "..."

# Enrichment prompts
BIRD_ENRICHMENT_PROMPT = "..."
BIRD_ENRICHMENT_PROMPT_INDIA = "..."  # With local names

# Selectors
def get_audio_prompt(backend) -> str
def get_image_prompt(backend) -> str
def get_enrichment_prompt(bird_name, scientific, location) -> str
```

---

### 4. UI Layer (`app.py`)

Clean Gradio interface (~250 lines).

```python
def create_app():
    with gr.Blocks():
        # Backend selector (Auto/Ollama/Cloud)
        # Status display
        
        # Tabs
        - Audio tab (with location/month)
        - Image tab (with location)
        - Description tab (with location)
        - Feedback tab
        - Analytics tab
        - About tab
```

---

## Novel Contributions

### 1. Multi-Stage Hybrid Architecture

Unlike single-model approaches, BirdSense uses:
- **Specialized model (BirdNET)** for pattern matching
- **LLM** for reasoning and validation
- **SAM-Audio** for source separation

### 2. Frequency-Band Multi-Bird Detection

```
Audio with multiple birds:
    │
    ├── Low band (500-1500 Hz) ──→ BirdNET ──→ Crow detected
    │
    ├── Medium band (1500-3000 Hz) ──→ BirdNET ──→ Myna detected  
    │
    └── High band (3000-6000 Hz) ──→ BirdNET ──→ Finch detected
```

### 3. LLM Validation Layer

BirdNET is the "gold standard" - LLM **enhances**, not overrides:

```python
if birdnet_confidence >= 70%:
    # Trust BirdNET, use LLM for context/enrichment only
else:
    # Use LLM to validate/disambiguate lower confidence results
```

### 4. Scientific Name Priority for Images

```python
# Fetch order (most specific first)
1. Scientific name (e.g., "Parus major")
2. Common name + "(bird)"
3. Common name
4. Wikimedia Commons search
5. iNaturalist fallback
```

---

## Data Flow

### Audio Identification

```
User uploads audio
    │
    ▼
Normalize (mono, float64)
    │
    ▼
SAM-Audio: Detect segments + separate bands
    │
    ├─── Full audio ─────────┐
    ├─── Low band ───────────┤
    ├─── Medium band ────────┼──→ BirdNET (each)
    ├─── High band ──────────┤
    └─── Very high band ─────┘
           │
           ▼
    Deduplicate results
           │
           ▼
    Extract acoustic features
           │
           ▼
    LLM validation (if needed)
           │
           ▼
    Enrich (images, facts, India info)
           │
           ▼
    Stream results to UI
```

### Image Identification

```
User uploads image
    │
    ▼
Convert to RGB, resize
    │
    ▼
Vision model (LLaVA/GPT-4o)
    │
    ▼
Parse JSON response
    │
    ▼
Deduplicate birds
    │
    ▼
Enrich each bird:
    ├── Fetch image (scientific name)
    ├── Get Wikipedia summary
    └── Get India info (always)
           │
           ▼
    Stream results to UI
```

---

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `IS_AZURE` | Use Azure OpenAI | `true` |
| `LITELLM_API_KEY` | API key | `your-key` |
| `LITELLM_API_BASE` | API endpoint | `https://...` |
| `AZURE_DEPLOYMENT` | Deployment name | `gpt4o-130524` |
| `AZURE_API_VERSION` | API version | `2024-02-15-preview` |
| `LITELLM_VISION_MODEL` | Vision model | `gpt-4o` |
| `LITELLM_TEXT_MODEL` | Text model | `gpt-4o` |
| `OLLAMA_HOST` | Ollama URL | `http://localhost:11434` |

---

## Performance Considerations

### Local (Ollama)
- Vision model: ~5-10s per image
- Text model: ~2-5s per query
- BirdNET: ~1-3s per audio

### Cloud (Azure/OpenAI)
- Vision model: ~2-5s per image
- Text model: ~1-2s per query
- Network latency dependent

### Optimization Tips
1. Use cloud backend for production
2. Cache enrichment data
3. Parallel image/info fetching

---

## Security Notes

- API keys stored in `.env` (gitignored)
- Environment variables in Cloud Run
- No hardcoded credentials in code
- SSL verification disabled for internal endpoints (VPN)

---

**🐦 BirdSense Architecture** - *Developed by Soham*

