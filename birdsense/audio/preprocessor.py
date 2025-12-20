"""
Audio Preprocessing Pipeline for BirdSense.

Handles:
- Audio loading and resampling
- Spectrogram generation (mel-spectrogram)
- Noise reduction for challenging recordings
- Amplitude normalization
- Chunk splitting for long recordings
"""

import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from typing import Tuple, Optional, List
from dataclasses import dataclass
import io


@dataclass
class AudioConfig:
    """Audio processing configuration."""
    sample_rate: int = 32000
    duration: float = 5.0
    n_fft: int = 1024
    hop_length: int = 320
    n_mels: int = 128
    fmin: int = 50
    fmax: int = 14000
    normalize: bool = True
    noise_reduction: bool = True
    noise_reduction_strength: float = 0.3
    min_amplitude_db: float = -60


class AudioPreprocessor:
    """
    Robust audio preprocessor for bird sound analysis.
    
    Designed to handle:
    - Feeble/distant bird calls
    - Noisy urban/natural environments
    - Multiple overlapping bird sounds
    - Various audio formats and quality levels
    """
    
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        
    def load_audio(
        self, 
        source: str | bytes | np.ndarray,
        target_sr: Optional[int] = None
    ) -> Tuple[np.ndarray, int]:
        """
        Load audio from file path, bytes, or numpy array.
        
        Args:
            source: File path, raw bytes, or numpy array
            target_sr: Target sample rate (uses config if None)
            
        Returns:
            Tuple of (audio_waveform, sample_rate)
        """
        target_sr = target_sr or self.config.sample_rate
        
        if isinstance(source, np.ndarray):
            # Already a numpy array
            audio = source
            sr = target_sr
        elif isinstance(source, bytes):
            # Load from bytes
            audio, sr = sf.read(io.BytesIO(source))
        else:
            # Load from file path
            audio, sr = librosa.load(source, sr=target_sr, mono=True)
            return audio, sr
            
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
            
        # Resample if needed
        if sr != target_sr:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
            
        return audio.astype(np.float32), sr
    
    def normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio amplitude.
        Handles feeble recordings by boosting low amplitude signals.
        """
        if len(audio) == 0:
            return audio
            
        # Peak normalization
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
            
        # Boost feeble audio (adaptive gain)
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < 0.1:  # Feeble recording detected
            target_rms = 0.2
            gain = target_rms / (rms + 1e-8)
            gain = min(gain, 10.0)  # Limit gain to avoid noise amplification
            audio = audio * gain
            
        return np.clip(audio, -1.0, 1.0)
    
    def reduce_noise(
        self, 
        audio: np.ndarray, 
        sr: int,
        strength: Optional[float] = None
    ) -> np.ndarray:
        """
        Apply spectral noise reduction.
        
        Uses spectral gating to reduce background noise while
        preserving bird call frequencies.
        """
        strength = strength or self.config.noise_reduction_strength
        
        if len(audio) < sr * 0.1:  # Too short
            return audio
            
        # Compute STFT
        stft = librosa.stft(audio, n_fft=self.config.n_fft, hop_length=self.config.hop_length)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise floor from quietest frames
        frame_energy = np.sum(magnitude ** 2, axis=0)
        noise_frames = frame_energy < np.percentile(frame_energy, 20)
        
        if np.sum(noise_frames) > 0:
            noise_profile = np.mean(magnitude[:, noise_frames], axis=1, keepdims=True)
        else:
            noise_profile = np.min(magnitude, axis=1, keepdims=True)
        
        # Spectral subtraction with oversubtraction factor
        alpha = 1.0 + strength
        magnitude_clean = magnitude - alpha * noise_profile
        magnitude_clean = np.maximum(magnitude_clean, magnitude * 0.1)  # Keep some residual
        
        # Reconstruct
        stft_clean = magnitude_clean * np.exp(1j * phase)
        audio_clean = librosa.istft(stft_clean, hop_length=self.config.hop_length, length=len(audio))
        
        return audio_clean.astype(np.float32)
    
    def apply_bandpass(
        self, 
        audio: np.ndarray, 
        sr: int,
        low_freq: Optional[int] = None,
        high_freq: Optional[int] = None
    ) -> np.ndarray:
        """
        Apply bandpass filter to focus on bird vocalization frequencies.
        Most bird calls are between 500Hz - 10kHz.
        """
        low_freq = low_freq or self.config.fmin
        high_freq = high_freq or min(self.config.fmax, sr // 2 - 100)
        
        nyquist = sr / 2
        low = low_freq / nyquist
        high = high_freq / nyquist
        
        # Butterworth bandpass filter
        b, a = signal.butter(4, [low, high], btype='band')
        audio_filtered = signal.filtfilt(b, a, audio)
        
        return audio_filtered.astype(np.float32)
    
    def compute_melspectrogram(
        self, 
        audio: np.ndarray, 
        sr: int
    ) -> np.ndarray:
        """
        Compute mel-spectrogram optimized for bird calls.
        
        Returns:
            Mel-spectrogram with shape (n_mels, time_frames)
        """
        mel_spec = librosa.feature.melspectrogram(
            y=audio,
            sr=sr,
            n_fft=self.config.n_fft,
            hop_length=self.config.hop_length,
            n_mels=self.config.n_mels,
            fmin=self.config.fmin,
            fmax=min(self.config.fmax, sr // 2)
        )
        
        # Convert to log scale (dB)
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        
        # Normalize to [0, 1] range for neural network input
        mel_spec_norm = (mel_spec_db - mel_spec_db.min()) / (mel_spec_db.max() - mel_spec_db.min() + 1e-8)
        
        return mel_spec_norm.astype(np.float32)
    
    def split_into_chunks(
        self, 
        audio: np.ndarray, 
        sr: int,
        overlap: float = 0.5
    ) -> List[np.ndarray]:
        """
        Split long audio into overlapping chunks for processing.
        
        Args:
            audio: Input audio waveform
            sr: Sample rate
            overlap: Overlap ratio between chunks (0.0 - 1.0)
            
        Returns:
            List of audio chunks
        """
        chunk_samples = int(self.config.duration * sr)
        hop_samples = int(chunk_samples * (1 - overlap))
        
        if len(audio) <= chunk_samples:
            # Pad short audio
            if len(audio) < chunk_samples:
                audio = np.pad(audio, (0, chunk_samples - len(audio)), mode='constant')
            return [audio]
        
        chunks = []
        start = 0
        while start < len(audio):
            end = start + chunk_samples
            chunk = audio[start:end]
            
            # Pad last chunk if needed
            if len(chunk) < chunk_samples:
                chunk = np.pad(chunk, (0, chunk_samples - len(chunk)), mode='constant')
                
            chunks.append(chunk)
            start += hop_samples
            
        return chunks
    
    def process(
        self, 
        source: str | bytes | np.ndarray,
        return_waveform: bool = False
    ) -> dict:
        """
        Full preprocessing pipeline.
        
        Args:
            source: Audio file path, bytes, or numpy array
            return_waveform: Include processed waveform in output
            
        Returns:
            Dictionary with processed audio data:
            - mel_specs: List of mel-spectrograms for each chunk
            - waveforms: List of audio chunks (if return_waveform=True)
            - duration: Total audio duration
            - sample_rate: Sample rate
            - num_chunks: Number of audio chunks
        """
        # Load audio
        audio, sr = self.load_audio(source)
        original_duration = len(audio) / sr
        
        # Apply bandpass filter
        audio = self.apply_bandpass(audio, sr)
        
        # Noise reduction (if enabled)
        if self.config.noise_reduction:
            audio = self.reduce_noise(audio, sr)
        
        # Normalize
        if self.config.normalize:
            audio = self.normalize_audio(audio)
        
        # Split into chunks
        chunks = self.split_into_chunks(audio, sr)
        
        # Compute mel-spectrograms
        mel_specs = [self.compute_melspectrogram(chunk, sr) for chunk in chunks]
        
        result = {
            "mel_specs": mel_specs,
            "duration": original_duration,
            "sample_rate": sr,
            "num_chunks": len(chunks),
            "chunk_duration": self.config.duration
        }
        
        if return_waveform:
            result["waveforms"] = chunks
            
        return result
    
    def get_audio_quality_assessment(self, audio: np.ndarray, sr: int) -> dict:
        """
        Assess audio quality for diagnostic purposes.
        
        Returns quality metrics useful for understanding
        why recognition might succeed or fail.
        """
        # RMS amplitude
        rms = np.sqrt(np.mean(audio ** 2))
        rms_db = 20 * np.log10(rms + 1e-8)
        
        # Peak amplitude
        peak = np.max(np.abs(audio))
        peak_db = 20 * np.log10(peak + 1e-8)
        
        # Signal-to-noise estimate (using spectral flatness)
        mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr)
        spectral_flatness = np.mean(librosa.feature.spectral_flatness(S=mel_spec))
        estimated_snr = -10 * np.log10(spectral_flatness + 1e-8)
        
        # Clipping detection
        clipping_ratio = np.mean(np.abs(audio) > 0.99)
        
        # Activity detection (voice activity equivalent for birds)
        frame_energy = librosa.feature.rms(y=audio)[0]
        activity_ratio = np.mean(frame_energy > np.percentile(frame_energy, 30))
        
        quality_score = min(1.0, max(0.0, 
            0.3 * (1 - clipping_ratio) +
            0.3 * min(1.0, estimated_snr / 20) +
            0.2 * min(1.0, (rms_db + 40) / 30) +
            0.2 * activity_ratio
        ))
        
        return {
            "rms_db": float(rms_db),
            "peak_db": float(peak_db),
            "estimated_snr_db": float(estimated_snr),
            "clipping_ratio": float(clipping_ratio),
            "activity_ratio": float(activity_ratio),
            "quality_score": float(quality_score),
            "quality_label": self._quality_label(quality_score)
        }
    
    def _quality_label(self, score: float) -> str:
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        elif score >= 0.2:
            return "poor"
        else:
            return "very_poor"

