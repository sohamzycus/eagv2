"""
Zero-Shot Bird Identification using LLM.

This is the CORE innovation: Instead of training on every bird,
we use the LLM's knowledge to identify ANY bird from audio features.

The LLM has learned about thousands of bird species from its training data,
including their calls, habitats, and behaviors.
"""

import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from .ollama_client import OllamaClient, OllamaConfig

logger = logging.getLogger(__name__)


@dataclass
class AudioFeatures:
    """Extracted audio features for LLM analysis."""
    duration: float
    dominant_frequency_hz: float
    frequency_range: Tuple[float, float]
    spectral_centroid: float
    spectral_bandwidth: float
    tempo_bpm: float
    num_syllables: int
    syllable_rate: float  # syllables per second
    is_melodic: bool
    is_repetitive: bool
    amplitude_pattern: str  # "constant", "rising", "falling", "varied"
    estimated_snr_db: float
    quality_score: float


@dataclass
class ZeroShotResult:
    """Result from zero-shot identification."""
    species_name: str
    scientific_name: str
    confidence: float  # 0.0 to 1.0
    confidence_label: str  # "high", "medium", "low"
    reasoning: str
    key_features_matched: List[str]
    alternative_species: List[Dict[str, Any]]
    is_indian_bird: bool
    is_unusual_sighting: bool
    unusual_reason: Optional[str]
    call_description: str


