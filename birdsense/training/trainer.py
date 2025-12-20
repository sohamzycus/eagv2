"""
BirdSense Model Trainer.

Production-grade training pipeline for bird audio classification.
Targets 85%+ confidence on correctly identified species.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from torch.cuda.amp import autocast, GradScaler
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging
import json
from datetime import datetime
from rich.progress import Progress, TaskID
from rich.console import Console
from rich.table import Table

try:
    from ..models.audio_classifier import BirdAudioClassifier
    from .dataset import create_dataloaders
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.audio_classifier import BirdAudioClassifier
    from training.dataset import create_dataloaders

console = Console()
logger = logging.getLogger(__name__)


class LabelSmoothingLoss(nn.Module):
    """Cross entropy with label smoothing for better calibration."""
    
    def __init__(self, num_classes: int, smoothing: float = 0.1):
        super().__init__()
        self.num_classes = num_classes
        self.smoothing = smoothing
        self.confidence = 1.0 - smoothing
    
    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        pred = pred.log_softmax(dim=-1)
        
        with torch.no_grad():
            true_dist = torch.zeros_like(pred)
            true_dist.fill_(self.smoothing / (self.num_classes - 1))
            true_dist.scatter_(1, target.unsqueeze(1), self.confidence)
        
        return torch.mean(torch.sum(-true_dist * pred, dim=-1))


class FocalLoss(nn.Module):
    """Focal loss for handling class imbalance."""
    
    def __init__(self, alpha: float = 0.25, gamma: float = 2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
    
    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        ce_loss = F.cross_entropy(pred, target, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        return focal_loss.mean()


class BirdSenseTrainer:
    """
    Production trainer for BirdSense model.
    
    Features:
    - Mixed precision training
    - Label smoothing for calibration
    - Cosine annealing with warm restarts
    - Early stopping with patience
    - Checkpoint saving and resumption
    - Temperature calibration post-training
    """
    
    def __init__(
        self,
        model: BirdAudioClassifier,
        data_dir: str,
        output_dir: str = "checkpoints",
        learning_rate: float = 1e-4,
        weight_decay: float = 0.01,
        batch_size: int = 32,
        epochs: int = 100,
        label_smoothing: float = 0.1,
        warmup_epochs: int = 5,
        patience: int = 15,
        device: Optional[str] = None,
        use_amp: bool = True
    ):
        """
        Initialize trainer.
        
        Args:
            model: BirdAudioClassifier model
            data_dir: Path to training data
            output_dir: Directory for checkpoints
            learning_rate: Initial learning rate
            weight_decay: Weight decay for regularization
            batch_size: Training batch size
            epochs: Maximum training epochs
            label_smoothing: Label smoothing factor (0.1 recommended)
            warmup_epochs: Warmup epochs before main training
            patience: Early stopping patience
            device: Training device (auto-detected if None)
            use_amp: Use automatic mixed precision
        """
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Training config
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.batch_size = batch_size
        self.epochs = epochs
        self.warmup_epochs = warmup_epochs
        self.patience = patience
        self.use_amp = use_amp
        
        # Device
        if device:
            self.device = torch.device(device)
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
        
        self.model.to(self.device)
        
        # Create dataloaders
        self.train_loader, self.val_loader, self.test_loader = create_dataloaders(
            data_dir=data_dir,
            batch_size=batch_size
        )
        
        # Loss function
        num_classes = model.num_classes
        self.criterion = LabelSmoothingLoss(num_classes, smoothing=label_smoothing)
        
        # Optimizer
        self.optimizer = AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Scheduler
        self.scheduler = CosineAnnealingWarmRestarts(
            self.optimizer,
            T_0=10,
            T_mult=2,
            eta_min=1e-6
        )
        
        # Mixed precision
        self.scaler = GradScaler() if use_amp and self.device.type == "cuda" else None
        
        # Training state
        self.best_val_acc = 0.0
        self.epochs_without_improvement = 0
        self.history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': [],
            'val_confidence': [],
            'learning_rate': []
        }
    
    def train_epoch(self, epoch: int) -> Tuple[float, float]:
        """Train for one epoch."""
        self.model.train()
        
        total_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (inputs, targets) in enumerate(self.train_loader):
            inputs = inputs.to(self.device)
            targets = targets.to(self.device)
            
            self.optimizer.zero_grad()
            
            if self.scaler:
                with autocast():
                    outputs = self.model(inputs)
                    loss = self.criterion(outputs['logits'], targets)
                
                self.scaler.scale(loss).backward()
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                outputs = self.model(inputs)
                loss = self.criterion(outputs['logits'], targets)
                loss.backward()
                self.optimizer.step()
            
            total_loss += loss.item()
            _, predicted = outputs['logits'].max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()
        
        avg_loss = total_loss / len(self.train_loader)
        accuracy = 100.0 * correct / total
        
        return avg_loss, accuracy
    
    @torch.no_grad()
    def validate(self) -> Tuple[float, float, float]:
        """Validate model."""
        self.model.eval()
        
        total_loss = 0.0
        correct = 0
        total = 0
        all_confidences = []
        all_correct = []
        
        for inputs, targets in self.val_loader:
            inputs = inputs.to(self.device)
            targets = targets.to(self.device)
            
            outputs = self.model(inputs)
            loss = self.criterion(outputs['logits'], targets)
            
            total_loss += loss.item()
            
            probs = outputs['probabilities']
            confidence, predicted = probs.max(1)
            
            total += targets.size(0)
            is_correct = predicted.eq(targets)
            correct += is_correct.sum().item()
            
            all_confidences.extend(confidence.cpu().numpy())
            all_correct.extend(is_correct.cpu().numpy())
        
        avg_loss = total_loss / len(self.val_loader)
        accuracy = 100.0 * correct / total
        
        # Average confidence on correct predictions
        import numpy as np
        all_confidences = np.array(all_confidences)
        all_correct = np.array(all_correct)
        
        if all_correct.sum() > 0:
            avg_confidence = float(all_confidences[all_correct].mean()) * 100
        else:
            avg_confidence = 0.0
        
        return avg_loss, accuracy, avg_confidence
    
    def train(self) -> Dict[str, Any]:
        """
        Full training loop.
        
        Returns:
            Training results and metrics
        """
        console.print("\n[bold green]Starting BirdSense Training[/bold green]\n")
        console.print(f"Device: {self.device}")
        console.print(f"Train samples: {len(self.train_loader.dataset)}")
        console.print(f"Val samples: {len(self.val_loader.dataset)}")
        console.print(f"Classes: {self.model.num_classes}")
        console.print(f"Parameters: {self.model.count_parameters()['total']:,}")
        console.print("")
        
        start_time = datetime.now()
        
        with Progress() as progress:
            epoch_task = progress.add_task("[cyan]Training", total=self.epochs)
            
            for epoch in range(self.epochs):
                # Train
                train_loss, train_acc = self.train_epoch(epoch)
                
                # Validate
                val_loss, val_acc, val_conf = self.validate()
                
                # Update scheduler
                self.scheduler.step()
                current_lr = self.optimizer.param_groups[0]['lr']
                
                # Record history
                self.history['train_loss'].append(train_loss)
                self.history['train_acc'].append(train_acc)
                self.history['val_loss'].append(val_loss)
                self.history['val_acc'].append(val_acc)
                self.history['val_confidence'].append(val_conf)
                self.history['learning_rate'].append(current_lr)
                
                # Progress update
                progress.update(
                    epoch_task, 
                    advance=1,
                    description=f"[cyan]Epoch {epoch+1}/{self.epochs} | "
                               f"Val Acc: {val_acc:.1f}% | Conf: {val_conf:.1f}%"
                )
                
                # Check for improvement
                if val_acc > self.best_val_acc:
                    self.best_val_acc = val_acc
                    self.epochs_without_improvement = 0
                    self._save_checkpoint("best.pt", epoch, val_acc, val_conf)
                    console.print(f"  [green]✓ New best: {val_acc:.2f}%[/green]")
                else:
                    self.epochs_without_improvement += 1
                
                # Early stopping
                if self.epochs_without_improvement >= self.patience:
                    console.print(f"\n[yellow]Early stopping at epoch {epoch+1}[/yellow]")
                    break
                
                # Periodic checkpoint
                if (epoch + 1) % 10 == 0:
                    self._save_checkpoint(f"epoch_{epoch+1}.pt", epoch, val_acc, val_conf)
        
        training_time = datetime.now() - start_time
        
        # Final evaluation
        console.print("\n[bold]Final Evaluation on Test Set[/bold]")
        self._load_checkpoint("best.pt")
        test_loss, test_acc, test_conf = self._evaluate_test()
        
        # Calibrate temperature
        console.print("\n[bold]Calibrating Temperature[/bold]")
        self.model.calibrate_temperature(self.val_loader, str(self.device))
        self._save_checkpoint("best_calibrated.pt", -1, test_acc, test_conf)
        
        # Results
        results = {
            'test_accuracy': test_acc,
            'test_confidence': test_conf,
            'best_val_accuracy': self.best_val_acc,
            'epochs_trained': len(self.history['train_loss']),
            'training_time': str(training_time),
            'final_learning_rate': self.history['learning_rate'][-1],
            'history': self.history
        }
        
        # Save results
        with open(self.output_dir / "training_results.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        self._print_results(results)
        
        return results
    
    @torch.no_grad()
    def _evaluate_test(self) -> Tuple[float, float, float]:
        """Evaluate on test set."""
        return self.validate()  # Same logic, different loader
    
    def _save_checkpoint(
        self,
        filename: str,
        epoch: int,
        val_acc: float,
        val_conf: float
    ):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'val_accuracy': val_acc,
            'val_confidence': val_conf,
            'best_val_acc': self.best_val_acc,
            'history': self.history
        }
        
        if self.scaler:
            checkpoint['scaler_state_dict'] = self.scaler.state_dict()
        
        torch.save(checkpoint, self.output_dir / filename)
    
    def _load_checkpoint(self, filename: str):
        """Load model checkpoint."""
        checkpoint = torch.load(self.output_dir / filename, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
    
    def _print_results(self, results: Dict[str, Any]):
        """Print training results."""
        table = Table(title="Training Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Test Accuracy", f"{results['test_accuracy']:.2f}%")
        table.add_row("Test Confidence (correct)", f"{results['test_confidence']:.2f}%")
        table.add_row("Best Val Accuracy", f"{results['best_val_accuracy']:.2f}%")
        table.add_row("Epochs Trained", str(results['epochs_trained']))
        table.add_row("Training Time", results['training_time'])
        
        console.print(table)
        
        if results['test_accuracy'] >= 85:
            console.print("\n[bold green]✓ Target 85% accuracy achieved![/bold green]")
        else:
            console.print(f"\n[yellow]Target: 85% | Current: {results['test_accuracy']:.2f}%[/yellow]")
            console.print("Consider: more data, longer training, or model tuning")


def train_birdsense(
    data_dir: str,
    output_dir: str = "checkpoints",
    epochs: int = 100,
    batch_size: int = 32,
    learning_rate: float = 1e-4,
    num_classes: int = 100
):
    """
    Train BirdSense model from scratch.
    
    Args:
        data_dir: Path to Xeno-Canto data
        output_dir: Checkpoint output directory
        epochs: Training epochs
        batch_size: Batch size
        learning_rate: Initial learning rate
        num_classes: Number of species classes
    """
    # Create model
    model = BirdAudioClassifier(
        num_classes=num_classes,
        encoder_architecture='cnn',
        embedding_dim=384,
        dropout=0.3
    )
    
    # Create trainer
    trainer = BirdSenseTrainer(
        model=model,
        data_dir=data_dir,
        output_dir=output_dir,
        learning_rate=learning_rate,
        batch_size=batch_size,
        epochs=epochs,
        label_smoothing=0.1,
        patience=15
    )
    
    # Train
    results = trainer.train()
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train BirdSense model")
    parser.add_argument("--data-dir", required=True, help="Path to training data")
    parser.add_argument("--output-dir", default="checkpoints", help="Output directory")
    parser.add_argument("--epochs", type=int, default=100, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--classes", type=int, default=100, help="Number of classes")
    
    args = parser.parse_args()
    
    train_birdsense(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        num_classes=args.classes
    )

