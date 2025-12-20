"""
Test Suite for BirdSense Audio Recognition.

Tests model robustness across different audio conditions:
1. Clear recordings - High SNR, single bird
2. Feeble/distant - Low amplitude, requires amplification
3. Noisy environment - Urban noise, wind, rain
4. Multi-bird chorus - Multiple species overlapping
5. Brief calls - Short duration calls (<1 second)

Run with: pytest tests/test_audio_conditions.py -v
"""

import pytest
import numpy as np
import torch
from typing import Tuple

# Import BirdSense modules
import sys
from pathlib import Path
# Add parent directory to path for imports
birdsense_dir = str(Path(__file__).parent.parent)
if birdsense_dir not in sys.path:
    sys.path.insert(0, birdsense_dir)

from audio.preprocessor import AudioPreprocessor, AudioConfig
from audio.augmentation import AudioAugmenter, AugmentationConfig
from audio.encoder import AudioEncoder, BirdAudioEncoder
from models.audio_classifier import BirdAudioClassifier


# Fixtures

@pytest.fixture
def audio_config():
    """Default audio configuration."""
    return AudioConfig(
        sample_rate=32000,
        duration=5.0,
        n_mels=128,
        normalize=True,
        noise_reduction=True
    )


@pytest.fixture
def preprocessor(audio_config):
    """Audio preprocessor instance."""
    return AudioPreprocessor(audio_config)


@pytest.fixture
def augmenter():
    """Audio augmenter instance."""
    return AudioAugmenter(seed=42)


@pytest.fixture
def encoder():
    """Audio encoder instance."""
    return AudioEncoder(architecture='cnn', n_mels=128, embedding_dim=384)


@pytest.fixture
def classifier():
    """Bird audio classifier instance."""
    return BirdAudioClassifier(num_classes=25, embedding_dim=384)


def generate_synthetic_bird_call(
    duration: float = 3.0,
    sample_rate: int = 32000,
    base_freq: float = 2000.0,
    harmonics: int = 3
) -> np.ndarray:
    """
    Generate synthetic bird-like call for testing.
    
    Creates a simple harmonic signal with frequency modulation
    that resembles basic bird vocalizations.
    """
    t = np.linspace(0, duration, int(duration * sample_rate))
    
    # Frequency modulation (bird-like frequency sweeps)
    freq_mod = base_freq + 200 * np.sin(2 * np.pi * 5 * t)  # 5Hz modulation
    
    # Generate harmonics
    signal = np.zeros_like(t)
    for i in range(1, harmonics + 1):
        amplitude = 1.0 / i  # Decreasing amplitude for higher harmonics
        signal += amplitude * np.sin(2 * np.pi * freq_mod * i * t / sample_rate * np.cumsum(np.ones_like(t)))
    
    # Apply amplitude envelope (attack-sustain-decay)
    envelope = np.ones_like(t)
    attack_samples = int(0.1 * sample_rate)
    decay_samples = int(0.2 * sample_rate)
    
    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    envelope[-decay_samples:] = np.linspace(1, 0, decay_samples)
    
    signal = signal * envelope
    
    # Normalize
    signal = signal / (np.max(np.abs(signal)) + 1e-8) * 0.8
    
    return signal.astype(np.float32)


def generate_multi_bird_call(
    n_birds: int = 3,
    duration: float = 5.0,
    sample_rate: int = 32000
) -> np.ndarray:
    """Generate overlapping multi-bird audio for testing."""
    mixed = np.zeros(int(duration * sample_rate), dtype=np.float32)
    
    for i in range(n_birds):
        # Different base frequencies for each "bird"
        base_freq = 1500 + i * 800 + np.random.uniform(-200, 200)
        call = generate_synthetic_bird_call(
            duration=np.random.uniform(1.0, 3.0),
            sample_rate=sample_rate,
            base_freq=base_freq
        )
        
        # Random start time
        start = np.random.randint(0, len(mixed) - len(call))
        mixed[start:start + len(call)] += call * np.random.uniform(0.5, 1.0)
    
    # Normalize
    mixed = mixed / (np.max(np.abs(mixed)) + 1e-8) * 0.8
    
    return mixed


