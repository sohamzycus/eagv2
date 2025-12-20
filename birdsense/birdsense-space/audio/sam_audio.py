"""
SAM-Audio Integration for BirdSense.

Integrates Meta's SAM-Audio (Segment Anything in Audio) model for:
- Audio source separation
- Isolating bird calls from background noise
- Handling multi-bird chorus scenarios
- Improving recognition accuracy in challenging conditions

References:
- Paper: https://ai.meta.com/research/publications/sam-audio-segment-anything-in-audio/
- Model: https://huggingface.co/facebook/sam-audio-large
- Demo: https://ai.meta.com/samaudio/

SAM-Audio uses multimodal prompts (text, audio, point) to segment audio,
making it ideal for isolating specific bird calls.
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SAMAudioConfig:
    """Configuration for SAM-Audio integration."""
    model_name: str = "facebook/sam-audio-large"
    device: str = "auto"
    cache_dir: str = ".cache/sam_audio"
    
    # Separation settings
    num_sources: int = 4  # Max number of sources to separate
    min_source_energy: float = 0.01  # Minimum energy threshold
    
    # Bird-specific settings
    bird_frequency_range: Tuple[int, int] = (500, 10000)  # Hz
    use_text_prompt: bool = True  # Use text prompts like "bird call"
    

class SAMAudioProcessor:
    """
    SAM-Audio processor for bird call isolation.
    
    Uses Meta's SAM-Audio model to:
    1. Separate overlapping audio sources
    2. Isolate bird calls from background
    3. Handle multi-bird recordings
    4. Improve SNR for feeble recordings
    """
    
    def __init__(self, config: Optional[SAMAudioConfig] = None):
        self.config = config or SAMAudioConfig()
        self.model = None
        self.processor = None
        self.device = None
        self._model_loaded = False
        
    def _setup_device(self):
        """Setup compute device."""
        if self.config.device == "auto":
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(self.config.device)
        
        logger.info(f"SAM-Audio using device: {self.device}")
    
    def load_model(self) -> bool:
        """
        Load SAM-Audio model from HuggingFace.
        
        Returns:
            True if model loaded successfully
        """
        if self._model_loaded:
            return True
        
        self._setup_device()
        
        try:
            # Try to load from transformers
            from transformers import AutoModel, AutoProcessor
            
            logger.info(f"Loading SAM-Audio model: {self.config.model_name}")
            
            cache_dir = Path(self.config.cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            self.processor = AutoProcessor.from_pretrained(
                self.config.model_name,
                cache_dir=str(cache_dir)
            )
            
            self.model = AutoModel.from_pretrained(
                self.config.model_name,
                cache_dir=str(cache_dir)
            )
            
            self.model.to(self.device)
            self.model.eval()
            
            self._model_loaded = True
            logger.info("SAM-Audio model loaded successfully")
            return True
            
        except ImportError:
            logger.warning("transformers library not available for SAM-Audio")
            return False
        except Exception as e:
            logger.warning(f"Failed to load SAM-Audio: {e}")
            logger.info("Falling back to spectral separation method")
            return False
    
    def is_available(self) -> bool:
        """Check if SAM-Audio is available."""
        return self._model_loaded
    
    @torch.no_grad()
    def separate_sources(
        self,
        audio: np.ndarray,
        sample_rate: int,
        text_prompts: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Separate audio into individual sources.
        
        Args:
            audio: Input audio waveform
            sample_rate: Sample rate
            text_prompts: Optional text prompts like ["bird call", "wind"]
            
        Returns:
            List of separated sources with metadata
        """
        if not self._model_loaded:
            # Fallback to spectral separation
            return self._spectral_separation(audio, sample_rate)
        
        try:
            # Prepare input for SAM-Audio
            if text_prompts is None:
                text_prompts = ["bird vocalization", "background noise"]
            
            # Process through model
            inputs = self.processor(
                audio,
                sampling_rate=sample_rate,
                text=text_prompts,
                return_tensors="pt"
            )
            
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            outputs = self.model(**inputs)
            
            # Extract separated sources
            sources = []
            for i, mask in enumerate(outputs.masks):
                separated = audio * mask.cpu().numpy()
                energy = np.mean(separated ** 2)
                
                if energy > self.config.min_source_energy:
                    sources.append({
                        'audio': separated,
                        'energy': float(energy),
                        'label': text_prompts[i] if i < len(text_prompts) else f'source_{i}',
                        'mask': mask.cpu().numpy()
                    })
            
            return sources
            
        except Exception as e:
            logger.warning(f"SAM-Audio separation failed: {e}")
            return self._spectral_separation(audio, sample_rate)
    
    def _spectral_separation(
        self,
        audio: np.ndarray,
        sample_rate: int
    ) -> List[Dict[str, Any]]:
        """
        Fallback spectral separation when SAM-Audio unavailable.
        
        Uses spectral masking to separate bird frequency ranges
        from background noise.
        """
        import scipy.signal as signal
        
        # Compute STFT
        f, t, Zxx = signal.stft(audio, fs=sample_rate, nperseg=1024, noverlap=768)
        magnitude = np.abs(Zxx)
        phase = np.angle(Zxx)
        
        # Create frequency masks
        low_freq, high_freq = self.config.bird_frequency_range
        
        # Bird frequency mask (500-10000 Hz)
        bird_mask = (f >= low_freq) & (f <= high_freq)
        bird_mask = bird_mask.astype(float).reshape(-1, 1)
        
        # Apply soft masking
        bird_magnitude = magnitude * bird_mask
        background_magnitude = magnitude * (1 - bird_mask * 0.8)
        
        # Reconstruct audio
        bird_stft = bird_magnitude * np.exp(1j * phase)
        _, bird_audio = signal.istft(bird_stft, fs=sample_rate, nperseg=1024, noverlap=768)
        
        background_stft = background_magnitude * np.exp(1j * phase)
        _, background_audio = signal.istft(background_stft, fs=sample_rate, nperseg=1024, noverlap=768)
        
        # Ensure same length
        min_len = min(len(audio), len(bird_audio), len(background_audio))
        bird_audio = bird_audio[:min_len]
        background_audio = background_audio[:min_len]
        
        sources = [
            {
                'audio': bird_audio.astype(np.float32),
                'energy': float(np.mean(bird_audio ** 2)),
                'label': 'bird_frequencies',
                'mask': bird_mask.flatten()
            },
            {
                'audio': background_audio.astype(np.float32),
                'energy': float(np.mean(background_audio ** 2)),
                'label': 'background',
                'mask': (1 - bird_mask).flatten()
            }
        ]
        
        return sources
    
    def isolate_bird_call(
        self,
        audio: np.ndarray,
        sample_rate: int
    ) -> Tuple[np.ndarray, float]:
        """
        Isolate the primary bird call from audio.
        
        Args:
            audio: Input audio
            sample_rate: Sample rate
            
        Returns:
            Tuple of (isolated_audio, quality_score)
        """
        # Try SAM-Audio first
        sources = self.separate_sources(
            audio, 
            sample_rate,
            text_prompts=["bird call", "bird song", "background noise", "wind"]
        )
        
        # Find the bird source
        bird_source = None
        max_bird_energy = 0
        
        for source in sources:
            label = source['label'].lower()
            if 'bird' in label and source['energy'] > max_bird_energy:
                bird_source = source
                max_bird_energy = source['energy']
        
        if bird_source is None:
            # No clear bird source found, return original with spectral enhancement
            return self._enhance_bird_frequencies(audio, sample_rate)
        
        # Calculate quality improvement
        original_energy = np.mean(audio ** 2)
        isolated_energy = bird_source['energy']
        quality_score = min(1.0, isolated_energy / (original_energy + 1e-8))
        
        return bird_source['audio'], quality_score
    
    def _enhance_bird_frequencies(
        self,
        audio: np.ndarray,
        sample_rate: int
    ) -> Tuple[np.ndarray, float]:
        """Enhance bird frequency range in audio."""
        import scipy.signal as signal
        
        low_freq, high_freq = self.config.bird_frequency_range
        nyquist = sample_rate / 2
        
        # Bandpass filter
        low = low_freq / nyquist
        high = min(high_freq / nyquist, 0.99)
        
        b, a = signal.butter(4, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, audio)
        
        # Mix with original (subtle enhancement)
        enhanced = audio * 0.3 + filtered * 0.7
        enhanced = enhanced / (np.max(np.abs(enhanced)) + 1e-8)
        
        return enhanced.astype(np.float32), 0.7
    
    def process_multi_bird(
        self,
        audio: np.ndarray,
        sample_rate: int,
        max_birds: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Process multi-bird recording to isolate individual birds.
        
        Args:
            audio: Multi-bird recording
            sample_rate: Sample rate
            max_birds: Maximum number of birds to isolate
            
        Returns:
            List of isolated bird calls with metadata
        """
        # Create prompts for multiple birds
        text_prompts = [f"bird call {i+1}" for i in range(max_birds)]
        text_prompts.append("background noise")
        
        sources = self.separate_sources(audio, sample_rate, text_prompts)
        
        # Filter to just bird sources
        bird_calls = []
        for source in sources:
            if 'bird' in source['label'].lower() and source['energy'] > self.config.min_source_energy:
                bird_calls.append({
                    'audio': source['audio'],
                    'energy': source['energy'],
                    'index': len(bird_calls)
                })
        
        # Sort by energy (loudest first)
        bird_calls.sort(key=lambda x: x['energy'], reverse=True)
        
        return bird_calls[:max_birds]


class SAMAudioEnhancer:
    """
    High-level interface for using SAM-Audio to improve BirdSense accuracy.
    
    Provides automatic preprocessing to:
    1. Improve SNR for feeble recordings
    2. Handle noisy environments
    3. Separate multi-bird choruses
    """
    
    def __init__(self, config: Optional[SAMAudioConfig] = None):
        self.processor = SAMAudioProcessor(config)
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize SAM-Audio (loads model)."""
        if not self._initialized:
            self._initialized = self.processor.load_model()
        return self._initialized
    
    def enhance_audio(
        self,
        audio: np.ndarray,
        sample_rate: int,
        scenario: str = "auto"
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Automatically enhance audio for better bird recognition.
        
        Args:
            audio: Input audio
            sample_rate: Sample rate
            scenario: One of 'auto', 'feeble', 'noisy', 'multi_bird'
            
        Returns:
            Tuple of (enhanced_audio, metadata)
        """
        metadata = {
            'original_rms': float(np.sqrt(np.mean(audio ** 2))),
            'scenario': scenario,
            'sam_audio_used': self.processor.is_available()
        }
        
        if scenario == "auto":
            scenario = self._detect_scenario(audio, sample_rate)
            metadata['detected_scenario'] = scenario
        
        if scenario == "feeble":
            enhanced, quality = self.processor.isolate_bird_call(audio, sample_rate)
            # Boost amplitude
            enhanced = enhanced * 2.0
            enhanced = np.clip(enhanced, -1.0, 1.0)
            metadata['enhancement'] = 'amplitude_boost'
            
        elif scenario == "noisy":
            enhanced, quality = self.processor.isolate_bird_call(audio, sample_rate)
            metadata['enhancement'] = 'noise_removal'
            
        elif scenario == "multi_bird":
            birds = self.processor.process_multi_bird(audio, sample_rate)
            if birds:
                # Return loudest bird for primary classification
                enhanced = birds[0]['audio']
                metadata['num_birds_detected'] = len(birds)
                metadata['enhancement'] = 'bird_separation'
            else:
                enhanced = audio
                metadata['enhancement'] = 'none'
        else:
            enhanced = audio
            metadata['enhancement'] = 'none'
        
        metadata['enhanced_rms'] = float(np.sqrt(np.mean(enhanced ** 2)))
        metadata['snr_improvement'] = metadata['enhanced_rms'] / (metadata['original_rms'] + 1e-8)
        
        return enhanced.astype(np.float32), metadata
    
    def _detect_scenario(
        self,
        audio: np.ndarray,
        sample_rate: int
    ) -> str:
        """Automatically detect audio scenario."""
        rms = np.sqrt(np.mean(audio ** 2))
        
        # Check for feeble audio
        if rms < 0.05:
            return "feeble"
        
        # Check for multi-source (high variance in spectral energy)
        import scipy.signal as signal
        f, t, Zxx = signal.stft(audio, fs=sample_rate, nperseg=512)
        frame_energy = np.sum(np.abs(Zxx) ** 2, axis=0)
        energy_variance = np.var(frame_energy) / (np.mean(frame_energy) ** 2 + 1e-8)
        
        if energy_variance > 2.0:
            return "multi_bird"
        
        # Check SNR estimate
        # High spectral flatness suggests noise
        spectral_flatness = np.exp(np.mean(np.log(np.abs(Zxx) + 1e-8))) / (np.mean(np.abs(Zxx)) + 1e-8)
        if spectral_flatness > 0.3:
            return "noisy"
        
        return "clear"


# Convenience function
def create_sam_audio_enhancer(
    device: str = "auto",
    load_model: bool = True
) -> SAMAudioEnhancer:
    """
    Create SAM-Audio enhancer instance.
    
    Args:
        device: Compute device
        load_model: Whether to load model immediately
        
    Returns:
        Configured SAMAudioEnhancer
    """
    config = SAMAudioConfig(device=device)
    enhancer = SAMAudioEnhancer(config)
    
    if load_model:
        enhancer.initialize()
    
    return enhancer

