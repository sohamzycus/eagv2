"""
Lightweight Audio Encoder for BirdSense.

Implements a small, efficient audio encoder optimized for bird call recognition.
Designed for edge deployment while maintaining competitive accuracy.

Architecture options:
1. AST-Tiny: Audio Spectrogram Transformer (small variant)
2. EfficientNet-B0: Adapted for spectrograms
3. MobileViT: Vision transformer for mobile
4. Custom CNN: Lightweight convolutional network
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
import math


class ConvBlock(nn.Module):
    """Convolutional block with batch norm and activation."""
    
    def __init__(
        self, 
        in_channels: int, 
        out_channels: int, 
        kernel_size: int = 3,
        stride: int = 1,
        padding: int = 1
    ):
        super().__init__()
        self.conv = nn.Conv2d(
            in_channels, out_channels, 
            kernel_size, stride, padding, 
            bias=False
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.act = nn.SiLU(inplace=True)  # Swish activation
    
    def forward(self, x):
        return self.act(self.bn(self.conv(x)))


class SqueezeExcitation(nn.Module):
    """Squeeze-and-Excitation attention block."""
    
    def __init__(self, channels: int, reduction: int = 4):
        super().__init__()
        reduced = max(1, channels // reduction)
        self.fc1 = nn.Conv2d(channels, reduced, 1)
        self.fc2 = nn.Conv2d(reduced, channels, 1)
    
    def forward(self, x):
        scale = F.adaptive_avg_pool2d(x, 1)
        scale = F.silu(self.fc1(scale))
        scale = torch.sigmoid(self.fc2(scale))
        return x * scale


class MBConv(nn.Module):
    """Mobile Inverted Bottleneck Conv (from EfficientNet)."""
    
    def __init__(
        self, 
        in_channels: int, 
        out_channels: int, 
        expand_ratio: int = 4,
        stride: int = 1,
        se_ratio: float = 0.25
    ):
        super().__init__()
        self.stride = stride
        self.use_residual = stride == 1 and in_channels == out_channels
        
        hidden_dim = in_channels * expand_ratio
        
        layers = []
        
        # Expansion
        if expand_ratio != 1:
            layers.extend([
                nn.Conv2d(in_channels, hidden_dim, 1, bias=False),
                nn.BatchNorm2d(hidden_dim),
                nn.SiLU(inplace=True)
            ])
        
        # Depthwise conv
        layers.extend([
            nn.Conv2d(hidden_dim, hidden_dim, 3, stride, 1, groups=hidden_dim, bias=False),
            nn.BatchNorm2d(hidden_dim),
            nn.SiLU(inplace=True)
        ])
        
        # Squeeze-and-Excitation
        if se_ratio > 0:
            layers.append(SqueezeExcitation(hidden_dim, int(1 / se_ratio)))
        
        # Projection
        layers.extend([
            nn.Conv2d(hidden_dim, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels)
        ])
        
        self.conv = nn.Sequential(*layers)
    
    def forward(self, x):
        if self.use_residual:
            return x + self.conv(x)
        return self.conv(x)


class BirdAudioEncoder(nn.Module):
    """
    Lightweight audio encoder for bird sound recognition.
    
    Takes mel-spectrogram input and produces embeddings.
    Designed for efficiency while maintaining good accuracy.
    
    Architecture: Custom efficient CNN inspired by EfficientNet-B0/MobileNetV3
    Parameters: ~2M (very lightweight)
    Input: Mel-spectrogram (1, n_mels, n_frames)
    Output: Embedding vector (embedding_dim,)
    """
    
    def __init__(
        self, 
        n_mels: int = 128,
        embedding_dim: int = 384,
        width_multiplier: float = 1.0
    ):
        super().__init__()
        
        self.n_mels = n_mels
        self.embedding_dim = embedding_dim
        
        def _make_divisible(v):
            """Round to nearest multiple of 8."""
            new_v = max(8, int(v * width_multiplier + 4) // 8 * 8)
            if new_v < 0.9 * v * width_multiplier:
                new_v += 8
            return new_v
        
        # Stem
        self.stem = ConvBlock(1, _make_divisible(32), 3, 2, 1)
        
        # Main blocks
        self.blocks = nn.Sequential(
            # Stage 1
            MBConv(_make_divisible(32), _make_divisible(16), expand_ratio=1, stride=1),
            
            # Stage 2
            MBConv(_make_divisible(16), _make_divisible(24), expand_ratio=4, stride=2),
            MBConv(_make_divisible(24), _make_divisible(24), expand_ratio=4, stride=1),
            
            # Stage 3
            MBConv(_make_divisible(24), _make_divisible(40), expand_ratio=4, stride=2),
            MBConv(_make_divisible(40), _make_divisible(40), expand_ratio=4, stride=1),
            
            # Stage 4
            MBConv(_make_divisible(40), _make_divisible(80), expand_ratio=4, stride=2),
            MBConv(_make_divisible(80), _make_divisible(80), expand_ratio=4, stride=1),
            MBConv(_make_divisible(80), _make_divisible(80), expand_ratio=4, stride=1),
            
            # Stage 5
            MBConv(_make_divisible(80), _make_divisible(112), expand_ratio=4, stride=1),
            MBConv(_make_divisible(112), _make_divisible(112), expand_ratio=4, stride=1),
            
            # Stage 6
            MBConv(_make_divisible(112), _make_divisible(192), expand_ratio=4, stride=2),
            MBConv(_make_divisible(192), _make_divisible(192), expand_ratio=4, stride=1),
        )
        
        # Head
        self.head = nn.Sequential(
            ConvBlock(_make_divisible(192), _make_divisible(320), 1, 1, 0),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(_make_divisible(320), embedding_dim),
            nn.LayerNorm(embedding_dim)
        )
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Linear):
                nn.init.trunc_normal_(m.weight, std=0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Mel-spectrogram tensor of shape (batch, n_mels, n_frames)
               or (batch, 1, n_mels, n_frames)
        
        Returns:
            Embedding tensor of shape (batch, embedding_dim)
        """
        # Add channel dimension if needed
        if x.dim() == 3:
            x = x.unsqueeze(1)  # (B, 1, n_mels, n_frames)
        
        x = self.stem(x)
        x = self.blocks(x)
        x = self.head(x)
        
        return x
    
    def get_embedding_dim(self) -> int:
        return self.embedding_dim


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for transformer."""
    
    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, :x.size(1)]


class PatchEmbed(nn.Module):
    """Convert spectrogram to patch embeddings."""
    
    def __init__(
        self, 
        img_size: Tuple[int, int] = (128, 500),
        patch_size: Tuple[int, int] = (16, 16),
        in_channels: int = 1,
        embed_dim: int = 384
    ):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.n_patches = (img_size[0] // patch_size[0]) * (img_size[1] // patch_size[1])
        
        self.proj = nn.Conv2d(
            in_channels, embed_dim,
            kernel_size=patch_size,
            stride=patch_size
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.proj(x)  # (B, embed_dim, H', W')
        x = x.flatten(2)  # (B, embed_dim, n_patches)
        x = x.transpose(1, 2)  # (B, n_patches, embed_dim)
        return x


class AudioTransformerEncoder(nn.Module):
    """
    Small Audio Spectrogram Transformer (AST) variant.
    
    Inspired by the original AST but significantly smaller for edge deployment.
    Parameters: ~8M (still lightweight)
    """
    
    def __init__(
        self,
        n_mels: int = 128,
        max_frames: int = 500,
        patch_size: Tuple[int, int] = (16, 16),
        embed_dim: int = 384,
        depth: int = 6,
        num_heads: int = 6,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.embed_dim = embed_dim
        
        # Patch embedding
        self.patch_embed = PatchEmbed(
            img_size=(n_mels, max_frames),
            patch_size=patch_size,
            in_channels=1,
            embed_dim=embed_dim
        )
        n_patches = self.patch_embed.n_patches
        
        # CLS token and positional embedding
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed = nn.Parameter(torch.zeros(1, n_patches + 1, embed_dim))
        self.pos_drop = nn.Dropout(dropout)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=int(embed_dim * mlp_ratio),
            dropout=dropout,
            activation='gelu',
            batch_first=True,
            norm_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=depth)
        
        # Output norm
        self.norm = nn.LayerNorm(embed_dim)
        
        # Initialize
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Mel-spectrogram (batch, n_mels, n_frames) or (batch, 1, n_mels, n_frames)
        
        Returns:
            Embedding (batch, embed_dim)
        """
        if x.dim() == 3:
            x = x.unsqueeze(1)
        
        # Pad to expected size if needed
        _, _, h, w = x.shape
        target_h, target_w = self.patch_embed.img_size
        
        if h != target_h or w != target_w:
            x = F.interpolate(x, size=(target_h, target_w), mode='bilinear', align_corners=False)
        
        # Patch embed
        x = self.patch_embed(x)  # (B, n_patches, embed_dim)
        
        # Add CLS token
        cls_tokens = self.cls_token.expand(x.shape[0], -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        
        # Add positional embedding
        x = x + self.pos_embed
        x = self.pos_drop(x)
        
        # Transformer
        x = self.encoder(x)
        x = self.norm(x)
        
        # Return CLS token embedding
        return x[:, 0]
    
    def get_embedding_dim(self) -> int:
        return self.embed_dim


class AudioEncoder(nn.Module):
    """
    Unified audio encoder interface.
    
    Supports multiple backbone architectures:
    - 'cnn': Lightweight CNN (BirdAudioEncoder)
    - 'ast_tiny': Small AST transformer
    """
    
    ARCHITECTURES = {
        'cnn': BirdAudioEncoder,
        'ast_tiny': AudioTransformerEncoder
    }
    
    def __init__(
        self,
        architecture: str = 'cnn',
        n_mels: int = 128,
        embedding_dim: int = 384,
        pretrained: bool = False,
        **kwargs
    ):
        super().__init__()
        
        if architecture not in self.ARCHITECTURES:
            raise ValueError(f"Unknown architecture: {architecture}. "
                           f"Choose from: {list(self.ARCHITECTURES.keys())}")
        
        encoder_cls = self.ARCHITECTURES[architecture]
        self.encoder = encoder_cls(n_mels=n_mels, embedding_dim=embedding_dim, **kwargs)
        self.embedding_dim = embedding_dim
        
        if pretrained:
            self._load_pretrained(architecture)
    
    def _load_pretrained(self, architecture: str):
        """Load pretrained weights if available."""
        # TODO: Implement pretrained weight loading from checkpoints
        pass
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)
    
    def get_embedding_dim(self) -> int:
        return self.embedding_dim
    
    @torch.no_grad()
    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract features without gradient computation."""
        self.eval()
        return self.forward(x)
    
    def count_parameters(self) -> int:
        """Count trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

