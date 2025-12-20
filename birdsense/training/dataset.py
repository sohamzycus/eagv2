"""
Bird Audio Dataset for Training.

Handles loading, augmentation, and batching of
bird audio recordings for model training.
"""

import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Callable
import json
import random
import logging

try:
    from ..audio.preprocessor import AudioPreprocessor, AudioConfig
    from ..audio.augmentation import AudioAugmenter, AugmentationConfig
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from audio.preprocessor import AudioPreprocessor, AudioConfig
    from audio.augmentation import AudioAugmenter, AugmentationConfig

logger = logging.getLogger(__name__)


class BirdAudioDataset(Dataset):
    """
    PyTorch Dataset for bird audio recordings.
    
    Features:
    - Loads audio from downloaded Xeno-Canto data
    - Real-time augmentation during training
    - Quality-based sampling weights
    - Efficient caching of spectrograms
    """
    
    def __init__(
        self,
        data_dir: str,
        species_list: Optional[List[str]] = None,
        split: str = "train",  # train, val, test
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        augment: bool = True,
        cache_spectrograms: bool = True,
        max_samples_per_species: Optional[int] = None,
        seed: int = 42
    ):
        """
        Initialize dataset.
        
        Args:
            data_dir: Directory with downloaded Xeno-Canto data
            species_list: List of species to include (None = all)
            split: Data split
            train_ratio: Ratio for training set
            val_ratio: Ratio for validation set
            augment: Whether to apply augmentation
            cache_spectrograms: Cache computed spectrograms
            max_samples_per_species: Limit samples per species
            seed: Random seed for reproducibility
        """
        self.data_dir = Path(data_dir)
        self.split = split
        self.augment = augment and split == "train"
        self.cache_spectrograms = cache_spectrograms
        
        # Initialize processors
        self.preprocessor = AudioPreprocessor()
        self.augmenter = AudioAugmenter(seed=seed) if self.augment else None
        
        # Load metadata
        metadata_path = self.data_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
        
        # Discover species and files
        self.species_to_idx: Dict[str, int] = {}
        self.idx_to_species: Dict[int, str] = {}
        self.samples: List[Dict] = []
        
        self._discover_files(species_list, max_samples_per_species)
        self._create_split(train_ratio, val_ratio, seed)
        
        # Spectrogram cache
        self.cache: Dict[str, np.ndarray] = {} if cache_spectrograms else None
        
        logger.info(
            f"Dataset initialized: {len(self.samples)} samples, "
            f"{len(self.species_to_idx)} species, split={split}"
        )
    
    def _discover_files(
        self,
        species_list: Optional[List[str]],
        max_samples: Optional[int]
    ):
        """Discover audio files in data directory."""
        species_dirs = sorted(self.data_dir.iterdir())
        
        for idx, species_dir in enumerate(species_dirs):
            if not species_dir.is_dir():
                continue
            
            species_name = species_dir.name.replace("_", " ")
            
            # Filter species if list provided
            if species_list and species_name not in species_list:
                continue
            
            self.species_to_idx[species_name] = idx
            self.idx_to_species[idx] = species_name
            
            # Find audio files
            audio_files = list(species_dir.glob("*.mp3")) + list(species_dir.glob("*.wav"))
            
            # Get metadata for quality-based sampling
            species_meta = self.metadata.get(species_name, [])
            meta_by_id = {m['id']: m for m in species_meta}
            
            # Limit samples if needed
            if max_samples and len(audio_files) > max_samples:
                # Prefer high-quality recordings
                scored_files = []
                for f in audio_files:
                    file_id = f.stem
                    meta = meta_by_id.get(file_id, {})
                    quality = meta.get('quality', 'E')
                    quality_score = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'E': 0}.get(quality, 0)
                    scored_files.append((f, quality_score))
                
                scored_files.sort(key=lambda x: x[1], reverse=True)
                audio_files = [f for f, _ in scored_files[:max_samples]]
            
            for audio_file in audio_files:
                file_id = audio_file.stem
                meta = meta_by_id.get(file_id, {})
                
                self.samples.append({
                    'path': audio_file,
                    'species': species_name,
                    'label': idx,
                    'quality': meta.get('quality', 'E'),
                    'location': meta.get('location', ''),
                    'latitude': meta.get('latitude'),
                    'longitude': meta.get('longitude')
                })
    
    def _create_split(
        self,
        train_ratio: float,
        val_ratio: float,
        seed: int
    ):
        """Split data into train/val/test sets."""
        random.seed(seed)
        
        # Group by species for stratified split
        by_species: Dict[int, List[Dict]] = {}
        for sample in self.samples:
            label = sample['label']
            if label not in by_species:
                by_species[label] = []
            by_species[label].append(sample)
        
        train_samples = []
        val_samples = []
        test_samples = []
        
        for label, species_samples in by_species.items():
            random.shuffle(species_samples)
            n = len(species_samples)
            
            n_train = int(n * train_ratio)
            n_val = int(n * val_ratio)
            
            train_samples.extend(species_samples[:n_train])
            val_samples.extend(species_samples[n_train:n_train + n_val])
            test_samples.extend(species_samples[n_train + n_val:])
        
        if self.split == "train":
            self.samples = train_samples
        elif self.split == "val":
            self.samples = val_samples
        else:
            self.samples = test_samples
        
        random.shuffle(self.samples)
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """
        Get a single sample.
        
        Returns:
            Tuple of (mel_spectrogram, label)
        """
        sample = self.samples[idx]
        path = sample['path']
        label = sample['label']
        
        # Check cache
        cache_key = str(path)
        if self.cache is not None and cache_key in self.cache:
            mel_spec = self.cache[cache_key].copy()
        else:
            # Load and preprocess
            try:
                result = self.preprocessor.process(str(path))
                mel_spec = result['mel_specs'][0]  # Use first chunk
                
                # Cache if enabled
                if self.cache is not None:
                    self.cache[cache_key] = mel_spec.copy()
                    
            except Exception as e:
                logger.warning(f"Error loading {path}: {e}")
                # Return zero spectrogram on error
                mel_spec = np.zeros((128, 500), dtype=np.float32)
        
        # Apply augmentation
        if self.augment and self.augmenter:
            mel_spec = self.augmenter.augment_spectrogram(mel_spec)
        
        # Ensure consistent size
        target_frames = 500
        if mel_spec.shape[1] < target_frames:
            # Pad
            pad_width = target_frames - mel_spec.shape[1]
            mel_spec = np.pad(mel_spec, ((0, 0), (0, pad_width)), mode='constant')
        elif mel_spec.shape[1] > target_frames:
            # Crop
            mel_spec = mel_spec[:, :target_frames]
        
        return torch.tensor(mel_spec, dtype=torch.float32), label
    
    def get_num_classes(self) -> int:
        """Get number of species classes."""
        return len(self.species_to_idx)
    
    def get_class_names(self) -> List[str]:
        """Get ordered list of species names."""
        return [self.idx_to_species[i] for i in range(len(self.idx_to_species))]
    
    def get_sample_weights(self) -> torch.Tensor:
        """
        Get sample weights for balanced sampling.
        
        Returns weights inversely proportional to class frequency.
        """
        class_counts = {}
        for sample in self.samples:
            label = sample['label']
            class_counts[label] = class_counts.get(label, 0) + 1
        
        weights = []
        for sample in self.samples:
            label = sample['label']
            weight = 1.0 / class_counts[label]
            
            # Boost high-quality samples
            quality = sample.get('quality', 'E')
            quality_boost = {'A': 2.0, 'B': 1.5, 'C': 1.2, 'D': 1.0, 'E': 0.8}
            weight *= quality_boost.get(quality, 1.0)
            
            weights.append(weight)
        
        return torch.tensor(weights, dtype=torch.float32)


