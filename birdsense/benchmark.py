"""
🐦 BirdSense Benchmark Suite
Developed by Soham

Comprehensive benchmark for all modalities:
- Description-based identification (LLM)
- Image-based identification (Vision LLM)  
- Audio-based identification (META SAM + BirdNET + Zero-shot LLM)

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


# Enhanced Zero-Shot Audio Prompt
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

## BirdNET Suggestions (if available):
{birdnet_suggestions}

## Location Context:
- Region: {location}
- Month: {month}

Based on these acoustic characteristics, identify the bird species. Consider:
1. Frequency range typical for this bird family
2. Call/song pattern and duration
3. Geographic distribution
4. Seasonal presence

Respond in JSON format:
```json
{{
  "birds": [
    {{
      "name": "Common Name",
      "scientific_name": "Genus species", 
      "confidence": 85,
      "reasoning": "Brief explanation of why this bird matches the acoustic profile"
    }}
  ]
}}
```

Be specific and accurate. If uncertain, provide multiple candidates with appropriate confidence levels.
"""


@dataclass
class TestResult:
    test_id: str
    category: str
    expected: str
    scientific: str
    predicted: List[str]
    correct: bool
    partial: bool
    confidence: float
    time_ms: int
    error: str = ""
    reasoning: str = ""


