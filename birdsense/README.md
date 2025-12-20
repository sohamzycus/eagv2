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

```bash
# Prerequisites
brew install python@3.12
ollama pull llava:7b
ollama pull phi4

# Setup
cd birdsense
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python app.py
# Open http://localhost:7860
```

## 📁 Project Structure

```
birdsense/
├── app.py              # Main application (Gradio UI + pipelines)
├── prompts.py          # External LLM prompts (no hardcoding)
├── confusion_rules.py  # Feature-based validation
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

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

## 🔮 Future Roadmap

- [ ] Geolocation auto-filtering (lat/lon based species filtering)
- [ ] Spectrogram visualization
- [ ] Custom model fine-tuning on regional data
- [ ] Mobile app (TensorFlow Lite)
- [ ] Offline mode with embedded models

---

**Developed by Soham** | BirdSense v1.0
