# 🐦 BirdSense Quick Start Guide

Get the MVP running in 5 minutes!

## Prerequisites

- Python 3.10+
- ~4GB free disk space
- (Optional) Ollama for LLM reasoning

## Installation

### Option 1: Automated Setup

```bash
cd birdsense
python setup.py
```

### Option 2: Manual Setup

```bash
# Create virtual environment
cd birdsense
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Install Ollama for LLM reasoning
# macOS/Linux:
curl -fsSL https://ollama.com/install.sh | sh
ollama pull phi3:mini

# Start Ollama server (in separate terminal)
ollama serve
```

## Running the Demo

### 1. Test All Audio Scenarios

```bash
python run_demo.py --test-all
```

This runs tests for:
- ✅ Clear recordings (high SNR)
- ✅ Feeble/distant audio (low amplitude)
- ✅ Noisy environments (urban, forest noise)
- ✅ Multi-bird chorus (overlapping calls)
- ✅ Brief calls (<1 second)

### 2. Interactive Mode

```bash
python run_demo.py --interactive
```

Navigate through options:
```
Options:
  1. Test with clear audio
  2. Test with feeble audio
  3. Test with noisy audio
  4. Test with multi-bird audio
  5. Test with brief call
  6. Record from microphone
  7. Run all tests
  8. List species database
  q. Quit
```

### 3. Process Audio File

```bash
python run_demo.py --audio path/to/bird_recording.wav
```

Supported formats: WAV, MP3, FLAC, OGG

### 4. Record from Microphone

```bash
python run_demo.py --record --duration 10
```

Records 10 seconds from your microphone and identifies the bird.

### 5. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test category
pytest tests/test_audio_conditions.py::TestPreprocessor -v
pytest tests/test_audio_conditions.py::TestRobustness -v
```

## Sample Output

```
╔══════════════════════════════════════════════════════════════╗
║   🐦 BirdSense MVP - Intelligent Bird Recognition           ║
╚══════════════════════════════════════════════════════════════╝

━━━ Scenario: NOISY ━━━

📊 Audio Analysis
┌─────────────────────────────────────────────────────────────┐
│ Audio: Noisy Environment                                     │
│ Duration: 3.00s (1 chunks)                                  │
│ Quality: FAIR (score: 0.45)                                 │
│ SNR: ~8.2 dB                                                │
└─────────────────────────────────────────────────────────────┘

🐦 Species Predictions
┌──────┬─────────────────────┬───────────────────────┬────────────┐
│ Rank │ Species             │ Scientific Name       │ Confidence │
├──────┼─────────────────────┼───────────────────────┼────────────┤
│ #1   │ Asian Koel          │ Eudynamys scolopaceus │ 34.5%      │
│ #2   │ Indian Cuckoo       │ Cuculus micropterus   │ 22.1%      │
│ #3   │ Coppersmith Barbet  │ Psilopogon haemace... │ 15.3%      │
└──────┴─────────────────────┴───────────────────────┴────────────┘

🎯 Uncertainty: 45.2%

🤖 AI Reasoning
┌─────────────────────────────────────────────────────────────┐
│ LLM Assessment: Asian Koel                                  │
│ Confidence: 60%                                             │
│                                                              │
│ The audio quality is fair with significant noise, but the   │
│ characteristic rising whistle pattern suggests Asian Koel.  │
│ The koel's loud "kuil-kuil" call can often be heard even   │
│ in noisy urban environments...                              │
└─────────────────────────────────────────────────────────────┘
```

## Model Architecture

The MVP uses a lightweight architecture optimized for edge deployment:

| Component | Size | Description |
|-----------|------|-------------|
| Audio Encoder | ~2MB | Efficient CNN with SE blocks |
| Classifier Head | ~0.5MB | 2-layer MLP with dropout |
| **Total** | **~2.5MB** | Runs on mobile devices |

Optional LLM reasoning (via Ollama):
- Model: `phi3:mini` (~2.3GB)
- Runs locally, no API calls needed

## Directory Structure

```
birdsense/
├── audio/                  # Audio processing
│   ├── preprocessor.py     # Spectrogram, noise reduction
│   ├── augmentation.py     # Data augmentation
│   └── encoder.py          # Neural network encoder
├── models/                 # Model definitions
│   ├── audio_classifier.py # Main classifier
│   └── novelty_detector.py # Unusual species detection
├── llm/                    # LLM integration
│   ├── ollama_client.py    # Ollama API client
│   └── reasoning.py        # Species reasoning engine
├── data/
│   └── species_db.py       # India bird species database
├── tests/
│   └── test_audio_conditions.py
├── config/
│   └── config.yaml
├── run_demo.py             # Main demo script
├── setup.py                # Automated setup
└── requirements.txt
```

## Troubleshooting

### "No module named 'librosa'"
```bash
pip install librosa
```

### "sounddevice not found" (for recording)
```bash
pip install sounddevice
```

### Ollama connection error
1. Make sure Ollama is running: `ollama serve`
2. Check if model is downloaded: `ollama list`
3. Download model if missing: `ollama pull phi3:mini`

### Poor recognition accuracy
- Use high-quality audio recordings
- Reduce background noise when possible
- Ensure bird calls are at least 1 second long
- Try recording closer to the bird

## Next Steps

After testing the MVP:

1. **Add real training data**
   - Download from Xeno-Canto: https://xeno-canto.org/
   - Focus on Indian bird species

2. **Train the model**
   - Use the training script (coming soon)
   - Fine-tune on your regional species

3. **Deploy to mobile**
   - Export to ONNX format
   - Use TFLite for Android/iOS

## Support

For issues or contributions, please open a GitHub issue or contact the CSCR team.

