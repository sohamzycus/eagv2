# 📁 BirdSense Project Structure

**Share this document with your ML architect for a complete project overview.**

---

## Repository Structure

```
birdsense/
├── 📄 README.md                     # Project overview & quick start
├── 📄 ARCHITECTURE.md               # Technical architecture (with SAM-Audio)
├── 📄 DEPLOY.md                     # Deployment guide (HuggingFace, Render, etc.)
├── 📄 RESEARCHER_GUIDE.md           # Guide for field researchers
├── 📄 QUICK_START.md                # 5-minute setup guide
│
├── 📄 docs/
│   └── ML_ARCHITECT_REVIEW.md       # Detailed enterprise architecture review
│
├── ⚙️ config/
│   └── config.yaml                  # Model & API configuration
│
├── 🎵 audio/                        # Audio Processing Module
│   ├── __init__.py
│   ├── preprocessor.py              # Audio loading, filtering, mel-spectrogram
│   ├── augmentation.py              # Data augmentation (noise, stretch, pitch)
│   ├── encoder.py                   # CNN audio encoder (EfficientNet-style)
│   └── sam_audio.py                 # Meta SAM-Audio integration
│
├── 🧠 models/                       # ML Models
│   ├── __init__.py
│   ├── audio_classifier.py          # Species classifier head
│   └── novelty_detector.py          # Out-of-distribution detection
│
├── 🗃️ data/                         # Data Management
│   ├── __init__.py
│   └── species_db.py                # India bird species database (25+)
│
├── 🤖 llm/                          # LLM Integration
│   ├── __init__.py
│   ├── ollama_client.py             # Ollama API client
│   └── reasoning.py                 # LLM-based species reasoning
│
├── 📡 api/                          # REST API
│   ├── __init__.py
│   └── server.py                    # FastAPI server with streaming
│
├── 🌐 webapp/                       # Web User Interface
│   ├── index.html                   # Main page
│   ├── styles.css                   # Dark theme styling
│   └── app.js                       # Recording, upload, visualization
│
├── 📊 training/                     # Model Training
│   ├── __init__.py
│   ├── xeno_canto.py                # Xeno-Canto data downloader
│   ├── dataset.py                   # PyTorch dataset
│   └── trainer.py                   # Training loop with calibration
│
├── 🧪 tests/                        # Test Suite
│   ├── __init__.py
│   └── test_audio_conditions.py     # 48 comprehensive tests
│
├── 📁 samples/                      # Test audio samples
│   ├── koel_sample.wav
│   ├── cuckoo_sample.wav
│   ├── kingfisher_sample.wav
│   └── mixed_birds.wav
│
├── 📁 checkpoints/                  # Model weights (gitignored)
│
├── 🐳 Dockerfile                    # Container build
├── 🐳 docker-compose.yml            # Multi-container deployment
├── 🎨 huggingface_app.py            # Gradio app for HuggingFace Spaces
├── 📦 requirements.txt              # Python dependencies
├── 📦 requirements_hf.txt           # Minimal deps for HuggingFace
├── ⚙️ setup.py                      # Package setup
├── 🚀 run_demo.py                   # CLI demo runner
└── 🚫 .gitignore                    # Git ignore rules
```

---

## Key Components

### 1️⃣ Audio Processing Pipeline

| File | Purpose | Key Functions |
|------|---------|---------------|
| `audio/preprocessor.py` | Load, filter, normalize audio | `process()`, `get_audio_quality_assessment()` |
| `audio/augmentation.py` | Data augmentation | `add_noise()`, `time_stretch()`, `pitch_shift()` |
| `audio/encoder.py` | CNN feature extraction | `forward()` → 384-dim embedding |
| `audio/sam_audio.py` | Meta SAM-Audio separation | `enhance_audio()`, `separate_sources()` |

### 2️⃣ ML Models

| File | Purpose | Architecture |
|------|---------|--------------|
| `models/audio_classifier.py` | Species classification | Linear head on 384-dim embedding |
| `models/novelty_detector.py` | Detect unknown species | Mahalanobis distance |

### 3️⃣ LLM Integration

| File | Purpose | Model |
|------|---------|-------|
| `llm/ollama_client.py` | Local LLM inference | qwen2.5:3b (recommended) |
| `llm/reasoning.py` | Context-aware reasoning | Habitat/season validation |

### 4️⃣ API & Web Interface