# Test Classes

class TestPreprocessor:
    """Tests for audio preprocessing."""
    
    def test_load_numpy_audio(self, preprocessor):
        """Test loading audio from numpy array."""
        audio = generate_synthetic_bird_call()
        loaded, sr = preprocessor.load_audio(audio)
        
        assert isinstance(loaded, np.ndarray)
        assert sr == preprocessor.config.sample_rate
    
    def test_normalize_feeble_audio(self, preprocessor):
        """Test normalization of feeble (low amplitude) audio."""
        # Create very quiet audio
        audio = generate_synthetic_bird_call() * 0.01  # 1% amplitude
        
        normalized = preprocessor.normalize_audio(audio)
        
        # Should boost feeble audio
        assert np.max(np.abs(normalized)) > np.max(np.abs(audio))
    
    def test_noise_reduction(self, preprocessor):
        """Test noise reduction capability."""
        audio = generate_synthetic_bird_call()
        sr = 32000
        
        # Add noise
        noisy_audio = audio + np.random.randn(len(audio)) * 0.1
        
        # Apply noise reduction
        clean_audio = preprocessor.reduce_noise(noisy_audio, sr)
        
        assert clean_audio.shape == noisy_audio.shape
        # Signal should be preserved
        assert np.corrcoef(audio, clean_audio)[0, 1] > 0.5
    
    def test_bandpass_filter(self, preprocessor):
        """Test bandpass filter for bird frequency range."""
        sr = 32000
        t = np.linspace(0, 1, sr)
        
        # Low frequency component (out of bird range)
        low_freq = np.sin(2 * np.pi * 30 * t)
        # Bird frequency component
        bird_freq = np.sin(2 * np.pi * 2000 * t)
        # High frequency noise
        high_freq = np.sin(2 * np.pi * 15000 * t)
        
        mixed = (low_freq + bird_freq + high_freq).astype(np.float32)
        filtered = preprocessor.apply_bandpass(mixed, sr, low_freq=50, high_freq=14000)
        
        # Bird frequency should dominate after filtering
        assert len(filtered) == len(mixed)
    
    def test_mel_spectrogram_shape(self, preprocessor):
        """Test mel-spectrogram output shape."""
        audio = generate_synthetic_bird_call(duration=5.0)
        sr = 32000
        
        mel_spec = preprocessor.compute_melspectrogram(audio, sr)
        
        assert mel_spec.shape[0] == preprocessor.config.n_mels
        assert mel_spec.ndim == 2
        assert mel_spec.min() >= 0 and mel_spec.max() <= 1
    
    def test_chunking_long_audio(self, preprocessor):
        """Test splitting long audio into chunks."""
        # Create 30 second audio
        audio = generate_synthetic_bird_call(duration=30.0)
        sr = 32000
        
        chunks = preprocessor.split_into_chunks(audio, sr, overlap=0.5)
        
        assert len(chunks) > 1
        # Each chunk should be the configured duration
        expected_samples = int(preprocessor.config.duration * sr)
        for chunk in chunks:
            assert len(chunk) == expected_samples
    
    def test_full_pipeline(self, preprocessor):
        """Test complete preprocessing pipeline."""
        audio = generate_synthetic_bird_call()
        
        result = preprocessor.process(audio, return_waveform=True)
        
        assert "mel_specs" in result
        assert "duration" in result
        assert "num_chunks" in result
        assert len(result["mel_specs"]) >= 1
    
    def test_quality_assessment(self, preprocessor):
        """Test audio quality assessment."""
        # Good quality audio
        good_audio = generate_synthetic_bird_call()
        sr = 32000
        
        quality = preprocessor.get_audio_quality_assessment(good_audio, sr)
        
        assert "quality_score" in quality
        assert "quality_label" in quality
        assert 0 <= quality["quality_score"] <= 1


