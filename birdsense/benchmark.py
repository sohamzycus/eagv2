"""
🐦 BirdSense Comprehensive Benchmark Suite
Developed by Soham

200+ test cases with India/South Asia focus:
- 60% India & South Asia birds
- 25% Common global birds  
- 15% Rare/exotic birds

Features:
- Description-based identification (LLM)
- Image-based identification (Vision LLM)
- Audio-based identification (META SAM + BirdNET + Zero-shot LLM)
- Web search enhancement for accuracy
- Rarity detection for research

Target: 90%+ accuracy across all modalities
"""

import json
import time
import random
import requests
import numpy as np
import soundfile as sf
import os
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from PIL import Image
import io
import warnings
warnings.filterwarnings('ignore')

from providers import provider_factory
from analysis import (
    parse_birds, deduplicate_birds, identify_with_birdnet,
    extract_audio_features, SAMAudio, BIRDNET_AVAILABLE
)
from prompts import get_description_prompt, get_image_prompt
from bird_dataset import get_full_dataset, get_india_focused_dataset, BirdEntry
from research_tools import enhance_with_search, check_for_rare_sighting, knowledge_search


# Zero-Shot Audio Prompt with Web Search Enhancement
ZERO_SHOT_AUDIO_PROMPT = """You are an expert ornithologist specializing in bird vocalizations.

Analyze these acoustic features from a bird recording and identify the bird species:

## Acoustic Analysis:
- **Duration**: {duration:.2f} seconds
- **Dominant Frequency**: {dominant_freq:.0f} Hz
- **Frequency Range**: {freq_min:.0f} - {freq_max:.0f} Hz  
- **Frequency Bandwidth**: {bandwidth:.0f} Hz
- **Spectral Centroid**: {spectral_centroid:.0f} Hz
- **Spectral Rolloff**: {spectral_rolloff:.0f} Hz
- **Zero Crossing Rate**: {zcr:.4f}
- **RMS Energy**: {rms:.4f}
- **Temporal Pattern**: {temporal_pattern}
- **Call Type**: {call_type}

## BirdNET Suggestions:
{birdnet_suggestions}

## Location Context:
- Region: {location}
- Month: {month}

## Additional Knowledge:
Consider birds found in {location}. Use your knowledge of:
- Seasonal presence and migration patterns
- Typical vocalizations for the region
- Similar-sounding species and how to differentiate

Respond in JSON format:
```json
{{
  "birds": [
    {{
      "name": "Common Name",
      "scientific_name": "Genus species", 
      "confidence": 85,
      "reasoning": "Brief explanation matching acoustic profile to this species"
    }}
  ]
}}
```

Prioritize accuracy over certainty. List multiple candidates if unsure.
"""


@dataclass
class TestResult:
    test_id: str
    category: str  # description, image, audio
    difficulty: str  # common, uncommon, rare, vagrant
    expected: str
    scientific: str
    predicted: List[str]
    correct: bool
    partial: bool
    confidence: float
    time_ms: int
    search_enhanced: bool = False
    rarity_flagged: bool = False
    error: str = ""


