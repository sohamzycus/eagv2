"""
Audio Augmentation for BirdSense.

Provides augmentation techniques to make the model robust to:
- Different noise conditions (urban, forest, rain, wind)
- Recording quality variations
- Distance/amplitude variations
- Pitch variations (natural variation in bird calls)
"""

import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass
import random


@dataclass
class AugmentationConfig:
    """Configuration for audio augmentation."""
    # Noise injection
    add_noise: bool = True
    noise_types: List[str] = None  # 'gaussian', 'pink', 'urban', 'forest'
    min_snr_db: float = 3.0
    max_snr_db: float = 30.0
    
    # Time stretching
    time_stretch: bool = True
    min_stretch_rate: float = 0.8
    max_stretch_rate: float = 1.2
    
    # Pitch shifting
    pitch_shift: bool = True
    min_semitones: float = -2.0
    max_semitones: float = 2.0
    
    # Amplitude variation
    amplitude_variation: bool = True
    min_gain_db: float = -12.0
    max_gain_db: float = 6.0
    
    # Time masking (simulate brief interruptions)
    time_mask: bool = True
    max_mask_ratio: float = 0.1
    
    # Frequency masking (simulate frequency-specific noise)
    freq_mask: bool = True
    max_freq_mask_bins: int = 20
    
    def __post_init__(self):
        if self.noise_types is None:
            self.noise_types = ['gaussian', 'pink', 'urban', 'forest']


