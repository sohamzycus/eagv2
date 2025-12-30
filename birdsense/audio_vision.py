"""
🎵 BirdSense Audio-Vision Analysis
Developed by Soham

Use vision models to analyze spectrograms for bird identification.
This is a powerful technique that leverages visual pattern recognition
on acoustic data.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from scipy import signal
from PIL import Image
import io
import tempfile
import os
from typing import Dict, List, Optional, Tuple

from providers import provider_factory
from analysis import parse_birds, deduplicate_birds
from enhanced_prompts import SPECTROGRAM_ANALYSIS_PROMPT, get_regional_context


class SpectrogramAnalyzer:
    """
    Convert audio to spectrogram and analyze with vision model.
    
    This technique is powerful because:
    1. Vision models excel at pattern recognition
    2. Spectrograms visually show frequency patterns
    3. Bird songs have distinctive visual signatures
    """
    
    def __init__(self):
        self.colormap = 'viridis'  # Clear visualization
    
    def generate_spectrogram(self, audio: np.ndarray, sr: int, 
                              output_format: str = "pil") -> Image.Image:
        """
        Generate a mel spectrogram image from audio.
        
        Args:
            audio: Audio signal as numpy array
            sr: Sample rate
            output_format: "pil" for PIL Image, "path" for file path
        
        Returns:
            PIL Image of the spectrogram
        """
        # Ensure mono
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)
        
        # Compute spectrogram
        nperseg = min(2048, len(audio) // 4)
        noverlap = nperseg // 2
        
        frequencies, times, Sxx = signal.spectrogram(
            audio, sr,
            nperseg=nperseg,
            noverlap=noverlap,
            scaling='density'
        )
        
        # Convert to dB scale
        Sxx_db = 10 * np.log10(Sxx + 1e-10)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
        
        # Plot spectrogram
        im = ax.pcolormesh(times, frequencies, Sxx_db, 
                          shading='gouraud', cmap=self.colormap)
        
        # Add labels and formatting
        ax.set_ylabel('Frequency (Hz)', fontsize=12)
        ax.set_xlabel('Time (s)', fontsize=12)
        ax.set_title('Bird Call Spectrogram', fontsize=14)
        
        # Focus on bird frequencies (0-10000 Hz typically)
        ax.set_ylim(0, min(10000, sr // 2))
        
        # Add colorbar
        cbar = fig.colorbar(im, ax=ax, label='Power (dB)')
        
        # Add frequency reference lines
        for freq in [1000, 2000, 4000, 6000, 8000]:
            if freq < sr // 2:
                ax.axhline(y=freq, color='white', linestyle='--', 
                          alpha=0.3, linewidth=0.5)
        
        plt.tight_layout()
        
        # Convert to PIL Image
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buf.seek(0)
        plt.close(fig)
        
        image = Image.open(buf).convert('RGB')
        return image
    
    def generate_mel_spectrogram(self, audio: np.ndarray, sr: int) -> Image.Image:
        """
        Generate mel-scale spectrogram (better for bird calls).
        """
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)
        
        # Mel spectrogram parameters
        n_fft = 2048
        hop_length = 512
        n_mels = 128
        
        # Compute mel spectrogram manually (no librosa dependency)
        # Using scipy for STFT
        f, t, Zxx = signal.stft(audio, sr, nperseg=n_fft, noverlap=n_fft-hop_length)
        
        # Convert to power
        power = np.abs(Zxx) ** 2
        
        # Simple mel filterbank
        mel_low = 0
        mel_high = 2595 * np.log10(1 + (sr/2) / 700)
        mel_points = np.linspace(mel_low, mel_high, n_mels + 2)
        hz_points = 700 * (10**(mel_points / 2595) - 1)
        
        # Bin frequencies
        bin_points = np.floor((n_fft + 1) * hz_points / sr).astype(int)
        
        # Create filterbank
        fbank = np.zeros((n_mels, n_fft // 2 + 1))
        for i in range(n_mels):
            for j in range(bin_points[i], bin_points[i+1]):
                fbank[i, j] = (j - bin_points[i]) / (bin_points[i+1] - bin_points[i])
            for j in range(bin_points[i+1], bin_points[i+2]):
                fbank[i, j] = (bin_points[i+2] - j) / (bin_points[i+2] - bin_points[i+1])
        
        # Apply filterbank
        mel_spec = np.dot(fbank, power[:len(fbank[0]), :])
        
        # Convert to dB
        mel_spec_db = 10 * np.log10(mel_spec + 1e-10)
        
        # Plot
        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
        
        im = ax.imshow(mel_spec_db, aspect='auto', origin='lower',
                      extent=[0, len(audio)/sr, 0, n_mels],
                      cmap=self.colormap)
        
        ax.set_ylabel('Mel Frequency Bin', fontsize=12)
        ax.set_xlabel('Time (s)', fontsize=12)
        ax.set_title('Mel Spectrogram - Bird Call Analysis', fontsize=14)
        
        fig.colorbar(im, ax=ax, label='Power (dB)')
        plt.tight_layout()
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return Image.open(buf).convert('RGB')
    
    def analyze_with_vision(self, audio: np.ndarray, sr: int,
                            location: str = "India", 
                            month: str = "January") -> List[Dict]:
        """
        Analyze audio using spectrogram + vision model.
        
        This is the main method that:
        1. Generates spectrogram image
        2. Sends to vision model with acoustic analysis prompt
        3. Parses and returns bird identifications
        """
        # Generate spectrogram
        spectrogram_image = self.generate_spectrogram(audio, sr)
        
        # Build prompt with regional context
        prompt = SPECTROGRAM_ANALYSIS_PROMPT.format(
            location=location,
            month=month
        )
        prompt += get_regional_context(location, month)
        
        # Call vision model
        try:
            response = provider_factory.call_vision(spectrogram_image, prompt)
            birds = parse_birds(response)
            return deduplicate_birds(birds)
        except Exception as e:
            print(f"Vision analysis error: {e}")
            return []
    
    def extract_visual_features(self, spectrogram_image: Image.Image) -> Dict:
        """
        Extract visual features from spectrogram for LLM prompt.
        """
        # Convert to numpy
        img_array = np.array(spectrogram_image)
        
        # Simple feature extraction
        features = {
            "has_harmonics": False,
            "frequency_range": "medium",
            "temporal_pattern": "unknown",
            "intensity": "medium"
        }
        
        # Analyze intensity distribution
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array
        
        # Check for horizontal lines (harmonics)
        row_variance = np.var(gray, axis=1)
        if np.max(row_variance) > 2 * np.mean(row_variance):
            features["has_harmonics"] = True
        
        # Check intensity
        mean_intensity = np.mean(gray)
        if mean_intensity > 200:
            features["intensity"] = "high"
        elif mean_intensity < 100:
            features["intensity"] = "low"
        
        return features


class MultiModalAudioAnalyzer:
    """
    Combine multiple audio analysis methods:
    1. BirdNET pattern matching
    2. Spectrogram vision analysis
    3. Acoustic feature LLM analysis
    """
    
    def __init__(self):
        self.spectrogram_analyzer = SpectrogramAnalyzer()
    
    def analyze(self, audio: np.ndarray, sr: int,
                location: str = "India",
                month: str = "January",
                use_birdnet: bool = True,
                use_spectrogram: bool = True,
                use_features: bool = True) -> List[Dict]:
        """
        Multi-modal audio analysis combining all methods.
        """
        from analysis import (identify_with_birdnet, extract_audio_features, 
                            hybrid_llm_validation, BIRDNET_AVAILABLE)
        
        all_results = []
        weights = []
        
        # Method 1: BirdNET
        if use_birdnet and BIRDNET_AVAILABLE:
            try:
                birdnet_results = identify_with_birdnet(audio, sr, location, month)
                if birdnet_results:
                    all_results.append(("birdnet", birdnet_results))
                    weights.append(0.4)  # BirdNET weight
            except Exception as e:
                print(f"BirdNET error: {e}")
        
        # Method 2: Spectrogram + Vision
        if use_spectrogram:
            try:
                spec_results = self.spectrogram_analyzer.analyze_with_vision(
                    audio, sr, location, month
                )
                if spec_results:
                    all_results.append(("spectrogram", spec_results))
                    weights.append(0.35)  # Spectrogram weight
            except Exception as e:
                print(f"Spectrogram error: {e}")
        
        # Method 3: Acoustic Features + LLM
        if use_features:
            try:
                features = extract_audio_features(audio, sr)
                if all_results:
                    # Get hints from other methods
                    hints = []
                    for method, results in all_results:
                        hints.extend([r.get("name", "") for r in results[:3]])
                    
                    feature_results = hybrid_llm_validation(
                        [{"name": h, "confidence": 50} for h in hints[:5]],
                        features, location, month
                    )
                else:
                    # No hints, pure feature analysis
                    feature_results = self._analyze_features_only(features, location, month)
                
                if feature_results:
                    all_results.append(("features", feature_results))
                    weights.append(0.25)  # Features weight
            except Exception as e:
                print(f"Features error: {e}")
        
        # Merge all results
        return self._merge_multimodal_results(all_results, weights)
    
    def _analyze_features_only(self, features: Dict, location: str, month: str) -> List[Dict]:
        """Analyze using only acoustic features."""
        from enhanced_prompts import SPECTROGRAM_ANALYSIS_PROMPT
        
        prompt = f"""Analyze these acoustic features and identify the bird:

