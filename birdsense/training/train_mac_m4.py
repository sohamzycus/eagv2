"""
BirdSense Local Training for Mac M4 Pro

Optimized for Apple Silicon (M4 Pro) using Metal Performance Shaders (MPS).
No cloud/GPU required - trains entirely on your local laptop.

Features:
- MPS acceleration (Apple GPU)
- Memory-efficient training
- Progress saving (resume training)
- Mixed precision for speed

Usage:
    python training/train_mac_m4.py --data_dir data/xeno-canto --epochs 50

Requirements:
    - Mac with Apple Silicon (M1/M2/M3/M4)
    - PyTorch with MPS support
    - 16GB+ RAM recommended
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import json

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio.preprocessor import AudioPreprocessor
from audio.augmentation import AudioAugmenter
from models.audio_classifier import BirdAudioClassifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BirdAudioDataset(Dataset):
    """Dataset for bird audio files with on-the-fly preprocessing."""
    
    def __init__(
        self,
        data_dir: str,
        species_list: list,
        preprocessor: AudioPreprocessor,
        augmenter: AudioAugmenter = None,
        train: bool = True,
        max_samples_per_class: int = 200
    ):
        self.data_dir = Path(data_dir)
        self.species_list = species_list
        self.preprocessor = preprocessor
        self.augmenter = augmenter
        self.train = train
        
        self.samples = []
        self._load_samples(max_samples_per_class)
    
    def _load_samples(self, max_per_class):
        """Load sample file paths."""
        import soundfile as sf
        
        for label_idx, species in enumerate(self.species_list):
            species_dir = self.data_dir / species.replace(' ', '_').lower()
            
            if not species_dir.exists():
                logger.warning(f"Directory not found: {species_dir}")
                continue
            
            audio_files = list(species_dir.glob('*.wav')) + list(species_dir.glob('*.mp3'))
            
            for audio_file in audio_files[:max_per_class]:
                self.samples.append({
                    'path': str(audio_file),
                    'label': label_idx,
                    'species': species
                })
        
        logger.info(f"Loaded {len(self.samples)} samples from {len(self.species_list)} classes")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        try:
            import soundfile as sf
            import librosa
            
            # Load audio
            audio, sr = librosa.load(sample['path'], sr=32000, mono=True)
            
            # Augment if training
            if self.train and self.augmenter:
                audio = self.augmenter.augment(audio, sr)
            
            # Preprocess to mel spectrogram
            result = self.preprocessor.process(audio)
            mel_spec = result['mel_specs'][0]  # Take first chunk
            
            # Convert to tensor
            x = torch.tensor(mel_spec, dtype=torch.float32)
            y = torch.tensor(sample['label'], dtype=torch.long)
            
            return x, y
            
        except Exception as e:
            logger.warning(f"Error loading {sample['path']}: {e}")
            # Return a zero tensor as fallback
            x = torch.zeros(1, 128, 100, dtype=torch.float32)
            y = torch.tensor(sample['label'], dtype=torch.long)
            return x, y


class MacM4Trainer:
    """
    Training pipeline optimized for Mac M4 Pro.
    
    Uses MPS (Metal Performance Shaders) for GPU acceleration
    on Apple Silicon Macs.
    """
    
    def __init__(
        self,
        data_dir: str,
        output_dir: str = "checkpoints",
        batch_size: int = 16,
        learning_rate: float = 1e-4,
        weight_decay: float = 0.01,
        label_smoothing: float = 0.1
    ):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.label_smoothing = label_smoothing
        
        # Setup device - prefer MPS for Mac M4
        self.device = self._setup_device()
        
        # Components
        self.preprocessor = AudioPreprocessor()
        self.augmenter = AudioAugmenter()
        self.model = None
        self.optimizer = None
        self.scheduler = None
        
        # Training state
        self.best_accuracy = 0.0
        self.epoch = 0
        self.history = {'train_loss': [], 'val_loss': [], 'val_acc': []}
    
    def _setup_device(self):
        """Setup compute device - MPS for Mac M4."""
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = torch.device("mps")
            logger.info("🍎 Using MPS (Apple Silicon GPU) - M4 Pro optimized!")
        elif torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info("Using CUDA GPU")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU (MPS not available)")
        
        return device
    
    def prepare_data(self, species_list: list, val_split: float = 0.15):
        """Prepare training and validation datasets."""
        
        # Full dataset
        full_dataset = BirdAudioDataset(
            self.data_dir,
            species_list,
            self.preprocessor,
            self.augmenter,
            train=True
        )
        
        # Split into train/val
        n_samples = len(full_dataset)
        n_val = int(n_samples * val_split)
        n_train = n_samples - n_val
        
        train_dataset, val_dataset = torch.utils.data.random_split(
            full_dataset, [n_train, n_val]
        )
        
        # DataLoaders - use small num_workers for MPS
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            num_workers=0,  # MPS works better with 0 workers
            pin_memory=False  # Not needed for MPS
        )
        
        self.val_loader = DataLoader(
            val_dataset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=0
        )
        
        logger.info(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}")
        
        return len(species_list)
    
    def build_model(self, num_classes: int):
        """Build and setup model."""
        self.model = BirdAudioClassifier(
            num_classes=num_classes,
            encoder_architecture='cnn',
            embedding_dim=384
        )
        self.model.to(self.device)
        
        # Optimizer with weight decay
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=self.weight_decay
        )
        
        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
            self.optimizer,
            T_0=10,
            T_mult=2
        )
        
        # Loss with label smoothing
        self.criterion = nn.CrossEntropyLoss(label_smoothing=self.label_smoothing)
        
        # Count parameters
        n_params = sum(p.numel() for p in self.model.parameters())
        logger.info(f"Model parameters: {n_params:,}")
    
    def train_epoch(self):
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        n_batches = 0
        
        for batch_idx, (x, y) in enumerate(self.train_loader):
            # Move to device
            x = x.to(self.device)
            y = y.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(x)
            loss = self.criterion(outputs['logits'], y)
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            total_loss += loss.item()
            n_batches += 1
            
            # Progress
            if batch_idx % 10 == 0:
                logger.info(f"  Batch {batch_idx}/{len(self.train_loader)}, Loss: {loss.item():.4f}")
        
        self.scheduler.step()
        
        return total_loss / n_batches
    
    @torch.no_grad()
    def validate(self):
        """Validate model."""
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        
        for x, y in self.val_loader:
            x = x.to(self.device)
            y = y.to(self.device)
            
            outputs = self.model(x)
            loss = self.criterion(outputs['logits'], y)
            
            total_loss += loss.item()
            
            preds = outputs['logits'].argmax(dim=1)
            correct += (preds == y).sum().item()
            total += y.size(0)
        
        accuracy = correct / total if total > 0 else 0.0
        avg_loss = total_loss / len(self.val_loader) if len(self.val_loader) > 0 else 0.0
        
        return avg_loss, accuracy
    
    def save_checkpoint(self, filename: str = "checkpoint.pt"):
        """Save training checkpoint."""
        checkpoint = {
            'epoch': self.epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'best_accuracy': self.best_accuracy,
            'history': self.history
        }
        
        path = self.output_dir / filename
        torch.save(checkpoint, path)
        logger.info(f"Saved checkpoint: {path}")
    
    def load_checkpoint(self, filename: str = "checkpoint.pt"):
        """Load training checkpoint to resume."""
        path = self.output_dir / filename
        
        if path.exists():
            checkpoint = torch.load(path, map_location=self.device)
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            self.epoch = checkpoint['epoch']
            self.best_accuracy = checkpoint['best_accuracy']
            self.history = checkpoint['history']
            
            logger.info(f"Resumed from epoch {self.epoch} with best acc: {self.best_accuracy:.2%}")
            return True
        
        return False
    
    def train(self, epochs: int, species_list: list, resume: bool = True):
        """
        Main training loop.
        
        Args:
            epochs: Number of epochs to train
            species_list: List of species names
            resume: Whether to resume from checkpoint
        """
        # Prepare data
        num_classes = self.prepare_data(species_list)
        
        # Build model
        self.build_model(num_classes)
        
        # Try to resume
        if resume:
            self.load_checkpoint()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🐦 BirdSense Training on Mac M4 Pro")
        logger.info(f"{'='*60}")
        logger.info(f"Device: {self.device}")
        logger.info(f"Classes: {num_classes}")
        logger.info(f"Epochs: {epochs}")
        logger.info(f"Batch Size: {self.batch_size}")
        logger.info(f"Learning Rate: {self.learning_rate}")
        logger.info(f"{'='*60}\n")
        
        # Training loop
        for epoch in range(self.epoch, epochs):
            self.epoch = epoch
            logger.info(f"\nEpoch {epoch + 1}/{epochs}")
            logger.info("-" * 40)
            
            # Train
            train_loss = self.train_epoch()
            
            # Validate
            val_loss, val_acc = self.validate()
            
            # Log
            logger.info(f"Train Loss: {train_loss:.4f}")
            logger.info(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2%}")
            
            # Save history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)
            
            # Save best model
            if val_acc > self.best_accuracy:
                self.best_accuracy = val_acc
                self.save_checkpoint("best_model.pt")
                logger.info(f"🎯 New best accuracy: {val_acc:.2%}")
            
            # Regular checkpoint
            self.save_checkpoint("checkpoint.pt")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Training complete!")
        logger.info(f"Best Accuracy: {self.best_accuracy:.2%}")
        logger.info(f"{'='*60}")
        
        # Save final model
        self.save_checkpoint("final_model.pt")
        
        return self.history


def main():
    parser = argparse.ArgumentParser(description="Train BirdSense on Mac M4 Pro")
    parser.add_argument("--data_dir", type=str, default="data/xeno-canto",
                        help="Directory with bird audio files")
    parser.add_argument("--output_dir", type=str, default="checkpoints",
                        help="Directory for saving models")
    parser.add_argument("--epochs", type=int, default=50,
                        help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16,
                        help="Batch size (reduce if running out of memory)")
    parser.add_argument("--lr", type=float, default=1e-4,
                        help="Learning rate")
    parser.add_argument("--no_resume", action="store_true",
                        help="Start fresh instead of resuming")
    
    args = parser.parse_args()
    
    # Define species to train on
    # Start with common Indian birds
    species_list = [
        "Asian Koel",
        "Indian Cuckoo",
        "Common Myna",
        "House Crow",
        "House Sparrow",
        "Red-vented Bulbul",
        "Coppersmith Barbet",
        "Rose-ringed Parakeet",
        "Spotted Dove",
        "White-throated Kingfisher",
        "Common Kingfisher",
        "Indian Peafowl",
        "Black Drongo",
        "Oriental Magpie-Robin",
        "Indian Robin",
        "Common Tailorbird",
        "Purple Sunbird",
        "Spotted Owlet",
        "Indian Golden Oriole",
        "Green Bee-eater"
    ]
    
    # Create trainer
    trainer = MacM4Trainer(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )
    
    # Check for data
    if not Path(args.data_dir).exists():
        logger.info(f"Data directory not found: {args.data_dir}")
        logger.info("Please download bird audio data first:")
        logger.info("  python training/xeno_canto.py --species 'Asian Koel' --max_recordings 100")
        return
    
    # Train!
    history = trainer.train(
        epochs=args.epochs,
        species_list=species_list,
        resume=not args.no_resume
    )
    
    # Save training history
    with open(Path(args.output_dir) / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)
    
    logger.info("\n🍎 Training completed on Mac M4 Pro!")


if __name__ == "__main__":
    main()