class BirdSenseBenchmark:
    """Comprehensive benchmark suite with 200+ test cases."""
    
    def __init__(self, use_search_enhancement: bool = True):
        self.results: List[TestResult] = []
        self.sam_audio = SAMAudio() if BIRDNET_AVAILABLE else None
        self.use_search = use_search_enhancement
        
        # Load full dataset
        self.full_dataset = get_full_dataset()
        self.india_dataset = get_india_focused_dataset()
        
        # Build test sets
        self.description_tests = self._build_description_tests()
        self.image_tests = self._build_image_tests()
        self.audio_tests = self._build_audio_tests()
        
        print(f"📊 Benchmark initialized:")
        print(f"   Description tests: {len(self.description_tests)}")
        print(f"   Image tests: {len(self.image_tests)}")
        print(f"   Audio tests: {len(self.audio_tests)}")
        print(f"   Total: {len(self.description_tests) + len(self.image_tests) + len(self.audio_tests)}")
    
    def _build_description_tests(self) -> List[Tuple]:
        """Build 150+ description tests from dataset."""
        tests = []
        
        for bird in self.full_dataset:
            tests.append((
                bird.name,
                bird.scientific_name,
                bird.description,
                bird.rarity_in_india,
                bird.native_regions
            ))
        
        return tests
    
    def _build_image_tests(self) -> List[Tuple]:
        """Build image tests with Wikipedia/iNaturalist URLs."""
        # Curated list of reliable image URLs
        return [
            # India Common Birds
            ("Indian Peafowl", "Pavo cristatus",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Peacock_Plumage.jpg/640px-Peacock_Plumage.jpg", "common"),
            ("House Sparrow", "Passer domesticus",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/Passer_domesticus_male_%2815%29.jpg/640px-Passer_domesticus_male_%2815%29.jpg", "common"),
            ("Common Myna", "Acridotheres tristis",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Common_Myna_-_Thailand.jpg/640px-Common_Myna_-_Thailand.jpg", "common"),
            ("Rose-ringed Parakeet", "Psittacula krameri",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Psittacula_krameri_male_-_Sirao_-_Cebu_-_Philippines.jpg/640px-Psittacula_krameri_male_-_Sirao_-_Cebu_-_Philippines.jpg", "common"),
            ("Indian Roller", "Coracias benghalensis",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Indian_roller_%28Coracias_benghalensis%29_Photograph_by_Shantanu_Kuveskar.jpg/640px-Indian_roller_%28Coracias_benghalensis%29_Photograph_by_Shantanu_Kuveskar.jpg", "common"),
            ("Green Bee-eater", "Merops orientalis",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Green_bee-eater_%28Merops_orientalis%29_Photograph_by_Shantanu_Kuveskar.jpg/640px-Green_bee-eater_%28Merops_orientalis%29_Photograph_by_Shantanu_Kuveskar.jpg", "common"),
            ("White-throated Kingfisher", "Halcyon smyrnensis",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/White-throated_kingfisher_%28Halcyon_smyrnensis_smyrnensis%29.jpg/640px-White-throated_kingfisher_%28Halcyon_smyrnensis_smyrnensis%29.jpg", "common"),
            ("Red-vented Bulbul", "Pycnonotus cafer",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Red-vented_Bulbul_%28Pycnonotus_cafer%29_calling_W_IMG_4456.jpg/640px-Red-vented_Bulbul_%28Pycnonotus_cafer%29_calling_W_IMG_4456.jpg", "common"),
            ("Oriental Magpie-Robin", "Copsychus saularis",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Oriental_Magpie_Robin_%28Copsychus_saularis%29-_Male_at_Kolkata_I_IMG_3003.jpg/640px-Oriental_Magpie_Robin_%28Copsychus_saularis%29-_Male_at_Kolkata_I_IMG_3003.jpg", "common"),
            ("Black Drongo", "Dicrurus macrocercus",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Black_drongo_%28Dicrurus_macrocercus%29_feeding_IMG_7629.jpg/640px-Black_drongo_%28Dicrurus_macrocercus%29_feeding_IMG_7629.jpg", "common"),
            
            # Global Birds
            ("Blue Jay", "Cyanocitta cristata",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Blue_jay_in_PP_%2830960%29.jpg/640px-Blue_jay_in_PP_%2830960%29.jpg", "not_native"),
            ("American Robin", "Turdus migratorius",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Turdus-migratorius-002.jpg/640px-Turdus-migratorius-002.jpg", "not_native"),
            ("Mallard", "Anas platyrhynchos",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Anas_platyrhynchos_male_female_quadrat.jpg/640px-Anas_platyrhynchos_male_female_quadrat.jpg", "common"),
            ("Greater Flamingo", "Phoenicopterus roseus",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Flamingos_Laguna_Colorada.jpg/640px-Flamingos_Laguna_Colorada.jpg", "common"),
            ("Eurasian Hoopoe", "Upupa epops",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Upupa_epops_-_Netherlands.jpg/640px-Upupa_epops_-_Netherlands.jpg", "common"),
            
            # Raptors
            ("Black Kite", "Milvus migrans",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Black_Kite_I_IMG_3585.jpg/640px-Black_Kite_I_IMG_3585.jpg", "common"),
            ("Brahminy Kite", "Haliastur indus",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Brahminy_kite_%28Haliastur_indus%29_Photograph_by_Shantanu_Kuveskar.jpg/640px-Brahminy_kite_%28Haliastur_indus%29_Photograph_by_Shantanu_Kuveskar.jpg", "common"),
            ("Spotted Owlet", "Athene brama",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ee/Spotted_owlet_%28Athene_brama%29_Photograph_By_Shantanu_Kuveskar.jpg/640px-Spotted_owlet_%28Athene_brama%29_Photograph_By_Shantanu_Kuveskar.jpg", "common"),
            
            # Waterbirds
            ("Indian Pond Heron", "Ardeola grayii",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Indian_Pond_Heron_%28Ardeola_grayii%29-_Breeding_in_Hyderabad%2C_AP_W_IMG_7603.jpg/640px-Indian_Pond_Heron_%28Ardeola_grayii%29-_Breeding_in_Hyderabad%2C_AP_W_IMG_7603.jpg", "common"),
            ("Painted Stork", "Mycteria leucocephala",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/3/35/Painted_Stork_%28Mycteria_leucocephala%29_in_Uppalapadu%2C_AP_W_IMG_5069.jpg/640px-Painted_Stork_%28Mycteria_leucocephala%29_in_Uppalapadu%2C_AP_W_IMG_5069.jpg", "common"),
        ]
    
    def _build_audio_tests(self) -> List[Tuple]:
        """Build audio tests with synthesized samples based on frequency profiles."""
        # Generate tests based on dataset audio characteristics
        tests = []
        
        # Select diverse birds with known audio characteristics
        audio_birds = [
            ("Asian Koel", "Eudynamys scolopaceus", (700, 1500), "rising"),
            ("Common Cuckoo", "Cuculus canorus", (600, 800), "two-note"),
            ("Greater Coucal", "Centropus sinensis", (200, 600), "booming"),
            ("White-throated Kingfisher", "Halcyon smyrnensis", (2000, 5000), "rattling"),
            ("Coppersmith Barbet", "Psilopogon haemacephalus", (1500, 2500), "metallic"),
            ("Indian Golden Oriole", "Oriolus kundoo", (1000, 3000), "fluting"),
            ("Black Drongo", "Dicrurus macrocercus", (1500, 4000), "mimicry"),
            ("Red-vented Bulbul", "Pycnonotus cafer", (2000, 5000), "cheerful"),
            ("Oriental Magpie-Robin", "Copsychus saularis", (1500, 6000), "melodious"),
            ("Common Tailorbird", "Orthotomus sutorius", (3000, 6000), "loud"),
            ("Purple Sunbird", "Cinnyris asiaticus", (4000, 8000), "squeaky"),
            ("Jungle Babbler", "Argya striata", (1500, 4000), "chattering"),
            ("House Crow", "Corvus splendens", (500, 2000), "cawing"),
            ("Indian Roller", "Coracias benghalensis", (1000, 3000), "harsh"),
            ("Green Bee-eater", "Merops orientalis", (3000, 5000), "trilling"),
            ("Spotted Owlet", "Athene brama", (500, 2000), "chirring"),
            ("Indian Eagle-Owl", "Bubo bengalensis", (200, 800), "hooting"),
            ("Barn Owl", "Tyto alba", (1000, 3000), "screeching"),
            ("Greater Racket-tailed Drongo", "Dicrurus paradiseus", (1000, 4000), "mimicry"),
            ("Indian Pitta", "Pitta brachyura", (800, 2000), "whistling"),
        ]
        
        for name, scientific, freq_range, pattern in audio_birds:
            tests.append((name, scientific, freq_range, pattern))
        
        return tests
    
    def check_match(self, expected: str, scientific: str, 
                    predictions: List[Dict]) -> Tuple[bool, bool, float]:
        """Check prediction accuracy with flexible matching."""
        if not predictions:
            return False, False, 0
        
        exp_lower = expected.lower()
        sci_lower = scientific.lower() if scientific else ""
        sci_parts = [s.strip().lower() for s in sci_lower.split('/')] if '/' in sci_lower else [sci_lower]
        
        top = predictions[0]
        pred_name = top.get("name", "").lower()
        pred_sci = top.get("scientific_name", "").lower()
        conf = top.get("confidence", 50)
        
        # Exact match
        if exp_lower in pred_name or pred_name in exp_lower:
            return True, True, conf
        for sci_part in sci_parts:
            if sci_part and (sci_part in pred_sci or pred_sci in sci_part):
                return True, True, conf
        
        # Top-3 match
        for p in predictions[:3]:
            pn = p.get("name", "").lower()
            ps = p.get("scientific_name", "").lower()
            if exp_lower in pn or pn in exp_lower:
                return False, True, p.get("confidence", 50)
            for sci_part in sci_parts:
                if sci_part and (sci_part in ps or ps in sci_part):
                    return False, True, p.get("confidence", 50)
        
        return False, False, conf
    
    def run_description_benchmark(self, max_tests: int = 150) -> List[TestResult]:
        """Run description benchmark on 150+ tests."""
        print("\n" + "="*70)
        print(f"📝 DESCRIPTION BENCHMARK ({min(max_tests, len(self.description_tests))} tests)")
        print("="*70)
        
        results = []
        tests = self.description_tests[:max_tests]
        
        for i, (name, sci, desc, rarity, regions) in enumerate(tests):
            print(f"[{i+1}/{len(tests)}] {name}...", end=" ", flush=True)
            
            start = time.time()
            try:
                # Build description with context
                full_desc = f"I saw a {desc}"
                if "India" in regions:
                    full_desc += " in India"
                
                prompt = get_description_prompt("cloud").format(description=full_desc)
                response = provider_factory.call_text(prompt)
                
                predicted = deduplicate_birds(parse_birds(response))
                
                # Enhance with search if enabled
                if self.use_search and predicted:
                    predicted = enhance_with_search(predicted, location="India")
                
                time_ms = int((time.time() - start) * 1000)
                
                correct, partial, conf = self.check_match(name, sci, predicted)
                
                # Check for rarity
                rarity_result = check_for_rare_sighting(name, "India") if predicted else {"is_rare": False}
                
                status = "✅" if correct else ("🟡" if partial else "❌")
                pred_name = predicted[0]["name"] if predicted else "None"
                rare_flag = " 🔬" if rarity_result.get("is_rare") else ""
                print(f"{status} → {pred_name}{rare_flag}")
                
                results.append(TestResult(
                    test_id=f"desc_{i}",
                    category="description",
                    difficulty=rarity,
                    expected=name,
                    scientific=sci,
                    predicted=[p.get("name", "") for p in predicted[:3]],
                    correct=correct,
                    partial=partial,
                    confidence=conf,
                    time_ms=time_ms,
                    search_enhanced=self.use_search,
                    rarity_flagged=rarity_result.get("is_rare", False)
                ))
            except Exception as e:
                print(f"⚠️ {str(e)[:30]}")
                results.append(TestResult(
                    test_id=f"desc_{i}",
                    category="description",
                    difficulty=rarity,
                    expected=name,
                    scientific=sci,
                    predicted=[],
                    correct=False,
                    partial=False,
                    confidence=0,
                    time_ms=0,
                    error=str(e)
                ))
            
            time.sleep(0.2)
        
        return results
    
    def run_image_benchmark(self) -> List[TestResult]:
        """Run image benchmark."""
        print("\n" + "="*70)
        print(f"📷 IMAGE BENCHMARK ({len(self.image_tests)} tests)")
        print("="*70)
        
        results = []
        
        for i, (name, sci, url, rarity) in enumerate(self.image_tests):
            print(f"[{i+1}/{len(self.image_tests)}] {name}...", end=" ", flush=True)
            
            start = time.time()
            try:
                headers = {"User-Agent": "BirdSense/1.0"}
                resp = requests.get(url, headers=headers, timeout=15, verify=False)
                
                if resp.status_code != 200:
                    raise Exception(f"HTTP {resp.status_code}")
                
                image = Image.open(io.BytesIO(resp.content)).convert("RGB")
                
                prompt = get_image_prompt("cloud")
                response = provider_factory.call_vision(image, prompt)
                
                predicted = deduplicate_birds(parse_birds(response))
                
                if self.use_search and predicted:
                    predicted = enhance_with_search(predicted, location="India")
                
                time_ms = int((time.time() - start) * 1000)
                
                correct, partial, conf = self.check_match(name, sci, predicted)
                
                status = "✅" if correct else ("🟡" if partial else "❌")
                pred_name = predicted[0]["name"] if predicted else "None"
                print(f"{status} → {pred_name}")
                
                results.append(TestResult(
                    test_id=f"img_{i}",
                    category="image",
                    difficulty=rarity,
                    expected=name,
                    scientific=sci,
                    predicted=[p.get("name", "") for p in predicted[:3]],
                    correct=correct,
                    partial=partial,
                    confidence=conf,
                    time_ms=time_ms,
                    search_enhanced=self.use_search
                ))
            except Exception as e:
                print(f"⚠️ {str(e)[:30]}")
                results.append(TestResult(
                    test_id=f"img_{i}",
                    category="image",
                    difficulty=rarity,
                    expected=name,
                    scientific=sci,
                    predicted=[],
                    correct=False,
                    partial=False,
                    confidence=0,
                    time_ms=0,
                    error=str(e)
                ))
            
            time.sleep(0.5)
        
        return results
    
    def run_audio_benchmark(self) -> List[TestResult]:
        """Run audio benchmark with synthesized samples."""
        print("\n" + "="*70)
        print(f"🎵 AUDIO BENCHMARK ({len(self.audio_tests)} tests)")
        print("="*70)
        
        # Import SAMAudio for enhancement
        from analysis import SAMAudio
        sam = SAMAudio()
        
        results = []
        
        for i, (name, sci, freq_range, pattern) in enumerate(self.audio_tests):
            print(f"[{i+1}/{len(self.audio_tests)}] {name}...", end=" ", flush=True)
            
            start = time.time()
            try:
                # Generate synthetic audio
                audio, sr = self._generate_bird_audio(freq_range, pattern)
                
                # 🔊 CRITICAL: Apply SAM-Audio enhancement BEFORE any analysis
                enhanced_audio = sam.enhance_audio(audio, sr)
                
                # Extract features from ENHANCED audio
                features = self._extract_features(enhanced_audio, sr)
                
                # Run BirdNET on ENHANCED audio
                birdnet_suggestions = ""
                birdnet_results = []
                if BIRDNET_AVAILABLE:
                    birdnet_results = identify_with_birdnet(enhanced_audio, sr, "India", "6")
                    if birdnet_results:
                        birdnet_suggestions = "\n".join([
                            f"- {r.get('name')} ({r.get('scientific_name', '')}) - {r.get('confidence', 0):.0f}%"
                            for r in birdnet_results[:5]
                        ])
                
                if not birdnet_suggestions:
                    birdnet_suggestions = "No BirdNET detections"
                
                # Zero-shot LLM analysis
                prompt = ZERO_SHOT_AUDIO_PROMPT.format(
                    duration=features["duration"],
                    dominant_freq=features["dominant_freq"],
                    freq_min=features["freq_min"],
                    freq_max=features["freq_max"],
                    bandwidth=features["bandwidth"],
                    spectral_centroid=features["spectral_centroid"],
                    spectral_rolloff=features["spectral_rolloff"],
                    zcr=features["zcr"],
                    rms=features["rms"],
                    temporal_pattern=features["temporal_pattern"],
                    call_type=features["call_type"],
                    birdnet_suggestions=birdnet_suggestions,
                    location="India",
                    month="6"
                )
                
                response = provider_factory.call_text(prompt)
                llm_results = parse_birds(response)
                
                # Merge results
                predicted = self._merge_audio_results(birdnet_results, llm_results)
                
                if self.use_search and predicted:
                    predicted = enhance_with_search(predicted, features, "India", "6")
                
                time_ms = int((time.time() - start) * 1000)
                
                correct, partial, conf = self.check_match(name, sci, predicted)
                
                status = "✅" if correct else ("🟡" if partial else "❌")
                pred_names = [p.get("name", "") for p in predicted[:2]]
                print(f"{status} → {pred_names}")
                
                results.append(TestResult(
                    test_id=f"audio_{i}",
                    category="audio",
                    difficulty="common",
                    expected=name,
                    scientific=sci,
                    predicted=[p.get("name", "") for p in predicted[:3]],
                    correct=correct,
                    partial=partial,
                    confidence=conf,
                    time_ms=time_ms,
                    search_enhanced=self.use_search
                ))
            except Exception as e:
                print(f"⚠️ {str(e)[:40]}")
                results.append(TestResult(
                    test_id=f"audio_{i}",
                    category="audio",
                    difficulty="common",
                    expected=name,
                    scientific=sci,
                    predicted=[],
                    correct=False,
                    partial=False,
                    confidence=0,
                    time_ms=0,
                    error=str(e)
                ))
            
            time.sleep(0.3)
        
        return results
    
    def _generate_bird_audio(self, freq_range: Tuple[int, int], 
                              pattern: str, duration: float = 5.0) -> Tuple[np.ndarray, int]:
        """Generate synthetic bird audio based on frequency profile."""
        sr = 44100
        t = np.linspace(0, duration, int(sr * duration))
        audio = np.zeros_like(t)
        
        f_low, f_high = freq_range
        f_center = (f_low + f_high) / 2
        
        if pattern == "rising":
            # Rising call (like Koel)
            for i in range(3):
                start = i * 1.5
                call_t = np.linspace(0, 1.2, int(sr * 1.2))
                freq = f_low + (f_high - f_low) * (call_t / 1.2)
                call = 0.6 * np.sin(2 * np.pi * np.cumsum(freq) / sr)
                env = np.exp(-2 * ((call_t - 0.6) / 0.4)**2)
                call = call * env
                idx = int(start * sr)
                end_idx = min(idx + len(call), len(audio))
                audio[idx:end_idx] += call[:end_idx-idx]
        
        elif pattern == "two-note":
            # Two-note call (like Cuckoo)
            for i in range(4):
                start = i * 1.2
                for note in range(2):
                    note_start = start + note * 0.4
                    note_t = np.linspace(0, 0.3, int(sr * 0.3))
                    freq = f_high if note == 0 else f_low
                    call = 0.5 * np.sin(2 * np.pi * freq * note_t)
                    env = np.sin(np.pi * note_t / 0.3)
                    call = call * env
                    idx = int(note_start * sr)
                    end_idx = min(idx + len(call), len(audio))
                    audio[idx:end_idx] += call[:end_idx-idx]
        
        elif pattern == "booming":
            # Deep booming (like Coucal)
            for i in range(3):
                start = i * 1.5
                boom_t = np.linspace(0, 0.8, int(sr * 0.8))
                call = 0.6 * np.sin(2 * np.pi * f_center * boom_t)
                call += 0.3 * np.sin(2 * np.pi * f_center * 2 * boom_t)
                env = np.exp(-((boom_t - 0.4) / 0.3)**2)
                call = call * env
                idx = int(start * sr)
                end_idx = min(idx + len(call), len(audio))
                audio[idx:end_idx] += call[:end_idx-idx]
        
        else:
            # Generic frequency-modulated call
            for i in range(4):
                start = i * 1.0
                call_t = np.linspace(0, 0.5, int(sr * 0.5))
                freq = f_center + (f_high - f_low) / 2 * np.sin(2 * np.pi * 10 * call_t)
                call = 0.5 * np.sin(2 * np.pi * np.cumsum(freq) / sr)
                env = np.exp(-((call_t - 0.25) / 0.15)**2)
                call = call * env
                idx = int(start * sr)
                end_idx = min(idx + len(call), len(audio))
                audio[idx:end_idx] += call[:end_idx-idx]
        
        # Normalize and add noise
        audio = audio / (np.max(np.abs(audio)) + 1e-10) * 0.7
        audio += np.random.randn(len(audio)) * 0.01
        
        return audio, sr
    
    def _extract_features(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract acoustic features."""
        from scipy import signal
        from scipy.fft import fft
        
        duration = len(audio) / sr
        
        n_fft = min(2048, len(audio))
        freqs = np.fft.rfftfreq(n_fft, 1/sr)
        fft_vals = np.abs(fft(audio[:n_fft]))[:len(freqs)]
        
        dominant_idx = np.argmax(fft_vals)
        dominant_freq = freqs[dominant_idx] if dominant_idx < len(freqs) else 0
        
        threshold = 0.1 * np.max(fft_vals)
        active_freqs = freqs[fft_vals > threshold]
        freq_min = np.min(active_freqs) if len(active_freqs) > 0 else 0
        freq_max = np.max(active_freqs) if len(active_freqs) > 0 else 0
        bandwidth = freq_max - freq_min
        
        spectral_centroid = np.sum(freqs * fft_vals) / (np.sum(fft_vals) + 1e-10)
        
        cumsum = np.cumsum(fft_vals)
        rolloff_idx = np.searchsorted(cumsum, 0.85 * cumsum[-1])
        spectral_rolloff = freqs[rolloff_idx] if rolloff_idx < len(freqs) else 0
        
        zcr = np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio))
        rms = np.sqrt(np.mean(audio ** 2))
        
        envelope = np.abs(signal.hilbert(audio))
        peaks, _ = signal.find_peaks(envelope, distance=sr//10)
        
        if len(peaks) > 1:
            intervals = np.diff(peaks) / sr
            if np.std(intervals) < 0.1:
                temporal_pattern = "repetitive/rhythmic"
            elif len(peaks) > 5:
                temporal_pattern = "complex/varied"
            else:
                temporal_pattern = "simple/short"
        else:
            temporal_pattern = "single note"
        
        if dominant_freq > 4000:
            call_type = "high-pitched (warbler/sunbird type)"
        elif dominant_freq > 2000:
            call_type = "medium-pitched (songbird type)"
        elif dominant_freq > 500:
            call_type = "low-pitched (cuckoo/dove type)"
        else:
            call_type = "very low (owl/large bird type)"
        
        if bandwidth > 3000:
            call_type += ", wide frequency range (song)"
        else:
            call_type += ", narrow frequency range (call)"
        
        return {
            "duration": duration,
            "dominant_freq": dominant_freq,
            "freq_min": freq_min,
            "freq_max": freq_max,
            "bandwidth": bandwidth,
            "spectral_centroid": spectral_centroid,
            "spectral_rolloff": spectral_rolloff,
            "zcr": zcr,
            "rms": rms,
            "temporal_pattern": temporal_pattern,
            "call_type": call_type
        }
    
    def _merge_audio_results(self, birdnet: List[Dict], 
                              llm: List[Dict]) -> List[Dict]:
        """Merge BirdNET and LLM results."""
        merged = {}
        
        for r in birdnet:
            name = r.get("name", "").lower()
            merged[name] = {
                "name": r.get("name"),
                "scientific_name": r.get("scientific_name", ""),
                "confidence": r.get("confidence", 0) * 0.4,
                "source": "birdnet"
            }
        
        for r in llm:
            name = r.get("name", "").lower()
            if name in merged:
                merged[name]["confidence"] += r.get("confidence", 0) * 0.6
                merged[name]["source"] = "both"
            else:
                merged[name] = {
                    "name": r.get("name"),
                    "scientific_name": r.get("scientific_name", ""),
                    "confidence": r.get("confidence", 0) * 0.6,
                    "source": "llm"
                }
        
        results = sorted(merged.values(), key=lambda x: x["confidence"], reverse=True)
        
        if results:
            max_conf = results[0]["confidence"]
            for r in results:
                r["confidence"] = min(95, r["confidence"] / max_conf * 100) if max_conf > 0 else 0
        
        return results
    
    def run_all(self, max_description_tests: int = 150) -> Dict[str, Any]:
        """Run complete benchmark."""
        print("\n" + "="*70)
        print("🐦 BIRDSENSE COMPREHENSIVE BENCHMARK")
        print(f"   Provider: {provider_factory.active_provider}")
        print(f"   Search Enhancement: {'ON' if self.use_search else 'OFF'}")
        print(f"   Timestamp: {datetime.now().isoformat()}")
        print("="*70)
        
        all_results = []
        
        desc_results = self.run_description_benchmark(max_description_tests)
        all_results.extend(desc_results)
        
        img_results = self.run_image_benchmark()
        all_results.extend(img_results)
        
        audio_results = self.run_audio_benchmark()
        all_results.extend(audio_results)
        
        self.results = all_results
        
        return self.calculate_metrics()
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive metrics."""
        total = len(self.results)
        correct = sum(1 for r in self.results if r.correct)
        partial = sum(1 for r in self.results if r.partial and not r.correct)
        errors = sum(1 for r in self.results if r.error)
        rare_flags = sum(1 for r in self.results if r.rarity_flagged)
        
        valid = [r for r in self.results if not r.error]
        avg_conf = sum(r.confidence for r in valid) / len(valid) if valid else 0
        avg_time = sum(r.time_ms for r in valid) / len(valid) if valid else 0
        
        # By category
        by_cat = {}
        for cat in ["description", "image", "audio"]:
            cat_results = [r for r in self.results if r.category == cat]
            if cat_results:
                c_correct = sum(1 for r in cat_results if r.correct)
                c_partial = sum(1 for r in cat_results if r.partial)
                c_valid = [r for r in cat_results if not r.error]
                by_cat[cat] = {
                    "total": len(cat_results),
                    "correct": c_correct,
                    "accuracy": round(c_correct / len(cat_results) * 100, 1),
                    "top3_accuracy": round(c_partial / len(cat_results) * 100, 1),
                    "avg_time_ms": int(sum(r.time_ms for r in c_valid) / len(c_valid)) if c_valid else 0
                }
        
        # By difficulty
        by_diff = {}
        for diff in ["common", "uncommon", "rare", "vagrant", "not_native"]:
            diff_results = [r for r in self.results if r.difficulty == diff]
            if diff_results:
                d_correct = sum(1 for r in diff_results if r.correct)
                d_partial = sum(1 for r in diff_results if r.partial)
                by_diff[diff] = {
                    "total": len(diff_results),
                    "correct": d_correct,
                    "accuracy": round(d_correct / len(diff_results) * 100, 1),
                    "top3_accuracy": round(d_partial / len(diff_results) * 100, 1)
                }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "provider": provider_factory.active_provider,
            "search_enhanced": self.use_search,
            "overall": {
                "total": total,
                "correct": correct,
                "partial": partial,
                "errors": errors,
                "rare_sightings_flagged": rare_flags,
                "accuracy": round(correct / total * 100, 1) if total else 0,
                "top3_accuracy": round((correct + partial) / total * 100, 1) if total else 0,
                "avg_confidence": round(avg_conf, 1),
                "avg_time_ms": int(avg_time)
            },
            "by_category": by_cat,
            "by_difficulty": by_diff
        }
    
    def print_report(self, metrics: Dict[str, Any]):
        """Print formatted report."""
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE BENCHMARK RESULTS")
        print("="*70)
        
        o = metrics["overall"]
        print(f"\n🏷️  Provider: {metrics['provider']}")
        print(f"🔍 Search Enhancement: {'ON' if metrics['search_enhanced'] else 'OFF'}")
        print(f"🔬 Rare Sightings Flagged: {o['rare_sightings_flagged']}")
        
        print(f"\n{'─'*70}")
        print(f"{'Category':<20} {'Tests':<8} {'Top-1':<15} {'Top-3':<15} {'Time':<10}")
        print(f"{'─'*70}")
        
        for cat, m in metrics.get("by_category", {}).items():
            emoji = "📝" if cat == "description" else ("📷" if cat == "image" else "🎵")
            acc = f"{m['correct']}/{m['total']} ({m['accuracy']}%)"
            top3 = f"{m['top3_accuracy']}%"
            print(f"{emoji} {cat.capitalize():<17} {m['total']:<8} {acc:<15} {top3:<15} {m['avg_time_ms']}ms")
        
        print(f"{'─'*70}")
        acc_str = f"{o['correct']}/{o['total']} ({o['accuracy']}%)"
        top3_str = f"{o['top3_accuracy']}%"
        print(f"{'📊 TOTAL':<20} {o['total']:<8} {acc_str:<15} {top3_str:<15} {o['avg_time_ms']}ms")
        print(f"{'─'*70}")
        
        # By Difficulty
        print(f"\n{'─'*70}")
        print("BY DIFFICULTY:")
        for diff, m in metrics.get("by_difficulty", {}).items():
            emoji = "🟢" if diff == "common" else ("🟡" if diff == "uncommon" else "🔴")
            print(f"   {emoji} {diff.replace('_', ' ').capitalize()}: {m['accuracy']}% ({m['correct']}/{m['total']})")
        
        # Grade
        grades = {90: "A+", 80: "A", 70: "B", 60: "C", 50: "D"}
        grade = "F"
        for threshold, g in sorted(grades.items(), reverse=True):
            if o['accuracy'] >= threshold:
                grade = g
                break
        
        print(f"\n🏆 OVERALL GRADE: {grade}")
        print("="*70)
    
    def save_results(self, metrics: Dict[str, Any]):
        """Save results to JSON."""
        filename = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, "w") as f:
            json.dump({
                "metrics": metrics,
                "results": [
                    {"id": r.test_id, "category": r.category, "difficulty": r.difficulty,
                     "expected": r.expected, "predicted": r.predicted, 
                     "correct": r.correct, "partial": r.partial,
                     "confidence": r.confidence, "time_ms": r.time_ms, 
                     "search_enhanced": r.search_enhanced,
                     "rarity_flagged": r.rarity_flagged, "error": r.error}
                    for r in self.results
                ]
            }, f, indent=2)
        
        print(f"\n💾 Saved: {filename}")


def main():
    """Run comprehensive benchmark."""
    provider_factory.set_active("cloud")
    
    # Run with search enhancement
    benchmark = BirdSenseBenchmark(use_search_enhancement=True)
    metrics = benchmark.run_all(max_description_tests=100)  # Run 100 desc tests for speed
    benchmark.print_report(metrics)
    benchmark.save_results(metrics)
    
    return metrics


if __name__ == "__main__":
    main()
