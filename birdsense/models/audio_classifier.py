"""
Bird Audio Classifier for BirdSense.

Complete classification pipeline from audio to species prediction.
Combines the audio encoder with a classification head and
optional LLM reasoning for enhanced accuracy.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, List, Dict, Tuple
import numpy as np

try:
    from ..audio.encoder import AudioEncoder
except ImportError:
    from audio.encoder import AudioEncoder


class ClassificationHead(nn.Module):
    """
    Classification head with dropout and layer norm.
    """
    
    def __init__(
        self,
        input_dim: int,
        num_classes: int,
        hidden_dims: List[int] = [256, 128],
        dropout: float = 0.3
    ):
        super().__init__()
        
        layers = []
        in_dim = input_dim
        
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(in_dim, h_dim),
                nn.LayerNorm(h_dim),
                nn.GELU(),
                nn.Dropout(dropout)
            ])
            in_dim = h_dim
        
        layers.append(nn.Linear(in_dim, num_classes))
        
        self.classifier = nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(x)


class BirdAudioClassifier(nn.Module):
    """
    Complete bird audio classification model.
    
    Combines:
    - Audio encoder (CNN or Transformer)
    - Classification head
    - Uncertainty estimation
    
    Designed for robust bird species identification from audio.
    """
    
    def __init__(
        self,
        num_classes: int = 250,
        encoder_architecture: str = 'cnn',
        n_mels: int = 128,
        embedding_dim: int = 384,
        hidden_dims: List[int] = [256, 128],
        dropout: float = 0.3,
        pretrained_encoder: bool = False
    ):
        super().__init__()
        
        self.num_classes = num_classes
        self.embedding_dim = embedding_dim
        
        # Audio encoder
        self.encoder = AudioEncoder(
            architecture=encoder_architecture,
            n_mels=n_mels,
            embedding_dim=embedding_dim,
            pretrained=pretrained_encoder
        )
        
        # Classification head
        self.classifier = ClassificationHead(
            input_dim=embedding_dim,
            num_classes=num_classes,
            hidden_dims=hidden_dims,
            dropout=dropout
        )
        
        # Temperature for calibrated probabilities
        self.temperature = nn.Parameter(torch.ones(1))
    
    def forward(
        self, 
        x: torch.Tensor,
        return_embeddings: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: Mel-spectrogram (batch, n_mels, n_frames)
            return_embeddings: Whether to return intermediate embeddings
            
        Returns:
            Dictionary with:
            - logits: Raw classification scores
            - probabilities: Softmax probabilities
            - embeddings: (optional) Audio embeddings
        """
        # Extract embeddings
        embeddings = self.encoder(x)
        
        # Classify
        logits = self.classifier(embeddings)
        
        # Temperature-scaled probabilities
        probabilities = F.softmax(logits / self.temperature, dim=-1)
        
        output = {
            "logits": logits,
            "probabilities": probabilities
        }
        
        if return_embeddings:
            output["embeddings"] = embeddings
        
        return output
    
    def predict(
        self,
        x: torch.Tensor,
        top_k: int = 5
    ) -> Dict[str, torch.Tensor]:
        """
        Get top-k predictions with confidence scores.
        
        Args:
            x: Mel-spectrogram input
            top_k: Number of top predictions to return
            
        Returns:
            Dictionary with:
            - top_indices: Indices of top-k classes
            - top_probabilities: Probabilities of top-k classes
            - max_confidence: Confidence of top prediction
            - uncertainty: Entropy-based uncertainty
        """
        with torch.no_grad():
            output = self.forward(x, return_embeddings=True)
            probs = output["probabilities"]
            
            # Top-k predictions
            top_probs, top_indices = torch.topk(probs, k=min(top_k, probs.size(-1)), dim=-1)
            
            # Uncertainty (entropy)
            entropy = -torch.sum(probs * torch.log(probs + 1e-8), dim=-1)
            max_entropy = np.log(self.num_classes)
            uncertainty = entropy / max_entropy  # Normalized [0, 1]
            
            return {
                "top_indices": top_indices,
                "top_probabilities": top_probs,
                "max_confidence": top_probs[:, 0],
                "uncertainty": uncertainty,
                "embeddings": output["embeddings"]
            }
    
    def get_embedding(self, x: torch.Tensor) -> torch.Tensor:
        """Extract audio embeddings without classification."""
        with torch.no_grad():
            return self.encoder(x)
    
    def calibrate_temperature(
        self,
        val_loader,
        device: str = 'cpu'
    ):
        """
        Calibrate temperature using validation set.
        Uses temperature scaling for better probability calibration.
        """
        self.eval()
        logits_list = []
        labels_list = []
        
        with torch.no_grad():
            for x, y in val_loader:
                x = x.to(device)
                output = self.forward(x)
                logits_list.append(output["logits"].cpu())
                labels_list.append(y)
        
        logits = torch.cat(logits_list, dim=0)
        labels = torch.cat(labels_list, dim=0)
        
        # Find optimal temperature
        best_temp = 1.0
        best_nll = float('inf')
        
        for temp in np.linspace(0.5, 3.0, 50):
            scaled_logits = logits / temp
            nll = F.cross_entropy(scaled_logits, labels)
            if nll < best_nll:
                best_nll = nll
                best_temp = temp
        
        self.temperature.data = torch.tensor([best_temp])
        print(f"Calibrated temperature: {best_temp:.3f}")
    
    def count_parameters(self) -> Dict[str, int]:
        """Count parameters in each component."""
        encoder_params = sum(p.numel() for p in self.encoder.parameters())
        classifier_params = sum(p.numel() for p in self.classifier.parameters())
        total_params = sum(p.numel() for p in self.parameters())
        
        return {
            "encoder": encoder_params,
            "classifier": classifier_params,
            "total": total_params,
            "total_mb": total_params * 4 / (1024 * 1024)  # Assuming float32
        }
    
    def export_onnx(self, path: str, n_mels: int = 128, n_frames: int = 500):
        """Export model to ONNX format for mobile deployment."""
        dummy_input = torch.randn(1, n_mels, n_frames)
        
        torch.onnx.export(
            self,
            dummy_input,
            path,
            input_names=['mel_spectrogram'],
            output_names=['logits', 'probabilities'],
            dynamic_axes={
                'mel_spectrogram': {0: 'batch', 2: 'frames'},
                'logits': {0: 'batch'},
                'probabilities': {0: 'batch'}
            },
            opset_version=14
        )
        print(f"Exported ONNX model to {path}")


