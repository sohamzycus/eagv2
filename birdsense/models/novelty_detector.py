"""
Novelty Detection for BirdSense.

Detects out-of-distribution samples that might represent:
- New species not in training data
- Species outside their normal range
- Unusual vocalizations
- Recording artifacts or non-bird sounds

Uses embedding-space distance metrics for detection.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass
import json


@dataclass
class NoveltyResult:
    """Result of novelty detection."""
    is_novel: bool
    novelty_score: float  # 0 = typical, 1 = very novel
    nearest_class: int
    nearest_distance: float
    confidence: float
    explanation: str


class NoveltyDetector:
    """
    Detects novel/out-of-distribution bird sounds.
    
    Uses Mahalanobis distance in embedding space to identify
    samples that don't match known species patterns.
    
    Key features:
    - Per-class covariance modeling
    - Adaptive thresholding
    - Geospatial prior integration (optional)
    """
    
    def __init__(
        self,
        embedding_dim: int = 384,
        num_classes: int = 250,
        threshold: float = 0.85
    ):
        self.embedding_dim = embedding_dim
        self.num_classes = num_classes
        self.threshold = threshold
        
        # Per-class statistics
        self.class_means: Optional[torch.Tensor] = None  # (num_classes, embedding_dim)
        self.class_covariances: Optional[torch.Tensor] = None  # (num_classes, embedding_dim, embedding_dim)
        self.global_covariance: Optional[torch.Tensor] = None
        self.is_fitted = False
        
        # For Mahalanobis distance
        self.precision_matrix: Optional[torch.Tensor] = None
    
    def fit(
        self,
        embeddings: torch.Tensor,
        labels: torch.Tensor,
        regularization: float = 1e-5
    ):
        """
        Fit the novelty detector on training embeddings.
        
        Args:
            embeddings: Training embeddings (n_samples, embedding_dim)
            labels: Class labels (n_samples,)
            regularization: Regularization for covariance estimation
        """
        embeddings = embeddings.cpu()
        labels = labels.cpu()
        
        n_classes = labels.max().item() + 1
        
        # Compute per-class means
        class_means = torch.zeros(n_classes, self.embedding_dim)
        class_counts = torch.zeros(n_classes)
        
        for emb, label in zip(embeddings, labels):
            class_means[label] += emb
            class_counts[label] += 1
        
        # Avoid division by zero
        class_counts = torch.clamp(class_counts, min=1)
        class_means = class_means / class_counts.unsqueeze(1)
        
        # Compute tied covariance (shared across classes for stability)
        centered = embeddings - class_means[labels]
        global_cov = (centered.T @ centered) / len(embeddings)
        
        # Add regularization
        global_cov += torch.eye(self.embedding_dim) * regularization
        
        # Compute precision matrix (inverse covariance)
        self.precision_matrix = torch.linalg.inv(global_cov)
        self.class_means = class_means
        self.global_covariance = global_cov
        self.num_classes = n_classes
        self.is_fitted = True
    
    def mahalanobis_distance(
        self,
        embeddings: torch.Tensor,
        class_idx: Optional[int] = None
    ) -> torch.Tensor:
        """
        Compute Mahalanobis distance to class mean(s).
        
        Args:
            embeddings: Query embeddings (batch, embedding_dim)
            class_idx: If specified, distance to specific class; otherwise min over all
            
        Returns:
            Distances (batch,) or (batch, num_classes)
        """
        if not self.is_fitted:
            raise RuntimeError("Novelty detector not fitted. Call fit() first.")
        
        embeddings = embeddings.cpu()
        
        if class_idx is not None:
            # Distance to specific class
            diff = embeddings - self.class_means[class_idx]
            dist = torch.sqrt(torch.sum(diff @ self.precision_matrix * diff, dim=-1))
            return dist
        else:
            # Distance to all classes
            distances = []
            for c in range(self.num_classes):
                diff = embeddings - self.class_means[c]
                dist = torch.sqrt(torch.sum(diff @ self.precision_matrix * diff, dim=-1))
                distances.append(dist)
            return torch.stack(distances, dim=-1)  # (batch, num_classes)
    
    def detect(
        self,
        embeddings: torch.Tensor,
        predicted_class: Optional[torch.Tensor] = None,
        species_names: Optional[List[str]] = None
    ) -> List[NoveltyResult]:
        """
        Detect novelty in embeddings.
        
        Args:
            embeddings: Query embeddings (batch, embedding_dim)
            predicted_class: Predicted class indices (batch,)
            species_names: Optional species name mapping
            
        Returns:
            List of NoveltyResult for each sample
        """
        if not self.is_fitted:
            raise RuntimeError("Novelty detector not fitted. Call fit() first.")
        
        # Compute distances to all classes
        all_distances = self.mahalanobis_distance(embeddings)  # (batch, num_classes)
        
        # Find minimum distance and corresponding class
        min_distances, nearest_classes = torch.min(all_distances, dim=-1)
        
        # Normalize to [0, 1] novelty score
        # Using sigmoid with empirically tuned scaling
        novelty_scores = torch.sigmoid((min_distances - 3.0) / 1.0)
        
        results = []
        for i in range(len(embeddings)):
            is_novel = novelty_scores[i].item() > self.threshold
            nearest = nearest_classes[i].item()
            
            if predicted_class is not None:
                pred = predicted_class[i].item()
                pred_distance = all_distances[i, pred].item()
            else:
                pred = nearest
                pred_distance = min_distances[i].item()
            
            # Generate explanation
            if is_novel:
                explanation = f"Sample appears novel (score: {novelty_scores[i]:.3f}). "
                explanation += f"Nearest known species: {species_names[nearest] if species_names else f'Class {nearest}'} "
                explanation += f"(distance: {min_distances[i]:.2f})"
            else:
                explanation = f"Sample matches known patterns (score: {novelty_scores[i]:.3f})"
            
            results.append(NoveltyResult(
                is_novel=is_novel,
                novelty_score=float(novelty_scores[i]),
                nearest_class=nearest,
                nearest_distance=float(min_distances[i]),
                confidence=float(1 - novelty_scores[i]),
                explanation=explanation
            ))
        
        return results
    
    def save(self, path: str):
        """Save fitted detector to file."""
        if not self.is_fitted:
            raise RuntimeError("Detector not fitted.")
        
        state = {
            "embedding_dim": self.embedding_dim,
            "num_classes": self.num_classes,
            "threshold": self.threshold,
            "class_means": self.class_means.numpy().tolist(),
            "precision_matrix": self.precision_matrix.numpy().tolist(),
            "global_covariance": self.global_covariance.numpy().tolist()
        }
        
        with open(path, 'w') as f:
            json.dump(state, f)
    
    def load(self, path: str):
        """Load fitted detector from file."""
        with open(path, 'r') as f:
            state = json.load(f)
        
        self.embedding_dim = state["embedding_dim"]
        self.num_classes = state["num_classes"]
        self.threshold = state["threshold"]
        self.class_means = torch.tensor(state["class_means"])
        self.precision_matrix = torch.tensor(state["precision_matrix"])
        self.global_covariance = torch.tensor(state["global_covariance"])
        self.is_fitted = True


class GeospatialNoveltyDetector(NoveltyDetector):
    """
    Extended novelty detector with geospatial priors.
    
    Considers species range maps to flag:
    - Species identified outside their known range
    - Unexpected seasonal occurrences
    """
    
    def __init__(
        self,
        embedding_dim: int = 384,
        num_classes: int = 250,
        threshold: float = 0.85,
        range_data_path: Optional[str] = None
    ):
        super().__init__(embedding_dim, num_classes, threshold)
        
        self.range_data: Dict[int, Dict] = {}  # class_id -> range info
        if range_data_path:
            self._load_range_data(range_data_path)
    
    def _load_range_data(self, path: str):
        """Load species range data."""
        with open(path, 'r') as f:
            self.range_data = json.load(f)
    
    def check_range_novelty(
        self,
        class_idx: int,
        latitude: float,
        longitude: float,
        month: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Check if species occurrence is novel given location.
        
        Args:
            class_idx: Predicted species index
            latitude: Recording latitude
            longitude: Recording longitude
            month: Optional month for seasonal check
            
        Returns:
            Tuple of (is_range_novel, explanation)
        """
        if class_idx not in self.range_data:
            return False, "No range data available"
        
        range_info = self.range_data[class_idx]
        
        # Simple bounding box check (can be enhanced with actual range polygons)
        lat_min = range_info.get("lat_min", -90)
        lat_max = range_info.get("lat_max", 90)
        lon_min = range_info.get("lon_min", -180)
        lon_max = range_info.get("lon_max", 180)
        
        in_range = (lat_min <= latitude <= lat_max and
                   lon_min <= longitude <= lon_max)
        
        if not in_range:
            return True, f"Species rarely found at this location ({latitude:.2f}, {longitude:.2f})"
        
        # Seasonal check
        if month and "seasonal_months" in range_info:
            if month not in range_info["seasonal_months"]:
                return True, f"Species unusual for month {month}"
        
        return False, "Within expected range"
    
    def detect_with_location(
        self,
        embeddings: torch.Tensor,
        predicted_class: torch.Tensor,
        latitude: float,
        longitude: float,
        month: Optional[int] = None,
        species_names: Optional[List[str]] = None
    ) -> List[NoveltyResult]:
        """
        Detect novelty considering both embeddings and location.
        """
        # Get embedding-based results
        results = self.detect(embeddings, predicted_class, species_names)
        
        # Enhance with geospatial information
        for i, result in enumerate(results):
            pred_class = predicted_class[i].item()
            is_range_novel, range_explanation = self.check_range_novelty(
                pred_class, latitude, longitude, month
            )
            
            if is_range_novel:
                # Boost novelty score for out-of-range detections
                result.novelty_score = min(1.0, result.novelty_score + 0.3)
                result.is_novel = result.novelty_score > self.threshold
                result.explanation += f" | RANGE ALERT: {range_explanation}"
        
        return results

