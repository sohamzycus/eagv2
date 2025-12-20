# 🐦 BirdSense - AI Bird Identification

**Developed by Soham**

A novel hybrid AI system for bird identification combining multiple approaches for superior accuracy.

## 🧠 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BirdSense Hybrid Architecture                     │
│                           Developed by Soham                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                │
│  │   AUDIO     │     │   IMAGE     │     │ DESCRIPTION │                │
│  │   Input     │     │   Input     │     │   Input     │                │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                │
│         │                   │                   │                        │
│         ▼                   │                   │                        │
│  ┌─────────────────┐        │                   │                        │
│  │  META SAM-Audio │        │                   │                        │
│  │  ─────────────  │        │                   │                        │
│  │  • Noise filter │        │                   │                        │
│  │  • Call isolate │        │                   │                        │
│  │  • Segment det. │        │                   │                        │
│  └────────┬────────┘        │                   │                        │
│           │                 │                   │                        │
│           ▼                 │                   │                        │
│  ┌─────────────────┐        │                   │                        │
│  │    BirdNET      │        │                   │                        │
│  │   (Cornell)     │        │                   │                        │
│  │  ─────────────  │        │                   │                        │
│  │  • 6000+ species│        │                   │                        │
│  │  • Spectrogram  │        │                   │                        │
│  │  • CNN pattern  │        │                   │                        │
│  └────────┬────────┘        │                   │                        │
│           │                 │                   │                        │
│           ▼                 ▼                   ▼                        │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │                    LLM Reasoning Layer                       │        │
│  │                    ──────────────────                        │        │
│  │   phi4 (14B)              LLaVA (7B)           phi4 (14B)    │        │
│  │   ─────────               ─────────            ─────────     │        │
│  │   • Context valid.        • Vision analysis    • Text reason │        │
│  │   • Location filter       • Feature extract    • Description │        │
│  │   • Season reason.        • Multi-bird det.    • matching    │        │
│  └─────────────────────────────────────────────────────────────┘        │
│                               │                                          │
│                               ▼                                          │
│                    ┌─────────────────────┐                               │
│                    │   Deduplication &   │                               │
│                    │   Confidence Merge  │                               │
│                    └──────────┬──────────┘                               │
│                               │                                          │
│                               ▼                                          │
│                    ┌─────────────────────┐                               │
│                    │  STREAMING RESULTS  │                               │
│                    │  ─────────────────  │                               │
│                    │  • Real-time trail  │                               │
│                    │  • Unique species   │                               │
│                    │  • Wikipedia images │                               │
│                    └─────────────────────┘                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## ✨ Key Features

### 1. **Hybrid BirdNET + LLM Pipeline**
- BirdNET (Cornell Lab): Pattern-based spectrogram analysis for 6000+ species
- LLM Validation: Contextual reasoning using location, season, and behavior
- **Novel contribution**: Combines best of both approaches

### 2. **META SAM-Audio Processing**
- Inspired by Meta's Segment Anything Model
- Isolates bird calls from background noise
- Detects multiple birds in same recording
- Frequency band separation for multi-species detection

### 3. **Feature-Based Identification**
- Systematic feature analysis (beak, head, body patterns)
- No hardcoded species rules
- Flexible for any bird species

### 4. **Streaming Results**
- Real-time analysis trail shows progress
- Birds displayed as identified (not waiting for all)
- Deduplication ensures each species shown once

## 🚀 Quick Start

### Option 1: Cloud Hosting (FREE, Permanent, Auto-Deploy)

Deploy to **Render.com** with **Groq API** (100% FREE, no credit card):

```bash
./deploy.sh cloud   # Shows step-by-step instructions
```

**5-Minute Setup:**
1. Get **FREE** API key at https://console.groq.com (no credit card!)
2. Go to https://render.com → New → Web Service
3. Connect GitHub repo: `sohamzycus/eagv2`, Root: `birdsense`, Runtime: Docker
4. Add env var: `GROQ_API_KEY` (your free Groq key)
5. Deploy! **Auto-refreshes on every git push.**

### Option 2: Local with GPU (Best Accuracy)

```bash
./deploy.sh local   # Sets up Ollama + models + runs app
```

### Option 3: Docker (Portable)

```bash
./deploy.sh docker  # Runs in Docker containers
```

### Option 4: Manual Setup

```bash
# 1. Prerequisites
brew install python@3.12 ollama  # Mac
# Or: curl -fsSL https://ollama.ai/install.sh | sh  # Linux

# 2. Start Ollama and pull models
ollama serve &
ollama pull llava:7b
ollama pull phi4

# 3. Setup Python environment
cd birdsense
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Run
python app.py
# Open http://localhost:7860
```

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| Storage | 15 GB | 25 GB |
| GPU | None (CPU works) | Apple M1+ or NVIDIA |
| Python | 3.12 | 3.12 |

