# 🐦 BirdSense - Intelligent Bird Recognition System

> **A Novel Multi-Modal Bird Recognition Model for CSCR Initiative**  
> Competitive with BirdNET | India-First Focus | Meta SAM-Audio Enhanced | Self-Learning | Mobile-Ready

## 🎯 Vision

1. **#1 Bird Recognition Model** - Surpass BirdNET accuracy, especially for Indian species
2. **Mobile-Ready** - Lightweight models optimized for edge deployment
3. **Self-Learning** - Continuous improvement from avian signals, research, and citizen science
4. **Novelty Detection** - Identify new species or out-of-range sightings

## 🚀 Quick Start for Researchers

### Start the Web Interface

```bash
cd birdsense
source venv/bin/activate

# Start API server with web UI
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

**Open in browser:** `http://localhost:8000/app`

**Share with team:** `http://<your-ip>:8000/app`

### Features
- 🎤 **Live Recording** - Record from microphone with real-time waveform
- 📊 **Live Histogram** - See frequency distribution in real-time
- 📁 **File Upload** - Upload WAV, MP3, FLAC samples
- 🤖 **AI Reasoning** - LLM-enhanced species identification
- 🔔 **Novelty Alerts** - Detect unusual sightings

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      BirdSense Pipeline                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INPUT → SAM-Audio → Preprocessing → Encoder → Classifier        │
│           ↓              ↓              ↓          ↓              │
│    Source      →    Spectrogram → Embedding → Predictions       │
│  Separation           + Noise         384-dim      ↓              │
│  (Meta AI)          Reduction                  LLM Reasoning      │
│                                                    ↓              │
│                                              Final Output         │
│                                           (85%+ confidence)       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🧠 Meta SAM-Audio Integration

BirdSense integrates Meta's state-of-the-art [SAM-Audio](https://ai.meta.com/samaudio/) (Segment Anything in Audio) for:

- **Source Separation** - Isolate bird calls from background noise
- **Multi-Bird Handling** - Separate overlapping bird calls
- **Feeble Recording Enhancement** - Boost weak signals
- **Noise Removal** - Handle urban/forest ambient noise

Reference: [SAM-Audio Paper](https://ai.meta.com/research/publications/sam-audio-segment-anything-in-audio/)

## 📱 Web Interface

The beautiful researcher interface includes:

| Feature | Description |
|---------|-------------|
| **Live Recording** | Record from device microphone |
| **Real-time Waveform** | Visualize audio as you record |
| **Frequency Histogram** | See bird call frequencies live |
| **File Upload** | Drag & drop audio files |
| **Streaming Results** | See AI analysis in real-time |
| **LLM Reasoning** | Natural language explanations |
| **Novelty Alerts** | Unusual sighting notifications |

## 🔧 Installation

### Prerequisites
- Python 3.10+
- ~4GB disk space (with models)
- Ollama (for LLM reasoning)

### Setup

```bash
cd birdsense
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Pull Ollama model (recommended: qwen2.5:3b)
ollama pull qwen2.5:3b
ollama serve &  # Start in background
```

## 📊 Training on Xeno-Canto

```bash
# Download training data (100+ Indian species)
python -c "
import asyncio
from training.xeno_canto import download_india_birds
asyncio.run(download_india_birds())
"

# Train model
python -m training.trainer \
  --data-dir data/xeno-canto \
  --epochs 100 \
  --batch-size 32
```

## 🐦 Supported Species

**25+ species in MVP**, expanding to **500+ Indian birds**:

- Common: Asian Koel, Indian Cuckoo, House Sparrow, Common Myna
- Endemic: Indian Robin, Grey Junglefowl, Indian Peafowl
- Wetland: Kingfishers, Egrets, Herons
- Forest: Barbets, Orioles, Drongos
- Conservation priority: Vultures, Bustards, Floricans

## 📁 Project Structure

```
birdsense/
├── api/                    # REST API
│   └── server.py           # FastAPI with streaming
├── webapp/                 # Web Interface
│   ├── index.html          # Main page
│   ├── styles.css          # Beautiful dark theme
│   └── app.js              # Recording, upload, visualization
├── audio/                  # Audio Processing
│   ├── preprocessor.py     # Spectrograms
│   ├── augmentation.py     # Data augmentation
│   ├── encoder.py          # Neural network
│   └── sam_audio.py        # Meta SAM-Audio integration
├── models/
│   ├── audio_classifier.py # Species classifier
│   └── novelty_detector.py # Unusual detection
├── llm/
│   ├── ollama_client.py    # LLM interface
│   └── reasoning.py        # Species reasoning
├── training/
│   ├── xeno_canto.py       # Download data
│   ├── dataset.py          # PyTorch dataset
│   └── trainer.py          # Training loop
├── data/
│   └── species_db.py       # Species database
└── tests/
    └── test_audio_conditions.py
```

## 🎯 Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Top-1 Accuracy | 85%+ | Training needed |
| Top-5 Accuracy | 95%+ | Training needed |
| Confidence (correct) | 85%+ | Calibrated |
| Inference Latency | <100ms | ~50ms |
| Model Size | <20MB | ~8MB |

## 🔗 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/app` | GET | Web interface |
| `/api/v1/identify` | POST | Identify bird (JSON) |
| `/api/v1/identify/stream` | POST | Identify bird (streaming) |
| `/api/v1/species` | GET | List all species |
| `/api/v1/health` | GET | Health check |
| `/docs` | GET | API documentation |

## 📚 References

- [Meta SAM-Audio](https://ai.meta.com/samaudio/) - Audio source separation
- [HuggingFace Model](https://huggingface.co/facebook/sam-audio-large) - Pre-trained weights
- [Xeno-Canto](https://xeno-canto.org/) - Bird audio database
- [eBird India](https://ebird.org/india) - Species checklists

## 🤝 Contributing

Part of the **CSCR (Citizen Science for Conservation Research)** initiative.

## 📄 License

MIT License - Open for research and conservation use.
