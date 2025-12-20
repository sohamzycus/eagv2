# 🐦 BirdSense Researcher Guide

## Quick Access for Testing

### Option 1: Web API (Recommended for Sharing)

Start the API server:
```bash
cd birdsense
source venv/bin/activate
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

**Share this URL with researchers:**
```
http://<your-ip>:8000/docs
```

This provides:
- Interactive API documentation (Swagger UI)
- File upload for testing
- Real-time streaming results
- All species information

### Option 2: Ngrok for Public Access

For sharing with external researchers without VPN:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# Start tunnel
ngrok http 8000
```

Share the generated URL (e.g., `https://abc123.ngrok.io/docs`)

### Option 3: Command Line Demo

```bash
python run_demo.py --interactive
```

---

## API Endpoints

### 1. Identify Bird (with streaming)

**Streaming endpoint for real-time results:**
```
POST /api/v1/identify/stream
```

Example with curl:
```bash
curl -X POST "http://localhost:8000/api/v1/identify/stream" \
  -F "audio=@bird_recording.wav" \
  -F "location_name=Western Ghats" \
  -F "use_llm=true"
```

### 2. Identify Bird (JSON response)

```
POST /api/v1/identify
```

Example:
```bash
curl -X POST "http://localhost:8000/api/v1/identify" \
  -F "audio=@bird_recording.wav" \
  -F "location_name=Kaziranga" \
  -F "month=3" \
  -F "use_llm=true"
```

Response:
```json
{
  "request_id": "uuid",
  "top_prediction": "Asian Koel",
  "top_confidence": 0.89,
  "predictions": [
    {
      "rank": 1,
      "common_name": "Asian Koel",
      "scientific_name": "Eudynamys scolopaceus",
      "hindi_name": "कोयल",
      "confidence": 0.89
    }
  ],
  "llm_reasoning": {
    "species": "Asian Koel",
    "confidence": 0.92,
    "reasoning": "The distinctive rising 'kuil' whistle pattern strongly suggests Asian Koel..."
  }
}
```

### 3. List All Species

```
GET /api/v1/species
```

Filter by habitat:
```
GET /api/v1/species?habitat=forest
```

Filter endemic species:
```
GET /api/v1/species?endemic_only=true
```

### 4. Health Check

```
GET /api/v1/health
```

---

## Python SDK Usage

```python
import httpx
import asyncio

async def identify_bird(audio_path: str, location: str = None):
    async with httpx.AsyncClient() as client:
        with open(audio_path, 'rb') as f:
            response = await client.post(
                "http://localhost:8000/api/v1/identify",
                files={"audio": f},
                params={
                    "location_name": location,
                    "use_llm": True
                }
            )
        return response.json()

# Usage
result = asyncio.run(identify_bird("bird.wav", "Kerala Backwaters"))
print(f"Species: {result['top_prediction']}")
print(f"Confidence: {result['top_confidence']:.1%}")
```

---

## Training Your Own Model

### 1. Download Training Data

```bash
cd birdsense
source venv/bin/activate

# Download 5 species for testing
python -c "
import asyncio
from training.xeno_canto import download_india_birds
asyncio.run(download_india_birds(max_species=5))
"

# Download all ~100+ species (takes time)
python -c "
import asyncio
from training.xeno_canto import download_india_birds
asyncio.run(download_india_birds())
"
```

### 2. Train Model

```bash
python -m training.trainer \
  --data-dir data/xeno-canto \
  --output-dir checkpoints \
  --epochs 100 \
  --batch-size 32 \
  --classes 100
```

### 3. Monitor Training

Training outputs:
- `checkpoints/best.pt` - Best model weights
- `checkpoints/best_calibrated.pt` - Calibrated model (85%+ confidence)
- `checkpoints/training_results.json` - Full training metrics

---

## Confidence Calibration

The model is trained with **label smoothing** and **temperature scaling** to achieve **85%+ confidence** on correct predictions.

Key techniques:
1. **Label Smoothing (0.1)** - Prevents overconfident predictions
2. **Temperature Scaling** - Post-training calibration on validation set
3. **Focal Loss** - Better handling of rare species
4. **Quality-weighted Sampling** - Prioritize high-quality recordings

---

## LLM Configuration

### Recommended Ollama Models

| Model | Size | Speed | Accuracy | Command |
|-------|------|-------|----------|---------|
| **qwen2.5:3b** | 2GB | Fast | Good | `ollama pull qwen2.5:3b` |
| llama3.2:3b | 2GB | Fast | Good | `ollama pull llama3.2:3b` |
| phi3:mini | 2.3GB | Fast | Good | `ollama pull phi3:mini` |
| mistral:7b | 4GB | Medium | Better | `ollama pull mistral:7b` |

### Setup Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended model
ollama pull qwen2.5:3b

# Start server (in background)
ollama serve &

# Verify
curl http://localhost:11434/api/tags
```

---

## Species Database

Currently supports **25+ common Indian species** with plans to expand to **500+**.

Access species data:
```python
from data.species_db import IndiaSpeciesDatabase

db = IndiaSpeciesDatabase()

# List all species
for species in db.get_all_species():
    print(f"{species.common_name} ({species.scientific_name})")
    print(f"  Hindi: {species.hindi_name}")
    print(f"  Call: {species.call_description}")

# Get endemic species
endemic = db.get_endemic_species()
print(f"Endemic to India: {len(endemic)} species")

# Search by habitat
forest_birds = db.search_by_habitat("forest")
```

---

## Novelty Detection

BirdSense can detect unusual sightings:

1. **Out-of-distribution audio** - Sounds that don't match known patterns
2. **Range anomalies** - Species outside their typical geographic range
3. **Seasonal anomalies** - Species appearing in unexpected seasons

When detected:
```json
{
  "novelty_alert": {
    "is_novel": true,
    "novelty_score": 0.92,
    "explanation": "Species rarely found at this location..."
  }
}
```

---

## Testing Different Audio Conditions

Run automated tests:
```bash
pytest tests/test_audio_conditions.py -v
```

Test scenarios:
- **Clear** - High-quality recording
- **Feeble** - Distant/quiet bird
- **Noisy** - Background noise
- **Multi-bird** - Multiple species
- **Brief** - Short calls (<1s)

---

## Mobile Integration

Export model for mobile:
```python
from models.audio_classifier import BirdAudioClassifier

model = BirdAudioClassifier(num_classes=100)
model.load_state_dict(torch.load("checkpoints/best.pt")["model_state_dict"])

# Export to ONNX
model.export_onnx("birdsense.onnx")
```

Use with:
- **Android**: ONNX Runtime or TFLite
- **iOS**: CoreML (convert from ONNX)
- **Edge devices**: ONNX Runtime

---

## Support

For issues or questions:
- Create GitHub issue
- Contact CSCR team
- Email: [your-email]

Happy birding! 🐦