## 📁 Project Structure

```
birdsense/
├── app.py              # Single codebase (auto-detects Ollama or Groq)
├── prompts.py          # External LLM prompts
├── confusion_rules.py  # Feature-based validation
├── feedback.py         # Feedback & analytics collection
├── export_data.py      # Export collected data
├── deploy.sh           # One-command deployment (local/docker/cloud)
├── Dockerfile          # Docker container config
├── docker-compose.yml  # Multi-container setup
├── render.yaml         # Render.com auto-deploy config
├── requirements.txt    # Local dependencies (with BirdNET)
├── requirements_cloud.txt  # Docker dependencies (lightweight)
├── .github/workflows/  # Auto-deploy on GitHub push
└── README.md           # This file
```

### Single Codebase - Auto-Detects Runtime:

| Mode | Detection | Models | Best For |
|------|-----------|--------|----------|
| **Local** | Ollama running | LLaVA + phi4 + BirdNET | Best accuracy |
| **Cloud** | GROQ_API_KEY set | Llama 3.2 Vision | FREE hosting |

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Audio ID | BirdNET (Cornell) + TensorFlow | Spectrogram pattern matching |
| Image ID | LLaVA 7B | Vision-language analysis |
| Text ID | phi4 (14B) | Reasoning & validation |
| Audio Processing | META SAM-Audio | Noise filtering, call isolation |
| UI | Gradio | Web interface |
| Image Source | Wikipedia/iNaturalist | Reference photos |

## 🧪 What Makes BirdSense Novel

1. **Hybrid Ensemble**: First to combine BirdNET + LLM for bird ID
2. **Contextual Validation**: LLM validates ML predictions using location/season
3. **Multi-Modal Fusion**: Audio + Image + Description analysis
4. **Streaming UX**: Real-time progress and results
5. **100% Local**: No cloud APIs required

## 📊 Comparison

| Feature | BirdNET Only | GPT-5 | BirdSense |
|---------|-------------|-------|-----------|
| Spectrogram Analysis | ✅ | ❌ | ✅ |
| Contextual Reasoning | ❌ | ✅ | ✅ |
| Location Awareness | Basic | ✅ | ✅ |
| Multi-modal | Audio only | Text/Image | **All 3** |
| Runs Locally | ✅ | ❌ | ✅ |
| Species Count | 6000+ | General | **6000+** |

## 🌐 Hosting for Testing

Share BirdSense with others for testing and feedback collection:

### Quick Share (Gradio Public URL)

```bash
# Creates a temporary public URL (valid for 72 hours)
python host.py

# Output: "Running on public URL: https://xxx.gradio.live"
```

This uses Gradio's built-in sharing feature - no extra setup required!

### Persistent Hosting Options

| Method | Cost | Setup Complexity | GPU |
|--------|------|------------------|-----|
| **Gradio Share** | Free | ⭐ (1 command) | Your local GPU |
| **ngrok** | Free tier | ⭐⭐ | Your local GPU |
| **Railway.app** | ~$5/mo | ⭐⭐⭐ | CPU only (slow) |
| **VPS + Ollama** | ~$20/mo | ⭐⭐⭐⭐ | Depends on VPS |

### Share Link Workflow

```bash
# 1. Start public hosting
python host.py

# 2. Share the gradio.live URL with testers
# 3. Testers use the Feedback tab to report results
# 4. Export feedback when done:
python export_data.py --export all
```

## 📊 Feedback & Sample Collection

BirdSense includes built-in audit and feedback collection:

### In-App Feedback
- **Feedback Tab**: Users can report if identification was correct/incorrect
- **Correct Species**: When wrong, users can provide the correct species
- **Notes**: Additional feedback for edge cases

### Data Export

```bash
# Show summary of collected data
python export_data.py

# Export feedback as JSON
python export_data.py --export feedback

# Export samples (audio/images with corrections)
python export_data.py --export samples

# Export everything
python export_data.py --export all
```

### Analytics Dashboard
Access the **📊 Analytics** tab in the app to see:
- Total predictions
- Accuracy from user feedback
- Top identified species
- Breakdown by input type

## 📁 Project Structure

```
birdsense/
├── app.py              # Main application (Gradio UI + pipelines)
├── prompts.py          # External LLM prompts (no hardcoding)
├── confusion_rules.py  # Feature-based validation
├── feedback.py         # Feedback & sample collection
├── host.py             # Public hosting script
├── export_data.py      # Data export utility
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## 🔮 Future Roadmap

- [ ] Geolocation auto-filtering (lat/lon based species filtering)
- [ ] Spectrogram visualization
- [ ] Custom model fine-tuning on regional data
- [ ] Mobile app (TensorFlow Lite)
- [ ] Offline mode with embedded models

---

**Developed by Soham** | BirdSense v1.0