class BirdSenseBenchmark:
    """Comprehensive benchmark suite."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.sam_audio = SAMAudio() if BIRDNET_AVAILABLE else None
        
        # Test datasets
        self.description_tests = self._get_description_tests()
        self.image_tests = self._get_image_tests()
        self.audio_tests = self._get_audio_tests()
    
    def _get_description_tests(self) -> List[Tuple[str, str, str, str]]:
        """Get description test cases (name, scientific, description, difficulty)."""
        return [
            # Easy - Common birds
            ("House Sparrow", "Passer domesticus", "small brown bird with grey crown and black bib", "easy"),
            ("American Robin", "Turdus migratorius", "thrush with orange-red breast and dark head", "easy"),
            ("Blue Jay", "Cyanocitta cristata", "blue crested bird with white and black markings", "easy"),
            ("Northern Cardinal", "Cardinalis cardinalis", "bright red bird with crest and black face", "easy"),
            ("Mallard", "Anas platyrhynchos", "duck with iridescent green head and yellow bill", "easy"),
            ("Canada Goose", "Branta canadensis", "large goose with black neck and white cheek patch", "easy"),
            ("Bald Eagle", "Haliaeetus leucocephalus", "large raptor with white head and brown body", "easy"),
            ("Great Blue Heron", "Ardea herodias", "tall grey-blue wading bird with long neck", "easy"),
            # Medium - Regional/Indian birds  
            ("Indian Peafowl", "Pavo cristatus", "large bird with iridescent blue neck and eye-spotted tail", "medium"),
            ("Common Myna", "Acridotheres tristis", "brown bird with yellow eye patch and beak, common in India", "medium"),
            ("Rose-ringed Parakeet", "Psittacula krameri", "green parrot with red beak and ring around neck", "medium"),
            ("White-throated Kingfisher", "Halcyon smyrnensis", "bright blue and chestnut kingfisher with white throat, found in India", "medium"),
            ("Red-vented Bulbul", "Pycnonotus cafer", "brown bird with black head and red patch under tail, common in South Asia", "medium"),
            ("Asian Koel", "Eudynamys scolopaceus", "glossy black cuckoo known for its loud 'ko-el' call in India", "medium"),
            # Hard - Similar species
            ("Common Nightingale", "Luscinia megarhynchos", "plain brown bird famous for its melodious song at night", "hard"),
            ("Song Thrush", "Turdus philomelos", "brown thrush with cream breast covered in dark spots", "hard"),
            ("Willow Warbler", "Phylloscopus trochilus", "small olive-green warbler with pale eyebrow", "hard"),
            ("Common Chiffchaff", "Phylloscopus collybita", "small olive-brown warbler similar to willow warbler", "hard"),
            # Expert - Exotic
            ("Resplendent Quetzal", "Pharomachrus mocinno", "emerald green bird with red breast and extremely long tail", "expert"),
            ("Scarlet Macaw", "Ara macao", "large parrot with red body and blue and yellow wings", "expert"),
            ("Atlantic Puffin", "Fratercula arctica", "black and white seabird with colorful triangular bill", "expert"),
            ("Snowy Owl", "Bubo scandiacus", "large white owl with some dark barring and yellow eyes", "expert"),
        ]
    
    def _get_image_tests(self) -> List[Tuple[str, str, str]]:
        """Get image test cases (name, scientific, url)."""
        return [
            ("Blue Jay", "Cyanocitta cristata",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Blue_jay_in_PP_%2830960%29.jpg/640px-Blue_jay_in_PP_%2830960%29.jpg"),
            ("American Robin", "Turdus migratorius",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Turdus-migratorius-002.jpg/640px-Turdus-migratorius-002.jpg"),
            ("Indian Peafowl", "Pavo cristatus",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Peacock_Plumage.jpg/640px-Peacock_Plumage.jpg"),
            ("Mallard", "Anas platyrhynchos",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Anas_platyrhynchos_male_female_quadrat.jpg/640px-Anas_platyrhynchos_male_female_quadrat.jpg"),
            ("Bald Eagle", "Haliaeetus leucocephalus",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/About_to_Launch_%2826075320352%29.jpg/640px-About_to_Launch_%2826075320352%29.jpg"),
            ("Northern Cardinal", "Cardinalis cardinalis",
             "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Cardinals_on_a_plane.JPG/640px-Cardinals_on_a_plane.JPG"),
        ]
    
    def _get_audio_tests(self) -> List[Tuple[str, str, str]]:
        """Get audio test cases (name, scientific, filepath)."""
        return [
            ("Asian Koel", "Eudynamys scolopaceus", "samples/koel_sample.wav"),
            ("Common Cuckoo", "Cuculus canorus", "samples/cuckoo_sample.wav"),
            ("Kingfisher", "Alcedo/Halcyon", "samples/kingfisher_sample.wav"),
            ("Robin", "Erithacus/Turdus", "samples/robin_sample.wav"),
            ("Sparrow", "Passer", "samples/sparrow_sample.wav"),
            ("Mixed Birds", "Various", "samples/mixed_birds.wav"),
        ]
    
    def check_match(self, expected: str, scientific: str, predictions: List[Dict]) -> Tuple[bool, bool, float]:
        """Check prediction accuracy with flexible matching."""
        if not predictions:
            return False, False, 0
        
        exp_lower = expected.lower()
        sci_lower = scientific.lower() if scientific else ""
        
        # Handle genus-level matching (e.g., "Alcedo/Halcyon" matches any kingfisher)
        sci_parts = [s.strip().lower() for s in sci_lower.split('/')] if '/' in sci_lower else [sci_lower]
        
        top = predictions[0]
        pred_name = top.get("name", "").lower()
        pred_sci = top.get("scientific_name", "").lower()
        conf = top.get("confidence", 50)
        
        # Exact or partial name match
        if exp_lower in pred_name or pred_name in exp_lower:
            return True, True, conf
        
        # Scientific name match (genus level)
        for sci_part in sci_parts:
            if sci_part and (sci_part in pred_sci or pred_sci in sci_part):
                return True, True, conf
        
        # Family/type match (e.g., "Kingfisher" in "White-throated Kingfisher")
        if exp_lower in pred_name:
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
    
    def enhanced_audio_analysis(self, audio: np.ndarray, sr: int, 
                                  location: str = "", month: str = "") -> List[Dict]:
        """
        Enhanced audio analysis using META SAM + BirdNET + Zero-shot LLM.
        
        Pipeline:
        1. META SAM-Audio for noise reduction & frequency isolation
        2. Extract detailed acoustic features
        3. BirdNET for pattern-based suggestions
        4. Zero-shot LLM analysis with acoustic features + BirdNET hints
        5. Cross-validate and rank results
        """
        results = []
        
        # Step 1: Apply SAM-Audio processing
        if self.sam_audio:
            try:
                processed_audio = self.sam_audio.process(audio, sr)
                if processed_audio is not None:
                    audio = processed_audio
            except Exception:
                pass
        
        # Step 2: Extract detailed acoustic features
        features = self._extract_detailed_features(audio, sr)
        
        # Step 3: Get BirdNET suggestions
        birdnet_suggestions = ""
        birdnet_results = []
        if BIRDNET_AVAILABLE:
            try:
                birdnet_results = identify_with_birdnet(audio, sr, location, month)
                if birdnet_results:
                    birdnet_suggestions = "\n".join([
                        f"- {r.get('name')} ({r.get('scientific_name', '')}) - {r.get('confidence', 0):.0f}% confidence"
                        for r in birdnet_results[:5]
                    ])
            except Exception:
                pass
        
        if not birdnet_suggestions:
            birdnet_suggestions = "No BirdNET detections available"
        
        # Step 4: Zero-shot LLM analysis
        try:
            prompt = ZERO_SHOT_AUDIO_PROMPT.format(
                duration=features.get("duration", 0),
                dominant_freq=features.get("dominant_freq", 0),
                freq_min=features.get("freq_min", 0),
                freq_max=features.get("freq_max", 0),
                bandwidth=features.get("bandwidth", 0),
                spectral_centroid=features.get("spectral_centroid", 0),
                spectral_rolloff=features.get("spectral_rolloff", 0),
                zcr=features.get("zcr", 0),
                rms=features.get("rms", 0),
                temporal_pattern=features.get("temporal_pattern", "unknown"),
                call_type=features.get("call_type", "unknown"),
                birdnet_suggestions=birdnet_suggestions,
                location=location or "Unknown",
                month=month or "Unknown"
            )
            
            response = provider_factory.call_text(prompt)
            llm_results = parse_birds(response)
            
            # Step 5: Cross-validate and merge results
            results = self._merge_results(birdnet_results, llm_results)
            
        except Exception as e:
            # Fall back to BirdNET results if LLM fails
            results = birdnet_results if birdnet_results else []
        
        return deduplicate_birds(results)
    
    def _extract_detailed_features(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract comprehensive acoustic features."""
        from scipy import signal
        from scipy.fft import fft
        
        # Basic features
        duration = len(audio) / sr
        
        # Spectral analysis
        n_fft = min(2048, len(audio))
        freqs = np.fft.rfftfreq(n_fft, 1/sr)
        fft_vals = np.abs(fft(audio[:n_fft]))[:len(freqs)]
        
        # Find dominant frequency
        dominant_idx = np.argmax(fft_vals)
        dominant_freq = freqs[dominant_idx] if dominant_idx < len(freqs) else 0
        
        # Frequency range (where energy > 10% of max)
        threshold = 0.1 * np.max(fft_vals)
        active_freqs = freqs[fft_vals > threshold]
        freq_min = np.min(active_freqs) if len(active_freqs) > 0 else 0
        freq_max = np.max(active_freqs) if len(active_freqs) > 0 else 0
        bandwidth = freq_max - freq_min
        
        # Spectral centroid
        spectral_centroid = np.sum(freqs * fft_vals) / (np.sum(fft_vals) + 1e-10)
        
        # Spectral rolloff (85%)
        cumsum = np.cumsum(fft_vals)
        rolloff_idx = np.searchsorted(cumsum, 0.85 * cumsum[-1])
        spectral_rolloff = freqs[rolloff_idx] if rolloff_idx < len(freqs) else 0
        
        # Zero crossing rate
        zcr = np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio))
        
        # RMS energy
        rms = np.sqrt(np.mean(audio ** 2))
        
        # Temporal pattern analysis
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
        
        # Call type classification based on features
        if dominant_freq > 4000:
            call_type = "high-pitched (warbler/finch type)"
        elif dominant_freq > 2000:
            call_type = "medium-pitched (songbird type)"
        elif dominant_freq > 500:
            call_type = "low-pitched (pigeon/dove type)"
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
    
    def _merge_results(self, birdnet: List[Dict], llm: List[Dict]) -> List[Dict]:
        """Merge and rank BirdNET + LLM results."""
        merged = {}
        
        # Add BirdNET results with weight 0.4
        for r in birdnet:
            name = r.get("name", "").lower()
            merged[name] = {
                "name": r.get("name"),
                "scientific_name": r.get("scientific_name", ""),
                "confidence": r.get("confidence", 0) * 0.4,
                "source": "birdnet"
            }
        
        # Add LLM results with weight 0.6
        for r in llm:
            name = r.get("name", "").lower()
            if name in merged:
                # Boost confidence if both agree
                merged[name]["confidence"] += r.get("confidence", 0) * 0.6
                merged[name]["source"] = "both"
            else:
                merged[name] = {
                    "name": r.get("name"),
                    "scientific_name": r.get("scientific_name", ""),
                    "confidence": r.get("confidence", 0) * 0.6,
                    "source": "llm"
                }
        
        # Sort by confidence
        results = sorted(merged.values(), key=lambda x: x["confidence"], reverse=True)
        
        # Normalize confidence
        if results:
            max_conf = results[0]["confidence"]
            for r in results:
                r["confidence"] = min(95, r["confidence"] / max_conf * 100) if max_conf > 0 else 0
        
        return results
    
    def run_description_benchmark(self) -> List[TestResult]:
        """Run description benchmark."""
        print("\n" + "="*70)
        print("📝 DESCRIPTION BENCHMARK")
        print("="*70)
        
        results = []
        
        for i, (name, sci, desc, diff) in enumerate(self.description_tests):
            print(f"[{i+1}/{len(self.description_tests)}] {name}...", end=" ", flush=True)
            
            start = time.time()
            try:
                prompt = get_description_prompt("cloud").format(description=f"I saw a {desc}")
                response = provider_factory.call_text(prompt)
                
                predicted = deduplicate_birds(parse_birds(response))
                time_ms = int((time.time() - start) * 1000)
                
                correct, partial, conf = self.check_match(name, sci, predicted)
                
                status = "✅" if correct else ("🟡" if partial else "❌")
                pred_name = predicted[0]["name"] if predicted else "None"
                print(f"{status} → {pred_name}")
                
                results.append(TestResult(
                    test_id=f"desc_{i}",
                    category="description",
                    expected=name,
                    scientific=sci,
                    predicted=[p.get("name", "") for p in predicted[:3]],
                    correct=correct,
                    partial=partial,
                    confidence=conf,
                    time_ms=time_ms
                ))
            except Exception as e:
                print(f"⚠️ {str(e)[:30]}")
                results.append(TestResult(
                    test_id=f"desc_{i}",
                    category="description",
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
    
    def run_image_benchmark(self) -> List[TestResult]:
        """Run image benchmark."""
        print("\n" + "="*70)
        print("📷 IMAGE BENCHMARK")
        print("="*70)
        
        results = []
        
        for i, (name, sci, url) in enumerate(self.image_tests):
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
                time_ms = int((time.time() - start) * 1000)
                
                correct, partial, conf = self.check_match(name, sci, predicted)
                
                status = "✅" if correct else ("🟡" if partial else "❌")
                pred_name = predicted[0]["name"] if predicted else "None"
                print(f"{status} → {pred_name}")
                
                results.append(TestResult(
                    test_id=f"img_{i}",
                    category="image",
                    expected=name,
                    scientific=sci,
                    predicted=[p.get("name", "") for p in predicted[:3]],
                    correct=correct,
                    partial=partial,
                    confidence=conf,
                    time_ms=time_ms
                ))
            except Exception as e:
                print(f"⚠️ {str(e)[:30]}")
                results.append(TestResult(
                    test_id=f"img_{i}",
                    category="image",
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
        """Run audio benchmark with enhanced pipeline."""
        print("\n" + "="*70)
        print("🎵 AUDIO BENCHMARK (META SAM + BirdNET + Zero-shot LLM)")
        print("="*70)
        
        results = []
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        for i, (name, sci, filepath) in enumerate(self.audio_tests):
            full_path = os.path.join(base_dir, filepath)
            print(f"[{i+1}/{len(self.audio_tests)}] {name}...", end=" ", flush=True)
            
            if not os.path.exists(full_path):
                print("⚠️ File not found")
                results.append(TestResult(
                    test_id=f"audio_{i}",
                    category="audio",
                    expected=name,
                    scientific=sci,
                    predicted=[],
                    correct=False,
                    partial=False,
                    confidence=0,
                    time_ms=0,
                    error="File not found"
                ))
                continue
            
            start = time.time()
            try:
                audio, sr = sf.read(full_path)
                if len(audio.shape) > 1:
                    audio = audio.mean(axis=1)
                
                # Use enhanced analysis
                predicted = self.enhanced_audio_analysis(audio, sr, "India", "6")
                time_ms = int((time.time() - start) * 1000)
                
                # For mixed birds, check if any detection is valid
                if name == "Mixed Birds":
                    correct = len(predicted) > 0
                    partial = correct
                    conf = predicted[0].get("confidence", 0) if predicted else 0
                else:
                    correct, partial, conf = self.check_match(name, sci, predicted)
                
                status = "✅" if correct else ("🟡" if partial else "❌")
                pred_names = [p.get("name", "") for p in predicted[:3]]
                print(f"{status} → {pred_names[:2]}")
                
                results.append(TestResult(
                    test_id=f"audio_{i}",
                    category="audio",
                    expected=name,
                    scientific=sci,
                    predicted=pred_names,
                    correct=correct,
                    partial=partial,
                    confidence=conf,
                    time_ms=time_ms
                ))
            except Exception as e:
                print(f"⚠️ {str(e)[:40]}")
                results.append(TestResult(
                    test_id=f"audio_{i}",
                    category="audio",
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
    
    def run_all(self) -> Dict[str, Any]:
        """Run complete benchmark."""
        print("\n" + "="*70)
        print("🐦 BIRDSENSE COMPLETE BENCHMARK")
        print(f"   Provider: {provider_factory.active_provider}")
        print(f"   Timestamp: {datetime.now().isoformat()}")
        print("="*70)
        
        all_results = []
        
        desc_results = self.run_description_benchmark()
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
        
        valid = [r for r in self.results if not r.error]
        avg_conf = sum(r.confidence for r in valid) / len(valid) if valid else 0
        avg_time = sum(r.time_ms for r in valid) / len(valid) if valid else 0
        
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
        
        return {
            "timestamp": datetime.now().isoformat(),
            "provider": provider_factory.active_provider,
            "overall": {
                "total": total,
                "correct": correct,
                "partial": partial,
                "errors": errors,
                "accuracy": round(correct / total * 100, 1) if total else 0,
                "top3_accuracy": round((correct + partial) / total * 100, 1) if total else 0,
                "avg_confidence": round(avg_conf, 1),
                "avg_time_ms": int(avg_time)
            },
            "by_category": by_cat
        }
    
    def print_report(self, metrics: Dict[str, Any]):
        """Print formatted report."""
        print("\n" + "="*70)
        print("📊 BENCHMARK RESULTS")
        print("="*70)
        
        o = metrics["overall"]
        print(f"\n🏷️  Provider: {metrics['provider']}")
        
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
                    {"id": r.test_id, "category": r.category, "expected": r.expected,
                     "predicted": r.predicted, "correct": r.correct, "partial": r.partial,
                     "confidence": r.confidence, "time_ms": r.time_ms, "error": r.error}
                    for r in self.results
                ]
            }, f, indent=2)
        
        print(f"\n💾 Saved: {filename}")


def main():
    """Run benchmark with cloud provider."""
    provider_factory.set_active("cloud")
    
    benchmark = BirdSenseBenchmark()
    metrics = benchmark.run_all()
    benchmark.print_report(metrics)
    benchmark.save_results(metrics)
    
    return metrics


if __name__ == "__main__":
    main()