class EnsembleBirdClassifier(nn.Module):
    """
    Ensemble of multiple classifiers for robust predictions.
    
    Uses multiple architectures and combines predictions for
    improved accuracy and calibration.
    """
    
    def __init__(
        self,
        num_classes: int = 250,
        n_mels: int = 128,
        embedding_dim: int = 384
    ):
        super().__init__()
        
        # Ensemble of different architectures
        self.classifiers = nn.ModuleList([
            BirdAudioClassifier(
                num_classes=num_classes,
                encoder_architecture='cnn',
                n_mels=n_mels,
                embedding_dim=embedding_dim
            ),
            # Can add more architectures here
        ])
        
        # Learnable ensemble weights
        self.ensemble_weights = nn.Parameter(torch.ones(len(self.classifiers)))
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Ensemble forward pass with weighted averaging.
        """
        all_logits = []
        all_embeddings = []
        
        for classifier in self.classifiers:
            output = classifier(x, return_embeddings=True)
            all_logits.append(output["logits"])
            all_embeddings.append(output["embeddings"])
        
        # Weighted average
        weights = F.softmax(self.ensemble_weights, dim=0)
        logits_stack = torch.stack(all_logits, dim=0)  # (n_models, batch, classes)
        ensemble_logits = torch.sum(weights.view(-1, 1, 1) * logits_stack, dim=0)
        
        probabilities = F.softmax(ensemble_logits, dim=-1)
        
        return {
            "logits": ensemble_logits,
            "probabilities": probabilities,
            "embeddings": torch.mean(torch.stack(all_embeddings), dim=0),
            "individual_logits": all_logits
        }