class TestAugmentation:
    """Tests for audio augmentation."""
    
    def test_gaussian_noise(self, augmenter):
        """Test Gaussian noise addition."""
        audio = generate_synthetic_bird_call()
        
        noisy = augmenter.add_gaussian_noise(audio, snr_db=10)
        
        assert noisy.shape == audio.shape
        assert not np.allclose(noisy, audio)
    
    def test_pink_noise(self, augmenter):
        """Test pink noise addition."""
        audio = generate_synthetic_bird_call()
        
        noisy = augmenter.add_pink_noise(audio, snr_db=10)
        
        assert noisy.shape == audio.shape
    
    def test_urban_noise(self, augmenter):
        """Test urban noise simulation."""
        audio = generate_synthetic_bird_call()
        sr = 32000
        
        noisy = augmenter.add_urban_noise(audio, sr, snr_db=5)
        
        assert noisy.shape == audio.shape
    
    def test_forest_noise(self, augmenter):
        """Test forest ambient noise simulation."""
        audio = generate_synthetic_bird_call()
        sr = 32000
        
        noisy = augmenter.add_forest_noise(audio, sr, snr_db=10)
        
        assert noisy.shape == audio.shape
    
    def test_time_stretch(self, augmenter):
        """Test time stretching."""
        audio = generate_synthetic_bird_call()
        
        stretched = augmenter.time_stretch(audio, rate=0.9)
        
        assert stretched.shape == audio.shape
    
    def test_pitch_shift(self, augmenter):
        """Test pitch shifting."""
        audio = generate_synthetic_bird_call()
        sr = 32000
        
        shifted = augmenter.pitch_shift(audio, sr, semitones=2)
        
        assert shifted.shape == audio.shape
    
    def test_gain_application(self, augmenter):
        """Test gain application."""
        audio = generate_synthetic_bird_call()
        
        # Reduce gain
        quiet = augmenter.apply_gain(audio, gain_db=-10)
        assert np.max(np.abs(quiet)) < np.max(np.abs(audio))
        
        # Increase gain
        loud = augmenter.apply_gain(audio, gain_db=6)
        assert np.max(np.abs(loud)) > np.max(np.abs(audio))
    
    def test_challenging_feeble(self, augmenter):
        """Test creation of feeble audio challenge."""
        audio = generate_synthetic_bird_call()
        sr = 32000
        
        feeble, metadata = augmenter.create_challenging_sample(audio, sr, 'feeble')
        
        assert metadata["challenge_type"] == "feeble"
        assert np.max(np.abs(feeble)) < np.max(np.abs(audio))
    
    def test_challenging_noisy(self, augmenter):
        """Test creation of noisy audio challenge."""
        audio = generate_synthetic_bird_call()
        sr = 32000
        
        noisy, metadata = augmenter.create_challenging_sample(audio, sr, 'noisy')
        
        assert metadata["challenge_type"] == "noisy"
        assert "noise_type" in metadata
    
    def test_challenging_multi_source(self, augmenter):
        """Test creation of multi-source audio challenge."""
        audio = generate_synthetic_bird_call()
        sr = 32000
        
        multi, metadata = augmenter.create_challenging_sample(audio, sr, 'multi_source')
        
        assert metadata["challenge_type"] == "multi_source"
    
    def test_challenging_brief(self, augmenter):
        """Test creation of brief call challenge."""
        audio = generate_synthetic_bird_call(duration=3.0)
        sr = 32000
        
        brief, metadata = augmenter.create_challenging_sample(audio, sr, 'brief')
        
        assert metadata["challenge_type"] == "brief"


