---
title: BirdSense Pro - AI Bird Identification
emoji: 🐦
colorFrom: green
colorTo: green
sdk: gradio
sdk_version: 5.9.1
app_file: app.py
pinned: true
license: mit
python_version: "3.11"
tags:
  - bird-identification
  - bioacoustics
  - audio-classification
  - image-classification
  - india-birds
  - ornithology
  - wildlife
  - conservation
---

# 🐦 BirdSense Pro

**Multi-Modal Bird Identification for India**

META SAM-Audio Preprocessing | Ollama LLM | 10,000+ Species | CSCR Initiative

## 🎯 Features

### 🎤 Audio Identification (with META SAM-Audio)
- **SAM-Audio style preprocessing** isolates bird calls from noise
- Text prompts: "bird call", "bird song" for source separation
- Frequency isolation: 500-10000 Hz bird vocalization range
- Multi-bird detection via frequency band analysis

### 📷 Image Identification  
- Color-based bird matching
- Pattern recognition
- Works with camera capture or uploads

### 📝 Description-Based
- Natural language bird identification
- Describe colors, calls, behavior
- Semantic matching via LLM

## 🔬 Technical Details

### META SAM-Audio Integration
```
Raw Audio → SAM-Audio Preprocessing → Feature Extraction → LLM Identification
                    ↓
         Text Prompt: "bird call, bird song"
         Frequency: 500-10000 Hz
         Noise Reduction: Spectral gating
```

### LLM Backend
- **Local**: Ollama with qwen2.5:3b
- **Cloud**: HuggingFace Inference API (fallback)

## 🇮🇳 CSCR Initiative

Part of the **Citizen Science for Conservation Research** initiative for open-source bird identification tools.

---

Made with ❤️ for Bird Researchers | CSCR Initiative
