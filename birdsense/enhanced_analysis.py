"""
🐦 BirdSense Enhanced Analysis
Developed by Soham

Integration of all improvement techniques:
1. Enhanced prompts (CoT, Few-shot, Confusion matrix)
2. Spectrogram vision analysis
3. eBird location awareness
4. Multi-modal fusion

This module provides enhanced versions of the core analysis functions.
"""

import numpy as np
from typing import Dict, List, Optional, Generator
import json

from providers import provider_factory
from analysis import (
    parse_birds, deduplicate_birds, fetch_bird_image, format_bird_result,
    extract_audio_features, identify_with_birdnet, SAMAudio, BIRDNET_AVAILABLE
)
from enhanced_prompts import (
    build_enhanced_description_prompt,
    build_enhanced_image_prompt, 
    build_enhanced_audio_prompt,
    get_confusion_prompt,
    INDIA_REGIONAL_BIRDS
)
from ebird_integration import (
    LocationAwareBirdContext,
    get_fallback_expected_species,
    get_location_coordinates
)


class EnhancedBirdAnalyzer:
    """
    Enhanced bird identification with all improvement techniques.
    
    Improvements over base analyzer:
    1. Chain-of-thought prompting for better reasoning
    2. Few-shot examples for Indian birds
    3. Similar species confusion handling
    4. eBird location context
    5. Multi-pass verification
    6. Spectrogram vision analysis
    """
    
    def __init__(self):
        self.location_context = LocationAwareBirdContext()
        self.sam_audio = SAMAudio()
    
    # =========================================================================
    # ENHANCED DESCRIPTION IDENTIFICATION
    # =========================================================================
    
    def identify_description_enhanced(self, description: str, 
                                        location: str = "India",
                                        month: str = "January") -> Generator[str, None, None]:
        """
        Enhanced description-based identification with CoT and few-shot.
        
        Improvements:
        - Chain-of-thought reasoning
        - Few-shot Indian bird examples
        - Confusion matrix for similar species
        - eBird location context
        """
        if not description or len(description.strip()) < 5:
            yield "<p style='color:#dc2626'>⚠️ Please describe the bird</p>"
            return
        
        model_info = provider_factory.get_model_info("text")
        
        # Stage 1: Build enhanced prompt
        yield self._status("Building enhanced prompt with regional context...", 1, 4)
        
        prompt = build_enhanced_description_prompt(description, location, month)
        
        # Add eBird context if available
        ebird_context = self.location_context.build_prompt_context(location, month)
        if ebird_context:
            prompt += f"\n\n**RECENT eBIRD DATA:**\n{ebird_context}"
        
        # Stage 2: First pass identification
        yield self._status("Pass 1: Initial identification with CoT reasoning...", 2, 4)
        
        response = provider_factory.call_text(prompt)
        candidates = parse_birds(response)
        
        if not candidates:
            yield "<p style='color:#dc2626'>❌ Could not identify bird</p>"
            return
        
        # Stage 3: Check for similar species
        yield self._status("Pass 2: Similar species verification...", 3, 4)
        
        candidate_names = [c["name"] for c in candidates[:3]]
        confusion_prompt = get_confusion_prompt(candidate_names)
        
        if confusion_prompt:
            # Re-check with confusion matrix
            verify_prompt = f"""
{confusion_prompt}

Given the original description: "{description}"
Which species is correct?

Respond in JSON: {{"birds": [{{"name": "...", "scientific_name": "...", "confidence": 90, "reason": "..."}}]}}
"""
            verify_response = provider_factory.call_text(verify_prompt)
            verified = parse_birds(verify_response)
            if verified:
                candidates = verified
        
        # Stage 4: Format results
        yield self._status("Generating detailed results...", 4, 4)
        
        birds = deduplicate_birds(candidates)
        results_html = self._build_results(birds, location, month, model_info)
        
        yield results_html
    
    # =========================================================================
    # ENHANCED IMAGE IDENTIFICATION
    # =========================================================================
    
    def identify_image_enhanced(self, image, 
                                  location: str = "India",
                                  month: str = "January") -> Generator[str, None, None]:
        """
        Enhanced image identification with field marks detection.
        
        Improvements:
        - Systematic field marks extraction
        - Regional context
        - Two-pass verification
        """
        if image is None:
            yield "<p style='color:#dc2626'>⚠️ Please upload an image</p>"
            return
        
        from PIL import Image
        if not isinstance(image, Image.Image):
            image = Image.open(image)
        
        model_info = provider_factory.get_model_info("vision")
        
        # Stage 1: Field marks detection
        yield self._status("Analyzing field marks (head, bill, wings, tail)...", 1, 3)
        
        prompt = build_enhanced_image_prompt(location, month)
        
        # Add eBird context
        ebird_context = self.location_context.build_prompt_context(location, month)
        if ebird_context:
            prompt += f"\n\n{ebird_context}"
        
        # Stage 2: Vision model analysis
        yield self._status("Vision model identification...", 2, 3)
        
        response = provider_factory.call_vision(image, prompt)
        candidates = parse_birds(response)
        
        if not candidates:
            # Try simpler prompt
            simple_prompt = f"""Identify this bird. 
Location: {location}, Month: {month}
Respond in JSON: {{"birds": [{{"name": "...", "scientific_name": "...", "confidence": 80}}]}}"""
            
            response = provider_factory.call_vision(image, simple_prompt)
            candidates = parse_birds(response)
        
        if not candidates:
            yield "<p style='color:#dc2626'>❌ Could not identify bird</p>"
            return
        
        # Stage 3: Format results
        yield self._status("Generating results...", 3, 3)
        
        birds = deduplicate_birds(candidates)
        results_html = self._build_results(birds, location, month, model_info)
        
        yield results_html
    
    # =========================================================================
    # ENHANCED AUDIO IDENTIFICATION
    # =========================================================================
    
    def identify_audio_enhanced(self, audio_input,
                                  location: str = "India",
                                  month: str = "January",
                                  use_spectrogram_vision: bool = True) -> Generator[str, None, None]:
        """
        Enhanced audio identification with spectrogram vision.
        
        Improvements:
        - Multi-frequency band analysis
        - Spectrogram + vision model
        - BirdNET + LLM fusion
        """
        if audio_input is None:
            yield "<p style='color:#dc2626'>⚠️ Please provide audio</p>"
            return
        
        if isinstance(audio_input, tuple):
            sr, audio_data = audio_input
        else:
            yield "<p style='color:#dc2626'>❌ Invalid audio format</p>"
            return
        
        if len(audio_data) == 0:
            yield "<p style='color:#dc2626'>❌ Empty audio</p>"
            return
        
        # Normalize
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        audio_data = audio_data.astype(np.float64)
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        model_info = provider_factory.get_model_info("text")
        all_candidates = []
        
        # Stage 1: SAM-Audio preprocessing
        yield self._status("META SAM-Audio filtering...", 1, 5)
        
        segments = self.sam_audio.detect_bird_segments(audio_data, sr)
        bands = self.sam_audio.separate_multiple_birds(audio_data, sr)
        
        # Stage 2: BirdNET analysis
        yield self._status("BirdNET pattern matching...", 2, 5)
        
        if BIRDNET_AVAILABLE:
            birdnet_results = identify_with_birdnet(audio_data, sr, location, month)
            for bird in birdnet_results:
                bird["source"] = "BirdNET"
            all_candidates.extend(birdnet_results)
            
            # Also check frequency bands
            for band in bands[:2]:
                band_audio = band.get("audio")
                if band_audio is not None and len(band_audio) > 0:
                    band_results = identify_with_birdnet(band_audio, sr, location, month)
                    for br in band_results:
                        if br["name"].lower() not in [c["name"].lower() for c in all_candidates]:
                            br["source"] = f"BirdNET ({band['band']})"
                            all_candidates.append(br)
        
        # Stage 3: Spectrogram + Vision (optional)
        if use_spectrogram_vision:
            yield self._status("Spectrogram vision analysis...", 3, 5)
            
            try:
                from audio_vision import SpectrogramAnalyzer
                spec_analyzer = SpectrogramAnalyzer()
                spec_image = spec_analyzer.generate_spectrogram(audio_data, sr)
                
                # Use vision model on spectrogram
                spec_prompt = build_enhanced_audio_prompt(True, location, month)
                spec_response = provider_factory.call_vision(spec_image, spec_prompt)
                spec_birds = parse_birds(spec_response)
                
                for bird in spec_birds:
                    if bird["name"].lower() not in [c["name"].lower() for c in all_candidates]:
                        bird["source"] = "Spectrogram+Vision"
                        all_candidates.append(bird)
            except Exception as e:
                print(f"Spectrogram vision error: {e}")
        
        # Stage 4: LLM reasoning with features
        yield self._status("LLM acoustic reasoning...", 4, 5)
        
        features = extract_audio_features(audio_data, sr)
        
        # Build enhanced audio prompt
        candidate_names = [c["name"] for c in all_candidates[:5]] if all_candidates else []
        
        audio_prompt = f"""Analyze this bird call:

ACOUSTIC FEATURES:
- Frequency range: {features['min_freq']:.0f} - {features['max_freq']:.0f} Hz
- Dominant frequency: {features['dominant_freq']:.0f} Hz
- Pattern: {features['pattern']}
- Duration: {features.get('duration', 'unknown')}

DETECTION HINTS:
- BirdNET suggestions: {', '.join(candidate_names) if candidate_names else 'None'}

CONTEXT:
- Location: {location}
- Month: {month}

Based on these acoustic features, which bird is most likely?
Consider that {location} has these common birds: {', '.join(get_fallback_expected_species(location, 1)[:15])}

Respond in JSON: {{"birds": [{{"name": "...", "scientific_name": "...", "confidence": 80, "acoustic_match": "why features match"}}]}}
"""
        
        llm_response = provider_factory.call_text(audio_prompt)
        llm_birds = parse_birds(llm_response)
        
        for bird in llm_birds:
            if bird["name"].lower() not in [c["name"].lower() for c in all_candidates]:
                bird["source"] = "LLM Acoustic"
                all_candidates.append(bird)
        
        # Stage 5: Merge and format results
        yield self._status("Generating results...", 5, 5)
        
        if not all_candidates:
            yield "<p style='color:#dc2626'>❌ Could not identify bird from audio</p>"
            return
        
        # Merge by weighted voting
        birds = self._merge_multi_source_results(all_candidates)
        results_html = self._build_results(birds, location, month, model_info)
        
        yield results_html
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _status(self, message: str, stage: int, total: int) -> str:
        """Generate status HTML."""
        progress = int((stage / total) * 100)
        return f"""
        <div style='padding:16px;background:#dbeafe;border-radius:8px;margin:10px 0;'>
            <div style='font-weight:bold;margin-bottom:8px;'>🧠 Enhanced Analysis</div>
            <div style='height:8px;background:#e2e8f0;border-radius:4px;overflow:hidden;'>
                <div style='height:100%;width:{progress}%;background:linear-gradient(to right,#3b82f6,#8b5cf6);transition:width 0.3s;'></div>
            </div>
            <div style='margin-top:8px;color:#475569;'>{message}</div>
        </div>
        """
    
    def _merge_multi_source_results(self, candidates: List[Dict]) -> List[Dict]:
        """Merge results from multiple sources with weighted scoring."""
        # Source weights
        WEIGHTS = {
            "BirdNET": 0.45,
            "Spectrogram+Vision": 0.30,
            "LLM Acoustic": 0.25
        }
        
        # Group by bird name
        bird_scores = {}
        for c in candidates:
            name = c["name"].lower()
            source = c.get("source", "Unknown")
            weight = WEIGHTS.get(source.split(" ")[0], 0.25)
            conf = c.get("confidence", 50)
            
            if name not in bird_scores:
                bird_scores[name] = {
                    "name": c["name"],
                    "scientific_name": c.get("scientific_name", c.get("scientific", "")),
                    "score": 0,
                    "sources": [],
                    "reasons": []
                }
            
            bird_scores[name]["score"] += weight * conf
            bird_scores[name]["sources"].append(source)
            if c.get("reason"):
                bird_scores[name]["reasons"].append(c["reason"])
        
        # Sort by score
        sorted_birds = sorted(bird_scores.values(), key=lambda x: x["score"], reverse=True)
        
        # Normalize to percentages
        if sorted_birds:
            max_score = sorted_birds[0]["score"]
            for bird in sorted_birds:
                bird["confidence"] = min(95, int(bird["score"] / max_score * 100))
                bird["reason"] = f"Sources: {', '.join(set(bird['sources']))}"
        
        return sorted_birds[:5]
    
    def _build_results(self, birds: List[Dict], location: str, month: str, 
                       model_info: Dict) -> str:
        """Build HTML results."""
        if not birds:
            return "<p style='color:#dc2626'>❌ No birds identified</p>"
        
        total_birds = len(birds)
        html_parts = []
        
        # Header
        html_parts.append(f"""
        <div style='padding:12px;background:#ecfdf5;border-radius:8px;margin-bottom:12px;'>
            <span style='font-weight:600;color:#047857;'>🎯 Found {total_birds} species</span>
            <span style='color:#6b7280;margin-left:10px;font-size:0.85em;'>
                🤖 {model_info['name']} ({model_info['provider']})
            </span>
        </div>
        """)
        
        # Bird results
        for idx, bird in enumerate(birds, 1):
            html_parts.append(format_bird_result(
                bird, idx, total_birds, location, month
            ))
        
        return "".join(html_parts)