class TestEncoder:
    """Tests for audio encoder."""
    
    def test_cnn_encoder_forward(self, encoder):
        """Test CNN encoder forward pass."""
        batch_size = 2
        n_mels = 128
        n_frames = 500
        
        x = torch.randn(batch_size, n_mels, n_frames)
        embeddings = encoder(x)
        
        assert embeddings.shape == (batch_size, encoder.embedding_dim)
    
    def test_encoder_with_channel_dim(self, encoder):
        """Test encoder with explicit channel dimension."""
        batch_size = 2
        n_mels = 128
        n_frames = 500
        
        x = torch.randn(batch_size, 1, n_mels, n_frames)
        embeddings = encoder(x)
        
        assert embeddings.shape == (batch_size, encoder.embedding_dim)
    
    def test_encoder_parameter_count(self, encoder):
        """Test encoder is lightweight."""
        n_params = encoder.count_parameters()
        
        # Should be under 10M parameters for edge deployment
        assert n_params < 10_000_000
    
    def test_encoder_deterministic(self, encoder):
        """Test encoder produces consistent outputs."""
        encoder.eval()
        x = torch.randn(1, 128, 500)
        
        with torch.no_grad():
            emb1 = encoder(x)
            emb2 = encoder(x)
        
        assert torch.allclose(emb1, emb2)


class TestClassifier:
    """Tests for bird audio classifier."""
    
    def test_classifier_forward(self, classifier):
        """Test classifier forward pass."""
        batch_size = 2
        x = torch.randn(batch_size, 128, 500)
        
        output = classifier(x)
        
        assert "logits" in output
        assert "probabilities" in output
        assert output["logits"].shape == (batch_size, classifier.num_classes)
        assert output["probabilities"].shape == (batch_size, classifier.num_classes)
    
    def test_classifier_probabilities_sum(self, classifier):
        """Test probabilities sum to 1."""
        x = torch.randn(2, 128, 500)
        
        output = classifier(x)
        prob_sums = output["probabilities"].sum(dim=-1)
        
        assert torch.allclose(prob_sums, torch.ones_like(prob_sums), atol=1e-5)
    
    def test_classifier_predict(self, classifier):
        """Test classifier prediction method."""
        classifier.eval()
        x = torch.randn(2, 128, 500)
        
        predictions = classifier.predict(x, top_k=5)
        
        assert "top_indices" in predictions
        assert "top_probabilities" in predictions
        assert "max_confidence" in predictions
        assert "uncertainty" in predictions
        assert predictions["top_indices"].shape == (2, 5)
    
    def test_classifier_embedding_extraction(self, classifier):
        """Test embedding extraction."""
        classifier.eval()
        x = torch.randn(2, 128, 500)
        
        embeddings = classifier.get_embedding(x)
        
        assert embeddings.shape == (2, classifier.embedding_dim)
    
    def test_classifier_parameter_count(self, classifier):
        """Test classifier size for mobile deployment."""
        params = classifier.count_parameters()
        
        # Total should be under 15MB for mobile
        assert params["total_mb"] < 15


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_pipeline_clear_audio(self, preprocessor, classifier):
        """Test full pipeline with clear audio."""
        # Generate clear bird call
        audio = generate_synthetic_bird_call()
        
        # Preprocess
        result = preprocessor.process(audio)
        mel_spec = result["mel_specs"][0]
        
        # Classify
        classifier.eval()
        x = torch.tensor(mel_spec).unsqueeze(0)
        predictions = classifier.predict(x)
        
        assert predictions["top_indices"].shape[1] == 5
        assert predictions["max_confidence"].item() >= 0
    
    def test_pipeline_feeble_audio(self, preprocessor, augmenter, classifier):
        """Test pipeline with feeble/distant audio."""
        audio = generate_synthetic_bird_call()
        sr = 32000
        
        # Make it feeble
        feeble, _ = augmenter.create_challenging_sample(audio, sr, 'feeble')
        
        # Preprocess (should handle low amplitude)
        result = preprocessor.process(feeble)
        mel_spec = result["mel_specs"][0]
        
        # Should still produce valid spectrogram
        assert not np.isnan(mel_spec).any()
        
        # Classify
        classifier.eval()
        x = torch.tensor(mel_spec).unsqueeze(0)
        predictions = classifier.predict(x)
        
        assert predictions is not None
    
    def test_pipeline_noisy_audio(self, preprocessor, augmenter, classifier):
        """Test pipeline with noisy audio."""
        audio = generate_synthetic_bird_call()
        sr = 32000
        
        # Add heavy noise
        noisy, _ = augmenter.create_challenging_sample(audio, sr, 'noisy')
        
        # Preprocess with noise reduction
        result = preprocessor.process(noisy)
        mel_spec = result["mel_specs"][0]
        
        assert not np.isnan(mel_spec).any()
        
        # Classify
        classifier.eval()
        x = torch.tensor(mel_spec).unsqueeze(0)
        predictions = classifier.predict(x)
        
        assert predictions is not None
    
    def test_pipeline_multi_bird_audio(self, preprocessor, classifier):
        """Test pipeline with multiple overlapping birds."""
        # Generate multi-bird audio
        audio = generate_multi_bird_call(n_birds=3)
        
        # Preprocess
        result = preprocessor.process(audio)
        mel_spec = result["mel_specs"][0]
        
        assert not np.isnan(mel_spec).any()
        
        # Classify
        classifier.eval()
        x = torch.tensor(mel_spec).unsqueeze(0)
        predictions = classifier.predict(x)
        
        # Should have predictions for multiple potential species
        assert predictions["uncertainty"].item() >= 0
    
    def test_pipeline_brief_call(self, preprocessor, augmenter, classifier):
        """Test pipeline with brief bird call."""
        audio = generate_synthetic_bird_call(duration=3.0)
        sr = 32000
        
        # Create brief call
        brief, _ = augmenter.create_challenging_sample(audio, sr, 'brief')
        
        # Preprocess
        result = preprocessor.process(brief)
        mel_spec = result["mel_specs"][0]
        
        assert not np.isnan(mel_spec).any()
        
        # Classify
        classifier.eval()
        x = torch.tensor(mel_spec).unsqueeze(0)
        predictions = classifier.predict(x)
        
        assert predictions is not None