class ZeroShotBirdIdentifier:
    """
    Zero-shot bird identification using LLM.
    
    This approach:
    1. Extracts audio features (frequency, pattern, duration)
    2. Sends features to LLM with expert prompt
    3. LLM identifies bird from its knowledge base
    4. Returns species with confidence and reasoning
    
    Benefits:
    - No training required
    - Can identify ANY of 10,000+ bird species
    - Works for non-Indian birds too (with novelty flag)
    - Explainable results
    """
    
    def __init__(self, ollama_config: Optional[OllamaConfig] = None):
        self.ollama = OllamaClient(ollama_config or OllamaConfig(model="qwen2.5:3b"))
        self.is_ready = False
        
    def initialize(self) -> bool:
        """Check if LLM is available."""
        try:
            import asyncio
            
            async def _check():
                return await self.ollama.health_check()
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                self.is_ready = loop.run_until_complete(_check())
            except RuntimeError:
                self.is_ready = asyncio.run(_check())
            
            return self.is_ready
        except Exception as e:
            logger.warning(f"Failed to initialize LLM: {e}")
            return False
    
    def extract_features(
        self, 
        audio: np.ndarray, 
        sample_rate: int = 32000,
        mel_spec: Optional[np.ndarray] = None
    ) -> AudioFeatures:
        """Extract audio features for LLM analysis."""
        import scipy.signal as signal
        
        duration = len(audio) / sample_rate
        
        # Frequency analysis
        freqs, psd = signal.welch(audio, sample_rate, nperseg=2048)
        
        # Dominant frequency
        dominant_idx = np.argmax(psd)
        dominant_freq = freqs[dominant_idx]
        
        # Frequency range (where 90% of energy is)
        cumsum = np.cumsum(psd) / np.sum(psd)
        freq_low = freqs[np.searchsorted(cumsum, 0.05)]
        freq_high = freqs[np.searchsorted(cumsum, 0.95)]
        
        # Spectral centroid
        spectral_centroid = np.sum(freqs * psd) / (np.sum(psd) + 1e-10)
        
        # Spectral bandwidth
        spectral_bandwidth = np.sqrt(np.sum(((freqs - spectral_centroid) ** 2) * psd) / (np.sum(psd) + 1e-10))
        
        # Amplitude envelope analysis
        envelope = np.abs(signal.hilbert(audio))
        envelope_smooth = signal.medfilt(envelope, 1001)
        
        # Detect syllables (peaks in envelope)
        peaks, _ = signal.find_peaks(envelope_smooth, height=0.1 * np.max(envelope_smooth), distance=sample_rate // 10)
        num_syllables = len(peaks)
        syllable_rate = num_syllables / duration if duration > 0 else 0
        
        # Amplitude pattern
        if len(envelope_smooth) > 100:
            start_amp = np.mean(envelope_smooth[:len(envelope_smooth)//4])
            end_amp = np.mean(envelope_smooth[-len(envelope_smooth)//4:])
            amp_var = np.std(envelope_smooth) / (np.mean(envelope_smooth) + 1e-10)
            
            if amp_var > 0.5:
                amp_pattern = "varied"
            elif end_amp > start_amp * 1.3:
                amp_pattern = "rising"
            elif end_amp < start_amp * 0.7:
                amp_pattern = "falling"
            else:
                amp_pattern = "constant"
        else:
            amp_pattern = "constant"
        
        # Melodic detection (frequency variation)
        if len(audio) > sample_rate:
            chunks = np.array_split(audio, 10)
            chunk_freqs = []
            for chunk in chunks:
                if len(chunk) > 512:
                    f, p = signal.welch(chunk, sample_rate, nperseg=512)
                    chunk_freqs.append(f[np.argmax(p)])
            freq_variation = np.std(chunk_freqs) / (np.mean(chunk_freqs) + 1e-10)
            is_melodic = freq_variation > 0.1
        else:
            is_melodic = False
        
        # Repetitiveness detection
        if num_syllables >= 3:
            if syllable_rate > 1.5 and syllable_rate < 10:  # Regular pattern
                is_repetitive = True
            else:
                is_repetitive = False
        else:
            is_repetitive = num_syllables >= 2
        
        # SNR estimation
        noise_floor = np.percentile(np.abs(audio), 10)
        signal_peak = np.percentile(np.abs(audio), 95)
        snr_db = 20 * np.log10((signal_peak + 1e-10) / (noise_floor + 1e-10))
        
        # Quality score
        quality_score = min(1.0, max(0.0, (snr_db - 5) / 25))
        
        # Tempo (for rhythmic calls)
        if num_syllables >= 2:
            tempo_bpm = syllable_rate * 60
        else:
            tempo_bpm = 0
        
        return AudioFeatures(
            duration=duration,
            dominant_frequency_hz=float(dominant_freq),
            frequency_range=(float(freq_low), float(freq_high)),
            spectral_centroid=float(spectral_centroid),
            spectral_bandwidth=float(spectral_bandwidth),
            tempo_bpm=float(tempo_bpm),
            num_syllables=num_syllables,
            syllable_rate=float(syllable_rate),
            is_melodic=is_melodic,
            is_repetitive=is_repetitive,
            amplitude_pattern=amp_pattern,
            estimated_snr_db=float(snr_db),
            quality_score=float(quality_score)
        )
    
    def identify(
        self,
        features: AudioFeatures,
        location: Optional[str] = None,
        month: Optional[int] = None,
        user_description: Optional[str] = None
    ) -> ZeroShotResult:
        """
        Identify bird species using zero-shot LLM inference.
        
        This is the NOVEL approach - using LLM's knowledge to identify
        any bird without needing to train on that specific species.
        """
        
        # Build expert prompt
        prompt = self._build_identification_prompt(features, location, month, user_description)
        
        # Call LLM (synchronously using asyncio)
        try:
            import asyncio
            
            async def _generate():
                return await self.ollama.generate(
                    prompt,
                    system_prompt=self._get_expert_system_prompt(),
                    temperature=0.3,  # Lower for more deterministic
                    max_tokens=1000
                )
            
            # Run async in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Use nest_asyncio for nested event loops
                    import nest_asyncio
                    nest_asyncio.apply()
                response = loop.run_until_complete(_generate())
            except RuntimeError:
                # No event loop running
                response = asyncio.run(_generate())
            
            # Parse response
            return self._parse_identification_response(response, features)
            
        except Exception as e:
            logger.error(f"LLM identification failed: {e}")
            return self._fallback_result(features)
    
    def _get_expert_system_prompt(self) -> str:
        """Expert ornithologist system prompt."""
        return """You are an expert ornithologist with deep knowledge of bird vocalizations worldwide.
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

Always respond in the exact JSON format requested."""

    def _build_identification_prompt(
        self,
        features: AudioFeatures,
        location: Optional[str],
        month: Optional[int],
        user_description: Optional[str]
    ) -> str:
        """Build identification prompt from audio features."""
        
        # Describe frequency in bird call terms
        freq_desc = self._describe_frequency(features.dominant_frequency_hz)
        
        # Season
        season = self._get_season(month) if month else "unknown"
        
        prompt = f"""Identify this bird based on its call characteristics:

## Audio Features
- **Duration**: {features.duration:.1f} seconds
- **Dominant Frequency**: {features.dominant_frequency_hz:.0f} Hz ({freq_desc})
- **Frequency Range**: {features.frequency_range[0]:.0f} - {features.frequency_range[1]:.0f} Hz
- **Call Pattern**: {"Melodic/varied" if features.is_melodic else "Monotone"}, {"Repetitive" if features.is_repetitive else "Non-repetitive"}
- **Syllables**: {features.num_syllables} syllables at {features.syllable_rate:.1f}/second
- **Rhythm**: {features.tempo_bpm:.0f} BPM (beats per minute)
- **Amplitude**: {features.amplitude_pattern} pattern

## Context
- **Location**: {location or "India (unspecified)"}
- **Season**: {season}
- **Recording Quality**: {self._quality_label(features.quality_score)} (SNR: {features.estimated_snr_db:.0f}dB)
"""
        
        if user_description:
            prompt += f"- **Observer Notes**: {user_description}\n"
        
        prompt += """
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
}"""
        
        return prompt
    
    def _describe_frequency(self, freq: float) -> str:
        """Describe frequency in bird call terms."""
        if freq < 500:
            return "very low (large bird or booming call)"
        elif freq < 1000:
            return "low (owl, dove, or large bird)"
        elif freq < 2000:
            return "low-medium (cuckoo, crow, or medium bird)"
        elif freq < 4000:
            return "medium (most songbirds)"
        elif freq < 6000:
            return "medium-high (warbler, sunbird)"
        elif freq < 8000:
            return "high (small passerine)"
        else:
            return "very high (insect-like or whistle)"
    
    def _get_season(self, month: int) -> str:
        """Get Indian season from month."""
        if month in [12, 1, 2]:
            return "winter (Dec-Feb) - winter migrants present"
        elif month in [3, 4, 5]:
            return "summer/pre-monsoon (Mar-May) - breeding season"
        elif month in [6, 7, 8, 9]:
            return "monsoon (Jun-Sep)"
        else:
            return "post-monsoon (Oct-Nov) - migration period"
    
    def _quality_label(self, score: float) -> str:
        """Convert quality score to label."""
        if score > 0.8:
            return "excellent"
        elif score > 0.6:
            return "good"
        elif score > 0.4:
            return "fair"
        else:
            return "poor"
    
    def _parse_identification_response(
        self, 
        response: str,
        features: AudioFeatures
    ) -> ZeroShotResult:
        """Parse LLM response into structured result."""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                confidence = float(data.get('confidence', 0.5))
                
                return ZeroShotResult(
                    species_name=data.get('species_name', 'Unknown'),
                    scientific_name=data.get('scientific_name', ''),
                    confidence=confidence,
                    confidence_label=self._confidence_label(confidence),
                    reasoning=data.get('reasoning', ''),
                    key_features_matched=data.get('key_features_matched', []),
                    alternative_species=data.get('alternatives', []),
                    is_indian_bird=data.get('is_indian_bird', True),
                    is_unusual_sighting=data.get('is_unusual', False),
                    unusual_reason=data.get('unusual_reason'),
                    call_description=data.get('typical_call', '')
                )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON: {e}")
        
        # Fallback: try to extract species name from text
        return self._fallback_result(features, response)
    
    def _confidence_label(self, confidence: float) -> str:
        """Convert confidence to label."""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _fallback_result(
        self, 
        features: AudioFeatures,
        llm_response: str = ""
    ) -> ZeroShotResult:
        """Generate fallback result when LLM parsing fails."""
        
        # Try to guess based on frequency
        if features.dominant_frequency_hz < 1000:
            if features.is_repetitive:
                species = "Spotted Owlet"
                scientific = "Athene brama"
            else:
                species = "Indian Cuckoo"
                scientific = "Cuculus micropterus"
        elif features.dominant_frequency_hz < 3000:
            if features.is_melodic:
                species = "Oriental Magpie-Robin"
                scientific = "Copsychus saularis"
            else:
                species = "Asian Koel"
                scientific = "Eudynamys scolopaceus"
        else:
            if features.syllable_rate > 3:
                species = "Coppersmith Barbet"
                scientific = "Psilopogon haemacephalus"
            else:
                species = "Common Tailorbird"
                scientific = "Orthotomus sutorius"
        
        return ZeroShotResult(
            species_name=species,
            scientific_name=scientific,
            confidence=0.4,
            confidence_label="low",
            reasoning="Identification based on audio frequency and pattern analysis. LLM analysis unavailable.",
            key_features_matched=["frequency range", "call pattern"],
            alternative_species=[],
            is_indian_bird=True,
            is_unusual_sighting=False,
            unusual_reason=None,
            call_description=""
        )


# Global instance for quick access
_identifier: Optional[ZeroShotBirdIdentifier] = None

def get_zero_shot_identifier() -> ZeroShotBirdIdentifier:
    """Get or create global zero-shot identifier."""
    global _identifier
    if _identifier is None:
        _identifier = ZeroShotBirdIdentifier()
    return _identifier

