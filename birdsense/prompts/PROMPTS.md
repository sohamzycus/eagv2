# 🐦 BirdSense Prompts Documentation

All LLM and SAM-Audio prompts used in BirdSense for bird voice separation and identification.

---

## 1. SAM-Audio Bird Voice Separation Prompts

**Location:** `audio/sam_audio.py`

### Text Prompts for Source Separation

```python
# Primary bird isolation prompts
text_prompts = [
    "bird call",           # General bird vocalization
    "bird song",           # Melodic bird sounds
    "bird vocalization",   # All bird sounds
    "background noise",    # Non-bird sounds to filter
    "wind"                 # Environmental noise
]

# For multi-bird recordings
multi_bird_prompts = [
    "bird call 1",        # First bird
    "bird call 2",        # Second bird
    "bird call 3",        # Third bird
    "background noise"    # To remove
]
```

### How SAM-Audio Works

```
┌─────────────────────────────────────────────────────────────────┐
│                   SAM-AUDIO SEPARATION PIPELINE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Input: Raw field recording                                     │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  TEXT PROMPTS TO SAM-AUDIO MODEL                        │   │
│   │                                                          │   │
│   │  "bird call" → Model creates mask for bird frequencies  │   │
│   │  "bird song" → Model isolates melodic bird sounds       │   │
│   │  "background noise" → Model identifies noise to remove  │   │
│   │                                                          │   │
│   │  Model: facebook/sam-audio-large                        │   │
│   │  Uses transformer cross-attention to match prompts      │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                         │
│        ▼                                                         │
│   Output: Isolated bird audio + Noise removed                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Spectral Fallback (When SAM-Audio unavailable)

When SAM-Audio model can't load, we use spectral separation:

```python
# Bird frequency range mask
bird_frequency_range = (500, 10000)  # Hz - covers most bird calls

# Creates bandpass filter to isolate bird frequencies
# Low frequencies (< 500 Hz): Usually wind, traffic
# High frequencies (> 10kHz): Usually insects, electronics
```

---

## 2. LLM Zero-Shot Identification Prompts

**Location:** `llm/zero_shot_identifier.py`

### System Prompt (Expert Ornithologist)

```
You are an expert ornithologist with deep knowledge of bird vocalizations worldwide.
You can identify birds by their calls based on frequency, pattern, duration, and context.

Your expertise includes:
- 10,000+ bird species globally
- Detailed knowledge of Indian birds (1,300+ species)
- Ability to distinguish similar-sounding species
- Understanding of seasonal and geographic variations

When identifying birds:
1. Consider the audio characteristics carefully
2. Match against known bird call patterns
3. Account for regional variations
4. Flag unusual or rare sightings
5. Provide confidence based on how well features match

Always respond in the exact JSON format requested.
```

### User Prompt Template

```
Identify this bird based on its call characteristics:

## Audio Features
- **Duration**: {duration} seconds
- **Dominant Frequency**: {frequency} Hz ({freq_description})
- **Frequency Range**: {low_freq} - {high_freq} Hz
- **Call Pattern**: {melodic/monotone}, {repetitive/non-repetitive}
- **Syllables**: {num_syllables} syllables at {rate}/second
- **Rhythm**: {tempo} BPM (beats per minute)
- **Amplitude**: {pattern} pattern

## Context
- **Location**: {location or "India (unspecified)"}
- **Season**: {season_description}
- **Recording Quality**: {quality_label} (SNR: {snr_db}dB)
- **Observer Notes**: {user_description}

## Task
Based on these audio features, identify the most likely bird species.