class AudioAugmenter:
    """
    Audio augmentation pipeline for training robust bird classifiers.
    
    Simulates real-world recording conditions including:
    - Environmental noise (traffic, wind, rain, other birds)
    - Recording equipment variations
    - Distance variations (feeble vs. close recordings)
    """
    
    def __init__(self, config: Optional[AugmentationConfig] = None, seed: Optional[int] = None):
        self.config = config or AugmentationConfig()
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
    
    def add_gaussian_noise(
        self, 
        audio: np.ndarray, 
        snr_db: float
    ) -> np.ndarray:
        """Add Gaussian white noise at specified SNR."""
        signal_power = np.mean(audio ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), len(audio))
        return (audio + noise).astype(np.float32)
    
    def add_pink_noise(
        self, 
        audio: np.ndarray, 
        snr_db: float
    ) -> np.ndarray:
        """
        Add pink (1/f) noise - more natural sounding than white noise.
        Common in environmental recordings.
        """
        n_samples = len(audio)
        
        # Generate pink noise using spectral shaping
        # Generate white noise
        white = np.random.randn(n_samples)
        
        # Apply 1/f filter in frequency domain
        fft = np.fft.rfft(white)
        freqs = np.fft.rfftfreq(n_samples)
        freqs[0] = 1e-10  # Avoid division by zero
        
        # Pink noise has 1/f power spectrum, so 1/sqrt(f) amplitude
        pink_filter = 1.0 / np.sqrt(freqs + 1e-10)
        pink_filter = pink_filter / np.max(pink_filter)
        
        pink = np.fft.irfft(fft * pink_filter, n=n_samples)
        pink = pink - np.mean(pink)
        pink = pink / (np.max(np.abs(pink)) + 1e-8)
        
        # Scale to desired SNR
        signal_power = np.mean(audio ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        pink = pink * np.sqrt(noise_power)
        
        return (audio + pink).astype(np.float32)
    
    def add_urban_noise(
        self, 
        audio: np.ndarray, 
        sr: int,
        snr_db: float
    ) -> np.ndarray:
        """
        Simulate urban noise (low-frequency rumble + occasional spikes).
        Models traffic, construction, and city ambience.
        """
        n_samples = len(audio)
        
        # Low-frequency rumble (traffic)
        t = np.arange(n_samples) / sr
        rumble = np.sin(2 * np.pi * 50 * t) * 0.5 + np.sin(2 * np.pi * 100 * t) * 0.3
        rumble += np.random.randn(n_samples) * 0.2
        
        # Occasional impulses (cars passing, doors)
        n_impulses = random.randint(2, 8)
        for _ in range(n_impulses):
            pos = random.randint(0, n_samples - 100)
            impulse_len = random.randint(50, 200)
            decay = np.exp(-np.arange(impulse_len) / (impulse_len * 0.3))
            impulse = np.random.randn(impulse_len) * decay
            rumble[pos:pos + impulse_len] += impulse * random.uniform(0.5, 2.0)
        
        rumble = rumble / (np.max(np.abs(rumble)) + 1e-8)
        
        # Scale to desired SNR
        signal_power = np.mean(audio ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        rumble = rumble * np.sqrt(noise_power)
        
        return (audio + rumble).astype(np.float32)
    
    def add_forest_noise(
        self, 
        audio: np.ndarray, 
        sr: int,
        snr_db: float
    ) -> np.ndarray:
        """
        Simulate forest ambient noise (insects, wind in leaves, water).
        """
        n_samples = len(audio)
        
        # Base: filtered noise (wind through leaves)
        wind = np.random.randn(n_samples)
        # Apply bandpass to simulate rustling (200-4000 Hz)
        from scipy import signal as sig
        nyquist = sr / 2
        b, a = sig.butter(2, [200 / nyquist, 4000 / nyquist], btype='band')
        wind = sig.filtfilt(b, a, wind)
        
        # Add modulation (gusts)
        t = np.arange(n_samples) / sr
        modulation = 0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t + random.random() * 2 * np.pi)
        wind = wind * modulation
        
        # Add some insect-like chirps (high frequency components)
        insect_freq = random.uniform(4000, 8000)
        insect = np.sin(2 * np.pi * insect_freq * t) * 0.1
        insect_modulation = np.random.rand(n_samples) > 0.7
        insect = insect * insect_modulation.astype(float)
        
        forest = wind * 0.8 + insect * 0.2
        forest = forest / (np.max(np.abs(forest)) + 1e-8)
        
        # Scale to desired SNR
        signal_power = np.mean(audio ** 2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        forest = forest * np.sqrt(noise_power)
        
        return (audio + forest).astype(np.float32)
    
    def add_noise(
        self, 
        audio: np.ndarray, 
        sr: int,
        noise_type: Optional[str] = None,
        snr_db: Optional[float] = None
    ) -> np.ndarray:
        """
        Add noise of specified type at random SNR.
        """
        if snr_db is None:
            snr_db = random.uniform(self.config.min_snr_db, self.config.max_snr_db)
        
        if noise_type is None:
            noise_type = random.choice(self.config.noise_types)
        
        if noise_type == 'gaussian':
            return self.add_gaussian_noise(audio, snr_db)
        elif noise_type == 'pink':
            return self.add_pink_noise(audio, snr_db)
        elif noise_type == 'urban':
            return self.add_urban_noise(audio, sr, snr_db)
        elif noise_type == 'forest':
            return self.add_forest_noise(audio, sr, snr_db)
        else:
            return self.add_gaussian_noise(audio, snr_db)
    
    def time_stretch(
        self, 
        audio: np.ndarray, 
        rate: Optional[float] = None
    ) -> np.ndarray:
        """
        Time-stretch audio without changing pitch.
        Uses simple resampling for efficiency.
        """
        if rate is None:
            rate = random.uniform(
                self.config.min_stretch_rate, 
                self.config.max_stretch_rate
            )
        
        # Simple linear interpolation stretching
        original_len = len(audio)
        new_len = int(original_len / rate)
        
        x_old = np.linspace(0, 1, original_len)
        x_new = np.linspace(0, 1, new_len)
        
        stretched = np.interp(x_new, x_old, audio)
        
        # Adjust to original length
        if len(stretched) > original_len:
            stretched = stretched[:original_len]
        elif len(stretched) < original_len:
            stretched = np.pad(stretched, (0, original_len - len(stretched)), mode='constant')
        
        return stretched.astype(np.float32)
    
    def pitch_shift(
        self, 
        audio: np.ndarray, 
        sr: int,
        semitones: Optional[float] = None
    ) -> np.ndarray:
        """
        Shift pitch by specified semitones.
        Simplified implementation using resampling.
        """
        if semitones is None:
            semitones = random.uniform(
                self.config.min_semitones, 
                self.config.max_semitones
            )
        
        # Pitch shift factor
        factor = 2 ** (semitones / 12.0)
        
        # Resample then time-stretch back
        original_len = len(audio)
        new_len = int(original_len / factor)
        
        # First resample to change pitch
        x_old = np.linspace(0, 1, original_len)
        x_new = np.linspace(0, 1, new_len)
        resampled = np.interp(x_new, x_old, audio)
        
        # Then stretch back to original length
        x_stretch = np.linspace(0, 1, len(resampled))
        x_target = np.linspace(0, 1, original_len)
        shifted = np.interp(x_target, x_stretch, resampled)
        
        return shifted.astype(np.float32)
    
    def apply_gain(
        self, 
        audio: np.ndarray, 
        gain_db: Optional[float] = None
    ) -> np.ndarray:
        """
        Apply gain to simulate distance/recording level variations.
        """
        if gain_db is None:
            gain_db = random.uniform(
                self.config.min_gain_db, 
                self.config.max_gain_db
            )
        
        gain_linear = 10 ** (gain_db / 20)
        audio = audio * gain_linear
        
        # Soft clip to avoid harsh distortion
        return np.tanh(audio).astype(np.float32)
    
    def time_mask(
        self, 
        spectrogram: np.ndarray
    ) -> np.ndarray:
        """
        Apply time masking to spectrogram (SpecAugment technique).
        """
        n_mels, n_frames = spectrogram.shape
        max_mask_width = int(n_frames * self.config.max_mask_ratio)
        
        if max_mask_width < 2:
            return spectrogram
        
        mask_width = random.randint(1, max_mask_width)
        mask_start = random.randint(0, n_frames - mask_width)
        
        masked = spectrogram.copy()
        masked[:, mask_start:mask_start + mask_width] = 0
        
        return masked
    
    def freq_mask(
        self, 
        spectrogram: np.ndarray
    ) -> np.ndarray:
        """
        Apply frequency masking to spectrogram (SpecAugment technique).
        """
        n_mels, n_frames = spectrogram.shape
        max_mask_bins = min(self.config.max_freq_mask_bins, n_mels // 4)
        
        if max_mask_bins < 2:
            return spectrogram
        
        mask_bins = random.randint(1, max_mask_bins)
        mask_start = random.randint(0, n_mels - mask_bins)
        
        masked = spectrogram.copy()
        masked[mask_start:mask_start + mask_bins, :] = 0
        
        return masked
    
    def augment_audio(
        self, 
        audio: np.ndarray, 
        sr: int,
        augmentations: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        Apply a random subset of augmentations to audio.
        
        Args:
            audio: Input audio waveform
            sr: Sample rate
            augmentations: List of augmentations to apply, or None for random
            
        Returns:
            Augmented audio
        """
        if augmentations is None:
            # Randomly select augmentations
            augmentations = []
            if self.config.add_noise and random.random() < 0.7:
                augmentations.append('noise')
            if self.config.time_stretch and random.random() < 0.3:
                augmentations.append('time_stretch')
            if self.config.pitch_shift and random.random() < 0.3:
                augmentations.append('pitch_shift')
            if self.config.amplitude_variation and random.random() < 0.5:
                augmentations.append('gain')
        
        augmented = audio.copy()
        
        for aug in augmentations:
            if aug == 'noise':
                augmented = self.add_noise(augmented, sr)
            elif aug == 'time_stretch':
                augmented = self.time_stretch(augmented)
            elif aug == 'pitch_shift':
                augmented = self.pitch_shift(augmented, sr)
            elif aug == 'gain':
                augmented = self.apply_gain(augmented)
        
        return augmented
    
    def augment_spectrogram(
        self, 
        spectrogram: np.ndarray
    ) -> np.ndarray:
        """
        Apply SpecAugment-style augmentations to mel-spectrogram.
        """
        augmented = spectrogram.copy()
        
        if self.config.time_mask and random.random() < 0.5:
            augmented = self.time_mask(augmented)
        
        if self.config.freq_mask and random.random() < 0.5:
            augmented = self.freq_mask(augmented)
        
        return augmented
    
    def create_challenging_sample(
        self, 
        audio: np.ndarray, 
        sr: int,
        challenge_type: str
    ) -> Tuple[np.ndarray, dict]:
        """
        Create specifically challenging audio samples for testing.
        
        Args:
            audio: Clean audio sample
            sr: Sample rate
            challenge_type: One of 'feeble', 'noisy', 'multi_source', 'brief'
            
        Returns:
            Tuple of (augmented_audio, metadata)
        """
        metadata = {"challenge_type": challenge_type}
        
        if challenge_type == 'feeble':
            # Simulate distant/quiet recording
            gain_db = random.uniform(-20, -10)
            audio = self.apply_gain(audio, gain_db)
            audio = self.add_noise(audio, sr, 'pink', snr_db=random.uniform(5, 10))
            metadata['gain_db'] = gain_db
            
        elif challenge_type == 'noisy':
            # Heavy noise contamination
            noise_type = random.choice(['urban', 'forest'])
            snr_db = random.uniform(0, 5)
            audio = self.add_noise(audio, sr, noise_type, snr_db)
            metadata['noise_type'] = noise_type
            metadata['snr_db'] = snr_db
            
        elif challenge_type == 'multi_source':
            # Simulate multiple overlapping sounds (mix with shifted copy)
            shifted = self.pitch_shift(audio, sr, random.uniform(-3, 3))
            delay_samples = random.randint(0, len(audio) // 4)
            delayed = np.roll(shifted, delay_samples)
            audio = audio * 0.7 + delayed * 0.5
            audio = self.add_noise(audio, sr, snr_db=random.uniform(10, 20))
            metadata['n_sources'] = 2
            
        elif challenge_type == 'brief':
            # Very short call with silence padding
            call_duration = random.uniform(0.3, 1.0)
            call_samples = int(call_duration * sr)
            if call_samples < len(audio):
                start = random.randint(0, len(audio) - call_samples)
                brief = np.zeros_like(audio)
                insert_pos = random.randint(0, len(audio) - call_samples)
                brief[insert_pos:insert_pos + call_samples] = audio[start:start + call_samples]
                audio = brief
                audio = self.add_noise(audio, sr, snr_db=random.uniform(10, 20))
                metadata['call_duration'] = call_duration
        
        return audio.astype(np.float32), metadata