# =========================================================================
# CONVENIENCE FUNCTIONS
# =========================================================================

# Global instance
_enhanced_analyzer = None

def get_enhanced_analyzer() -> EnhancedBirdAnalyzer:
    """Get or create enhanced analyzer instance."""
    global _enhanced_analyzer
    if _enhanced_analyzer is None:
        _enhanced_analyzer = EnhancedBirdAnalyzer()
    return _enhanced_analyzer


def identify_description_enhanced(description: str, location: str = "India",
                                    month: str = "January") -> Generator[str, None, None]:
    """Enhanced description identification."""
    analyzer = get_enhanced_analyzer()
    yield from analyzer.identify_description_enhanced(description, location, month)


def identify_image_enhanced(image, location: str = "India",
                             month: str = "January") -> Generator[str, None, None]:
    """Enhanced image identification."""
    analyzer = get_enhanced_analyzer()
    yield from analyzer.identify_image_enhanced(image, location, month)


def identify_audio_enhanced(audio_input, location: str = "India",
                             month: str = "January") -> Generator[str, None, None]:
    """Enhanced audio identification."""
    analyzer = get_enhanced_analyzer()
    yield from analyzer.identify_audio_enhanced(audio_input, location, month)


# =========================================================================
# TEST
# =========================================================================

if __name__ == "__main__":
    print("🐦 BirdSense Enhanced Analysis")
    print("=" * 50)
    
    analyzer = EnhancedBirdAnalyzer()
    
    # Test description
    print("\n📝 Testing enhanced description identification...")
    description = "A small green bird with red beak in my garden in Bangalore"
    
    for result in analyzer.identify_description_enhanced(description, "Bangalore, Karnataka", "March"):
        if "Found" in result:
            print("✅ Description identification working!")
            break
    
    print("\n✅ Enhanced analysis module ready!")
    print("\nImprovements included:")
    print("  - Chain-of-thought prompting")
    print("  - Few-shot Indian bird examples")
    print("  - Similar species confusion matrix")
    print("  - eBird location context")
    print("  - Spectrogram + vision analysis")
    print("  - Multi-source result fusion")