Dominant Frequency: {features.get('dominant_freq', 0):.0f} Hz
Frequency Range: {features.get('freq_range', (0, 0))}
Spectral Centroid: {features.get('spectral_centroid', 0):.0f} Hz
Temporal Pattern: {features.get('temporal_pattern', 'unknown')}
Location: {location}
Month: {month}

Based on these acoustic characteristics, identify likely bird species.
Respond in JSON format with "birds" array containing name, scientific_name, confidence.
"""
        
        try:
            response = provider_factory.call_text(prompt)
            return parse_birds(response)
        except:
            return []
    
    def _merge_multimodal_results(self, all_results: List[Tuple[str, List[Dict]]], 
                                   weights: List[float]) -> List[Dict]:
        """Merge results from multiple methods with weighted voting."""
        if not all_results:
            return []
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Aggregate scores
        bird_scores = {}
        
        for (method, results), weight in zip(all_results, weights):
            for bird in results[:5]:
                name = bird.get("name", "").lower()
                if not name:
                    continue
                
                if name not in bird_scores:
                    bird_scores[name] = {
                        "name": bird.get("name"),
                        "scientific_name": bird.get("scientific_name", ""),
                        "score": 0,
                        "sources": []
                    }
                
                # Add weighted score
                confidence = bird.get("confidence", 50)
                bird_scores[name]["score"] += weight * confidence
                bird_scores[name]["sources"].append(method)
        
        # Sort by score
        sorted_birds = sorted(bird_scores.values(), 
                            key=lambda x: x["score"], reverse=True)
        
        # Convert to final format
        results = []
        max_score = sorted_birds[0]["score"] if sorted_birds else 1
        
        for bird in sorted_birds[:5]:
            results.append({
                "name": bird["name"],
                "scientific_name": bird["scientific_name"],
                "confidence": min(95, bird["score"] / max_score * 100),
                "sources": bird["sources"]
            })
        
        return results


# Convenience functions
def analyze_audio_multimodal(audio: np.ndarray, sr: int,
                              location: str = "India",
                              month: str = "January") -> List[Dict]:
    """
    Main function for multi-modal audio analysis.
    
    Combines:
    - BirdNET pattern matching (40%)
    - Spectrogram vision analysis (35%)
    - Acoustic feature LLM analysis (25%)
    """
    analyzer = MultiModalAudioAnalyzer()
    return analyzer.analyze(audio, sr, location, month)


def generate_spectrogram_for_display(audio: np.ndarray, sr: int) -> Image.Image:
    """Generate spectrogram image for UI display."""
    analyzer = SpectrogramAnalyzer()
    return analyzer.generate_spectrogram(audio, sr)


# Test
if __name__ == "__main__":
    print("Testing SpectrogramAnalyzer...")
    
    # Generate test audio (simple sine wave)
    sr = 44100
    duration = 3.0
    t = np.linspace(0, duration, int(sr * duration))
    
    # Simulate koel call (rising frequency)
    freq = 700 + 800 * (t / duration)
    audio = 0.5 * np.sin(2 * np.pi * np.cumsum(freq) / sr)
    
    analyzer = SpectrogramAnalyzer()
    spec_image = analyzer.generate_spectrogram(audio, sr)
    
    print(f"Generated spectrogram: {spec_image.size}")
    spec_image.save("test_spectrogram.png")
    print("Saved to test_spectrogram.png")