def create_dataloaders(
    data_dir: str,
    batch_size: int = 32,
    num_workers: int = 4,
    species_list: Optional[List[str]] = None,
    max_samples_per_species: Optional[int] = None
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Create train, validation, and test dataloaders.
    
    Args:
        data_dir: Path to data directory
        batch_size: Batch size
        num_workers: Number of data loading workers
        species_list: Species to include
        max_samples_per_species: Limit per species
        
    Returns:
        Tuple of (train_loader, val_loader, test_loader)
    """
    train_dataset = BirdAudioDataset(
        data_dir=data_dir,
        species_list=species_list,
        split="train",
        augment=True,
        max_samples_per_species=max_samples_per_species
    )
    
    val_dataset = BirdAudioDataset(
        data_dir=data_dir,
        species_list=species_list,
        split="val",
        augment=False,
        max_samples_per_species=max_samples_per_species
    )
    
    test_dataset = BirdAudioDataset(
        data_dir=data_dir,
        species_list=species_list,
        split="test",
        augment=False,
        max_samples_per_species=max_samples_per_species
    )
    
    # Weighted sampler for training
    train_weights = train_dataset.get_sample_weights()
    train_sampler = torch.utils.data.WeightedRandomSampler(
        weights=train_weights,
        num_samples=len(train_dataset),
        replacement=True
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        sampler=train_sampler,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    return train_loader, val_loader, test_loader

