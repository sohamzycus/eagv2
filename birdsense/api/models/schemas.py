"""
🐦 BirdSense API - Pydantic Models
Developed by Soham

Request/Response schemas for the REST API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============ AUTH MODELS ============

class UserLogin(BaseModel):
    """Login request payload."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=6, description="Password")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "birder",
                "password": "password123"
            }
        }
    }


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiry in seconds")


class UserInfo(BaseModel):
    """User information."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True


# ============ BIRD IDENTIFICATION MODELS ============

class BirdResult(BaseModel):
    """Single bird identification result."""
    name: str = Field(..., description="Common name of the bird")
    scientific_name: Optional[str] = Field(None, description="Scientific name (Genus species)")
    confidence: int = Field(..., ge=0, le=100, description="Confidence percentage")
    reason: Optional[str] = Field(None, description="Reasoning for identification")
    source: str = Field("LLM", description="Detection source (BirdNET, LLM, etc.)")
    image_url: Optional[str] = Field(None, description="Image URL from Wikipedia/iNaturalist")
    
    # Enrichment data
    summary: Optional[str] = Field(None, description="Species summary")
    habitat: Optional[str] = Field(None, description="Habitat information")
    diet: Optional[str] = Field(None, description="Diet information")
    conservation: Optional[str] = Field(None, description="IUCN conservation status")
    fun_facts: Optional[List[str]] = Field(None, description="Interesting facts")
    
    # India-specific
    india_info: Optional[Dict[str, Any]] = Field(None, description="India-specific information")


class IdentificationResponse(BaseModel):
    """Bird identification response."""
    success: bool
    birds: List[BirdResult] = Field(default_factory=list)
    total_birds: int = 0
    processing_time_ms: int = Field(description="Processing time in milliseconds")
    model_used: str = Field(description="Model used for identification")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "birds": [{
                    "name": "House Sparrow",
                    "scientific_name": "Passer domesticus",
                    "confidence": 85,
                    "reason": "Brown plumage with black bib",
                    "source": "GPT-4o",
                    "image_url": "https://upload.wikimedia.org/...",
                    "conservation": "LC"
                }],
                "total_birds": 1,
                "processing_time_ms": 2500,
                "model_used": "GPT-4o (Azure)",
                "timestamp": "2024-12-22T10:30:00Z"
            }
        }
    }


# ============ REQUEST MODELS ============

class AudioIdentifyRequest(BaseModel):
    """Audio identification request (for JSON payload)."""
    audio_base64: str = Field(..., description="Base64 encoded audio data")
    sample_rate: int = Field(44100, description="Audio sample rate in Hz")
    location: Optional[str] = Field(None, description="Location (e.g., Mumbai, India)")
    month: Optional[str] = Field(None, description="Month (e.g., March)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "audio_base64": "UklGRiQAAABXQVZFZm10...",
                "sample_rate": 44100,
                "location": "Mumbai, India",
                "month": "December"
            }
        }
    }


class ImageIdentifyRequest(BaseModel):
    """Image identification request (for JSON payload)."""
    image_base64: str = Field(..., description="Base64 encoded image data")
    location: Optional[str] = Field(None, description="Location for India-specific info")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "image_base64": "/9j/4AAQSkZJRgABAQAA...",
                "location": "Kerala, India"
            }
        }
    }


class DescriptionIdentifyRequest(BaseModel):
    """Description-based identification request."""
    description: str = Field(..., min_length=10, description="Bird description")
    location: Optional[str] = Field(None, description="Location context")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "description": "Small bird with bright yellow body and black wings. Seen near a sunflower field.",
                "location": "Rajasthan, India"
            }
        }
    }


# ============ STATUS MODELS ============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    birdnet_available: bool
    llm_backend: str
    llm_status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: str
    error_code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