| File | Purpose | Endpoints |
|------|---------|-----------|
| `api/server.py` | FastAPI backend | `/identify`, `/species`, `/health` |
| `webapp/*` | Researcher UI | Recording, upload, histogram |
| `huggingface_app.py` | Gradio interface | For public deployment |

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     BIRDSENSE DATA FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   FIELD RECORDING                                                │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │  Web App    │    │  REST API   │    │   Mobile    │        │
│   │  /app       │───▶│  /identify  │◀───│   SDK       │        │
│   └─────────────┘    └──────┬──────┘    └─────────────┘        │
│                             │                                    │
│                             ▼                                    │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │                    PROCESSING PIPELINE                    │ │
│   │                                                           │ │
│   │  1. SAM-Audio → Source separation (if noisy)             │ │
│   │  2. Preprocessor → Mel-spectrogram                       │ │
│   │  3. Encoder → 384-dim embedding                          │ │
│   │  4. Classifier → Top-5 predictions                       │ │
│   │  5. Novelty Detector → Out-of-range check                │ │
│   │  6. LLM Reasoning → Final species + explanation          │ │
│   │                                                           │ │
│   └──────────────────────────────────────────────────────────┘ │
│                             │                                    │
│                             ▼                                    │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │                      RESPONSE                             │ │
│   │                                                           │ │
│   │  {                                                        │ │
│   │    "species": "Asian Koel",                              │ │
│   │    "confidence": 0.87,                                   │ │
│   │    "reasoning": "The distinctive 'ku-oo' call...",       │ │
│   │    "novelty_alert": null                                 │ │
│   │  }                                                        │ │
│   └──────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Audio Processing** | librosa, scipy, soundfile | Industry-standard bioacoustics |
| **ML Framework** | PyTorch | Flexibility, research-friendly |
| **Audio Separation** | Meta SAM-Audio | State-of-the-art, zero-shot |
| **LLM** | Ollama (qwen2.5:3b) | Local, private, fast |
| **API** | FastAPI | Modern, async, auto-docs |
| **Web UI** | Vanilla JS + CSS | Lightweight, no build step |
| **Deployment** | Docker, HuggingFace | Free, easy sharing |

---

## Model Architecture Summary

```
Input: Audio (WAV/MP3, any sample rate)
         │
         ▼
SAM-Audio (Optional)
  ├── Source separation
  ├── Noise removal
  └── Multi-bird handling
         │
         ▼
Preprocessor
  ├── Resample to 32kHz
  ├── Bandpass filter (50Hz-14kHz)
  └── Mel-spectrogram (128 bins)
         │
         ▼
CNN Encoder (EfficientNet-style)
  ├── 7 MBConv stages
  ├── SE attention blocks
  ├── ~2M parameters
  └── Output: 384-dim embedding
         │
         ▼
Classifier Head
  ├── Linear (384 → num_classes)
  ├── Softmax
  └── Output: Top-K predictions
         │
         ▼
LLM Reasoning (Ollama)
  ├── Context integration
  ├── Habitat/season validation
  └── Output: Final species + reasoning
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/identify` | Identify species from audio |
| `POST` | `/api/v1/identify/stream` | Streaming SSE response |
| `GET` | `/api/v1/species` | List all species |
| `GET` | `/api/v1/species/{id}` | Species details |
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/status` | Model & system status |
| `GET` | `/app` | Web UI |
| `GET` | `/docs` | API documentation |

---

## Running Locally

```bash
# 1. Setup
cd birdsense
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Install Ollama (for LLM reasoning)
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5:3b

# 3. Start API server
uvicorn api.server:app --host 0.0.0.0 --port 8000

# 4. Open in browser
open http://localhost:8000/app
```

---

## Deployment Options

| Platform | Cost | URL Pattern | GPU |
|----------|------|-------------|-----|
| **HuggingFace Spaces** | FREE | `huggingface.co/spaces/USER/birdsense` | Optional |
| Render | FREE | `birdsense.onrender.com` | No |
| Railway | $5/mo | `birdsense.up.railway.app` | No |
| Fly.io | FREE | `birdsense.fly.dev` | No |
| Docker | Self-host | Custom | Optional |

---

## Files for ML Architect Review

1. **`docs/ML_ARCHITECT_REVIEW.md`** - Comprehensive enterprise review document
2. **`ARCHITECTURE.md`** - Visual architecture diagrams with SAM-Audio integration
3. **`README.md`** - Project overview and results
4. **`training/trainer.py`** - Training pipeline with calibration
5. **`audio/sam_audio.py`** - Meta SAM-Audio integration

---

## Contact

**Project:** BirdSense - CSCR Initiative  
**Status:** MVP Ready for Training & Deployment  
**Next:** Train on Xeno-Canto data, deploy to HuggingFace Spaces