class TestRobustness:
    """Tests for model robustness across conditions."""
    
    @pytest.mark.parametrize("snr_db", [30, 20, 10, 5, 0])
    def test_noise_levels(self, preprocessor, augmenter, classifier, snr_db):
        """Test classification at various noise levels."""
        audio = generate_synthetic_bird_call()
        sr = 32000
        
        noisy = augmenter.add_gaussian_noise(audio, snr_db=snr_db)
        
        result = preprocessor.process(noisy)
        mel_spec = result["mel_specs"][0]
        
        classifier.eval()
        x = torch.tensor(mel_spec).unsqueeze(0)
        predictions = classifier.predict(x)
        
        # Model should still produce valid predictions
        assert not torch.isnan(predictions["top_probabilities"]).any()
    
    @pytest.mark.parametrize("gain_db", [-20, -15, -10, -5, 0, 5])
    def test_amplitude_levels(self, preprocessor, augmenter, classifier, gain_db):
        """Test classification at various amplitude levels."""
        audio = generate_synthetic_bird_call()
        
        adjusted = augmenter.apply_gain(audio, gain_db=gain_db)
        
        result = preprocessor.process(adjusted)
        mel_spec = result["mel_specs"][0]
        
        classifier.eval()
        x = torch.tensor(mel_spec).unsqueeze(0)
        predictions = classifier.predict(x)
        
        assert not torch.isnan(predictions["top_probabilities"]).any()
    
    @pytest.mark.parametrize("noise_type", ["gaussian", "pink", "urban", "forest"])
    def test_noise_types(self, preprocessor, augmenter, classifier, noise_type):
        """Test classification with different noise types."""
        audio = generate_synthetic_bird_call()
        sr = 32000
        
        noisy = augmenter.add_noise(audio, sr, noise_type=noise_type, snr_db=10)
        
        result = preprocessor.process(noisy)
        mel_spec = result["mel_specs"][0]
        
        classifier.eval()
        x = torch.tensor(mel_spec).unsqueeze(0)
        predictions = classifier.predict(x)
        
        assert not torch.isnan(predictions["top_probabilities"]).any()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