Respond in this exact JSON format:
{
    "species_name": "Common Name",
    "scientific_name": "Genus species",
    "confidence": 0.85,
    "reasoning": "Detailed explanation of why this species matches...",
    "key_features_matched": ["feature1", "feature2"],
    "alternatives": [
        {"name": "Alternative 1", "scientific": "Genus species", "confidence": 0.1},
        {"name": "Alternative 2", "scientific": "Genus species", "confidence": 0.05}
    ],
    "is_indian_bird": true,
    "is_unusual": false,
    "unusual_reason": null,
    "typical_call": "Description of what this bird typically sounds like"
}
```

### Frequency Description Mappings

| Frequency Range | Description | Typical Birds |
|-----------------|-------------|---------------|
| < 500 Hz | very low (large bird or booming call) | Bittern, large owls |
| 500-1000 Hz | low (owl, dove, or large bird) | Dove, owl, crow |
| 1000-2000 Hz | low-medium (cuckoo, crow, or medium bird) | Koel, cuckoo |
| 2000-4000 Hz | medium (most songbirds) | Robin, bulbul |
| 4000-6000 Hz | medium-high (warbler, sunbird) | Warbler, sunbird |
| 6000-8000 Hz | high (small passerine) | Tailorbird |
| > 8000 Hz | very high (insect-like or whistle) | Kingfisher alarm |

### Season Context for India

| Months | Season | Bird Activity |
|--------|--------|---------------|
| Dec-Feb | Winter | Winter migrants present |
| Mar-May | Summer/Pre-monsoon | Breeding season - most vocal |
| Jun-Sep | Monsoon | Reduced activity |
| Oct-Nov | Post-monsoon | Migration period |

---

## 3. Example LLM Conversation

### Input Features
```json
{
    "duration": 8.0,
    "dominant_frequency_hz": 2500,
    "frequency_range": [800, 5000],
    "is_melodic": true,
    "is_repetitive": true,
    "num_syllables": 27,
    "syllable_rate": 3.4,
    "location": "Western Ghats, Kerala",
    "month": 4
}
```

### LLM Response
```json
{
    "species_name": "Asian Koel",
    "scientific_name": "Eudynamys scolopaceus",
    "confidence": 0.92,
    "reasoning": "The repetitive melodic call with dominant frequency around 2500 Hz 
                  and high syllable rate is characteristic of the Asian Koel. 
                  April is breeding season when males are most vocal. 
                  Western Ghats is within the species' range.",
    "key_features_matched": [
        "Repetitive ascending whistle",
        "Mid-frequency range (2-3 kHz)",
        "Breeding season vocalization",
        "Geographic match"
    ],
    "alternatives": [
        {"name": "Indian Cuckoo", "scientific": "Cuculus micropterus", "confidence": 0.05},
        {"name": "Common Hawk-Cuckoo", "scientific": "Hierococcyx varius", "confidence": 0.03}
    ],
    "is_indian_bird": true,
    "is_unusual": false,
    "unusual_reason": null,
    "typical_call": "The Asian Koel's call is a loud, ascending 'ku-oo' repeated many times, 
                     becoming faster and more frantic during breeding season."
}
```

---

## 4. Novelty Detection Prompts

When identifying unusual sightings:

```
## Special Instructions for Novelty Detection

If the bird call characteristics don't match any common Indian species:
1. Check if it matches any globally known species
2. Set "is_indian_bird": false if non-Indian
3. Set "is_unusual": true if rare/vagrant
4. Explain in "unusual_reason" why this is noteworthy

Examples of unusual sightings:
- Kookaburra (Australian) heard in India → is_indian_bird: false
- Rare winter vagrant from Central Asia
- Species at unusual elevation or habitat
```

---

## 5. Quality-Based Confidence Adjustment

```python
# The LLM is instructed to adjust confidence based on recording quality:

if quality_score > 0.8:  # Excellent
    # Can have high confidence if features match
    confidence_adjustment = 1.0
elif quality_score > 0.6:  # Good
    # Moderate confidence ceiling
    confidence_adjustment = 0.9
elif quality_score > 0.4:  # Fair
    # Lower confidence due to noise
    confidence_adjustment = 0.7
else:  # Poor
    # Significantly reduce confidence
    confidence_adjustment = 0.5
```

---

## Summary

| Component | Prompt Type | Purpose |
|-----------|-------------|---------|
| SAM-Audio | Text prompts | Separate bird calls from noise |
| LLM System | Expert persona | Set up ornithologist knowledge |
| LLM User | Feature description | Provide audio analysis for identification |
| LLM Output | JSON format | Structured response with confidence |
| Novelty | Special instructions | Detect rare/unusual sightings |

