"""
BirdSense Production API Server - Zero-Shot LLM Edition.

NOVEL APPROACH: Uses LLM as PRIMARY identifier for ANY bird species.
No training required - leverages LLM's knowledge of 10,000+ bird species.

FastAPI-based REST API with:
- Zero-shot bird identification via LLM
- Audio file upload and identification
- Live streaming responses (SSE)
- Real-time bird detection stream
- Species database queries
- Health monitoring

Usage:
    uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import io
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncGenerator

import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import soundfile as sf

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio.preprocessor import AudioPreprocessor
from audio.augmentation import AudioAugmenter
from models.audio_classifier import BirdAudioClassifier
from models.novelty_detector import NoveltyDetector
from data.species_db import IndiaSpeciesDatabase
from llm.ollama_client import OllamaConfig, OllamaClient
from llm.zero_shot_identifier import ZeroShotBirdIdentifier, AudioFeatures

# Try importing SAM-Audio
try:
    from audio.sam_audio import SAMAudioEnhancer, SAMAudioConfig
    HAS_SAM_AUDIO = True
except ImportError:
    HAS_SAM_AUDIO = False

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic Models
class IdentificationRequest(BaseModel):
    """Request for bird identification."""
    location_name: Optional[str] = Field(None, description="Location name")
    latitude: Optional[float] = Field(None, description="GPS latitude")
    longitude: Optional[float] = Field(None, description="GPS longitude")
    description: Optional[str] = Field(None, description="User description of the bird")
    month: Optional[int] = Field(None, ge=1, le=12, description="Month of recording")
    use_llm: bool = Field(True, description="Use LLM for zero-shot identification")


class SpeciesPrediction(BaseModel):
    """Single species prediction."""
    rank: int
    species_name: str
    scientific_name: str
    confidence: float
    confidence_percent: float
    reasoning: Optional[str] = None


class IdentificationResponse(BaseModel):
    """Full identification response."""
    request_id: str
    timestamp: str
    audio_duration: float
    audio_quality: str
    quality_score: float
    
    # Main result
    species_name: str
    scientific_name: str
    confidence: float
    confidence_percent: float
    confidence_label: str
    reasoning: str
    
    # Features matched
    key_features: List[str]
    
    # Alternatives
    alternatives: List[Dict[str, Any]]
    
    # Novelty detection
    is_indian_bird: bool
    is_unusual_sighting: bool
    unusual_reason: Optional[str] = None
    
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    llm_available: bool
    zero_shot_ready: bool
    species_count: int
    device: str
    timestamp: str


# Global state
class AppState:
    """Application state container."""
    preprocessor: Optional[AudioPreprocessor] = None
    classifier: Optional[BirdAudioClassifier] = None
    species_db: Optional[IndiaSpeciesDatabase] = None
    zero_shot_identifier: Optional[ZeroShotBirdIdentifier] = None
    sam_audio: Optional[Any] = None
    device: str = "cpu"
    model_loaded: bool = False
    
    # Live detection state
    active_websockets: List[WebSocket] = []
    detected_birds: List[Dict] = []  # Last 50 detections


state = AppState()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="🐦 BirdSense API",
        description="Intelligent Bird Recognition - Zero-Shot LLM Identification",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS for web clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.on_event("startup")
    async def startup():
        """Initialize models on startup."""
        logger.info("🐦 Starting BirdSense API (Zero-Shot LLM Edition)...")
        
        # Device selection
        if torch.cuda.is_available():
            state.device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            state.device = "mps"
        else:
            state.device = "cpu"
        
        logger.info(f"Using device: {state.device}")
        
        # Initialize components
        state.preprocessor = AudioPreprocessor()
        state.species_db = IndiaSpeciesDatabase()
        
        # Initialize Zero-Shot Identifier (MAIN INNOVATION)
        try:
            state.zero_shot_identifier = ZeroShotBirdIdentifier(
                OllamaConfig(model="qwen2.5:3b")
            )
            if state.zero_shot_identifier.initialize():
                logger.info("✅ Zero-shot LLM identifier ready!")
            else:
                logger.warning("⚠️ LLM not available - will use feature-based fallback")
        except Exception as e:
            logger.warning(f"Zero-shot identifier setup failed: {e}")
        
        # Initialize SAM-Audio (optional)
        if HAS_SAM_AUDIO:
            try:
                state.sam_audio = SAMAudioEnhancer()
                state.sam_audio.initialize()
                logger.info("✅ SAM-Audio loaded")
            except Exception as e:
                logger.warning(f"SAM-Audio not available: {e}")
        
        # Initialize CNN classifier as backup
        num_classes = state.species_db.get_num_classes()
        state.classifier = BirdAudioClassifier(num_classes=num_classes)
        state.classifier.to(state.device)
        state.classifier.eval()
        
        state.model_loaded = True
        logger.info("🐦 BirdSense API ready! Zero-shot identification enabled.")
    
    # Serve webapp static files
    webapp_path = Path(__file__).parent.parent / "webapp"
    if webapp_path.exists():
        app.mount("/static", StaticFiles(directory=str(webapp_path)), name="static")
        logger.info(f"Serving webapp from {webapp_path}")
    
    return app


app = create_app()


# Helper functions
def process_audio_file(file_content: bytes) -> tuple:
    """Process uploaded audio file."""
    try:
        audio_io = io.BytesIO(file_content)
        audio, sr = sf.read(audio_io)
        
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        return audio.astype(np.float32), sr
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid audio file: {str(e)}")


async def run_zero_shot_identification(
    audio: np.ndarray,
    sample_rate: int,
    location: Optional[str] = None,
    month: Optional[int] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Run zero-shot identification using LLM."""
    import time
    start_time = time.time()
    
    # Resample if needed
    if sample_rate != 32000:
        import scipy.signal
        num_samples = int(len(audio) * 32000 / sample_rate)
        audio = scipy.signal.resample(audio, num_samples)
        sample_rate = 32000
    
    # Get audio quality
    quality = state.preprocessor.get_audio_quality_assessment(audio, sample_rate)
    
    # Extract audio features
    features = state.zero_shot_identifier.extract_features(audio, sample_rate)
    
    # Zero-shot identification via LLM
    result = state.zero_shot_identifier.identify(
        features=features,
        location=location,
        month=month,
        user_description=description
    )
    
    processing_time = (time.time() - start_time) * 1000
    
    return {
        'audio_duration': float(features.duration),
        'audio_quality': quality['quality_label'],
        'quality_score': float(quality['quality_score']),
        'species_name': str(result.species_name),
        'scientific_name': str(result.scientific_name),
        'confidence': float(result.confidence),
        'confidence_percent': round(float(result.confidence) * 100, 1),
        'confidence_label': str(result.confidence_label),
        'reasoning': str(result.reasoning),
        'key_features': [str(f) for f in result.key_features_matched],
        'alternatives': result.alternative_species,
        'is_indian_bird': bool(result.is_indian_bird),
        'is_unusual_sighting': bool(result.is_unusual_sighting),
        'unusual_reason': str(result.unusual_reason) if result.unusual_reason else None,
        'call_description': str(result.call_description),
        'audio_features': {
            'dominant_frequency': float(features.dominant_frequency_hz),
            'frequency_range': (float(features.frequency_range[0]), float(features.frequency_range[1])),
            'syllables': int(features.num_syllables),
            'syllable_rate': float(features.syllable_rate),
            'is_melodic': bool(features.is_melodic),
            'is_repetitive': bool(features.is_repetitive),
            'snr_db': float(features.estimated_snr_db)
        },
        'processing_time_ms': float(processing_time)
    }


async def stream_identification(
    audio: np.ndarray,
    sample_rate: int,
    location: Optional[str] = None,
    month: Optional[int] = None,
    description: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """Stream identification results using Server-Sent Events."""
    
    # Step 1: Audio analysis
    yield f"data: {json.dumps({'step': 'analyzing', 'message': 'Analyzing audio...'})}\n\n"
    await asyncio.sleep(0.1)
    
    # Resample if needed
    if sample_rate != 32000:
        import scipy.signal
        num_samples = int(len(audio) * 32000 / sample_rate)
        audio = scipy.signal.resample(audio, num_samples)
        sample_rate = 32000
    
    quality = state.preprocessor.get_audio_quality_assessment(audio, sample_rate)
    yield f"data: {json.dumps({'step': 'quality', 'quality': quality['quality_label'], 'score': round(quality['quality_score'], 2), 'snr': round(quality['estimated_snr_db'], 1)})}\n\n"
    
    # Step 2: Feature extraction
    yield f"data: {json.dumps({'step': 'features', 'message': 'Extracting audio features...'})}\n\n"
    await asyncio.sleep(0.1)
    
    features = state.zero_shot_identifier.extract_features(audio, sample_rate)
    
    yield f"data: {json.dumps({'step': 'features_done', 'duration': round(features.duration, 1), 'dominant_freq': round(features.dominant_frequency_hz, 0), 'syllables': features.num_syllables, 'melodic': features.is_melodic, 'repetitive': features.is_repetitive})}\n\n"
    
    # Step 3: Zero-shot LLM identification
    yield f"data: {json.dumps({'step': 'identifying', 'message': 'AI analyzing bird call patterns...'})}\n\n"
    await asyncio.sleep(0.1)
    
    result = state.zero_shot_identifier.identify(
        features=features,
        location=location,
        month=month,
        user_description=description
    )
    
    # Step 4: Send main result
    confidence_pct = round(result.confidence * 100, 1)
    yield f"data: {json.dumps({'step': 'result', 'species': result.species_name, 'scientific': result.scientific_name, 'confidence': confidence_pct, 'confidence_label': result.confidence_label, 'reasoning': result.reasoning, 'key_features': result.key_features_matched, 'call_description': result.call_description, 'is_indian': result.is_indian_bird})}\n\n"
    
    # Step 5: Send alternatives
    if result.alternative_species:
        for i, alt in enumerate(result.alternative_species[:3], 1):
            alt_conf = round(alt.get('confidence', 0.1) * 100, 1)
            yield f"data: {json.dumps({'step': 'alternative', 'rank': i + 1, 'species': alt.get('name', 'Unknown'), 'scientific': alt.get('scientific', ''), 'confidence': alt_conf})}\n\n"
            await asyncio.sleep(0.05)
    
    # Step 6: Novelty alert if unusual
    if result.is_unusual_sighting:
        yield f"data: {json.dumps({'step': 'novelty', 'is_unusual': True, 'is_indian': result.is_indian_bird, 'reason': result.unusual_reason or 'Unusual sighting detected!'})}\n\n"
    elif not result.is_indian_bird:
        yield f"data: {json.dumps({'step': 'novelty', 'is_unusual': True, 'is_indian': False, 'reason': f'{result.species_name} is not typically found in India - exciting observation!'})}\n\n"
    
    # Step 7: Complete
    yield f"data: {json.dumps({'step': 'complete', 'message': 'Analysis complete'})}\n\n"
    
    # Track detection for live stream
    if confidence_pct >= 60:
        detection = {
            'timestamp': datetime.now().isoformat(),
            'species': result.species_name,
            'confidence': confidence_pct,
            'is_indian': result.is_indian_bird
        }
        state.detected_birds.append(detection)
        if len(state.detected_birds) > 50:
            state.detected_birds.pop(0)
        
        # Broadcast to connected websockets
        for ws in state.active_websockets:
            try:
                await ws.send_json(detection)
            except:
                pass


# API Routes
@app.get("/", response_class=JSONResponse)
async def root():
    """API root - welcome message."""
    return {
        "message": "🐦 BirdSense API - Zero-Shot LLM Bird Identification",
        "version": "2.0.0",
        "webapp": "/app",
        "docs": "/docs",
        "features": [
            "Zero-shot identification (10,000+ species)",
            "No training required",
            "Works for ANY bird worldwide",
            "Live streaming results",
            "Novelty detection for rare sightings"
        ]
    }


@app.get("/app", response_class=HTMLResponse)
async def serve_webapp():
    """Serve the main web application."""
    webapp_path = Path(__file__).parent.parent / "webapp" / "index.html"
    if webapp_path.exists():
        return webapp_path.read_text()
    raise HTTPException(status_code=404, detail="Web app not found")


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Check API health and model status."""
    llm_available = False
    if state.zero_shot_identifier:
        llm_available = state.zero_shot_identifier.is_ready
    
    return HealthResponse(
        status="healthy" if state.model_loaded else "initializing",
        llm_available=llm_available,
        zero_shot_ready=state.zero_shot_identifier is not None,
        species_count=10000,  # LLM can identify 10,000+ species
        device=state.device,
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/status")
async def detailed_status():
    """Get detailed system status."""
    return {
        "status": "healthy" if state.model_loaded else "initializing",
        "mode": "zero_shot_llm",
        "llm_model": "qwen2.5:3b",
        "capabilities": {
            "zero_shot_identification": state.zero_shot_identifier is not None,
            "llm_ready": state.zero_shot_identifier.is_ready if state.zero_shot_identifier else False,
            "sam_audio": state.sam_audio is not None,
            "cnn_backup": state.classifier is not None
        },
        "species_capability": "10,000+ species (via LLM knowledge)",
        "device": state.device,
        "recent_detections": len(state.detected_birds)
    }


@app.post("/api/v1/identify")
async def identify_bird(
    audio: UploadFile = File(..., description="Audio file (WAV, MP3, FLAC)"),
    location_name: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    description: Optional[str] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    use_llm: bool = Query(True)
):
    """
    Identify bird species from audio file using ZERO-SHOT LLM.
    
    This is the NOVEL approach - no training required!
    The LLM can identify ANY of 10,000+ bird species worldwide.
    """
    if not state.model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    # Read and process audio
    content = await audio.read()
    audio_data, sr = process_audio_file(content)
    
    # Run zero-shot identification
    result = await run_zero_shot_identification(
        audio_data, 
        sr,
        location=location_name,
        month=month,
        description=description
    )
    
    return {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        **result
    }


@app.post("/api/v1/identify/stream")
async def identify_bird_stream(
    audio: UploadFile = File(...),
    location_name: Optional[str] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    description: Optional[str] = Query(None),
    use_llm: bool = Query(True)
):
    """
    Stream bird identification results using Server-Sent Events.
    
    Provides real-time progress updates as the identification proceeds.
    """
    if not state.model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    content = await audio.read()
    audio_data, sr = process_audio_file(content)
    
    return StreamingResponse(
        stream_identification(
            audio_data, 
            sr,
            location=location_name,
            month=month,
            description=description
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.websocket("/api/v1/live")
async def live_detection_stream(websocket: WebSocket):
    """
    WebSocket for live bird detection stream.
    
    Clients receive real-time notifications when birds are detected
    with confidence >= 60%.
    """
    await websocket.accept()
    state.active_websockets.append(websocket)
    
    try:
        # Send recent detections on connect
        await websocket.send_json({
            "type": "history",
            "detections": state.detected_birds[-10:]
        })
        
        # Keep connection alive
        while True:
            # Wait for any message (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in state.active_websockets:
            state.active_websockets.remove(websocket)


@app.get("/api/v1/detections")
async def get_recent_detections(limit: int = Query(20, ge=1, le=50)):
    """Get recent bird detections (confidence >= 60%)."""
    return {
        "detections": state.detected_birds[-limit:],
        "total": len(state.detected_birds)
    }


@app.get("/api/v1/species/search")
async def search_species(
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search for bird species using LLM knowledge.
    
    This searches across 10,000+ species.
    """
    if not state.zero_shot_identifier or not state.zero_shot_identifier.is_ready:
        # Fallback to local database
        all_species = state.species_db.get_all_species()
        matches = [
            {"name": s.common_name, "scientific": s.scientific_name}
            for s in all_species
            if query.lower() in s.common_name.lower() or query.lower() in s.scientific_name.lower()
        ][:limit]
        return {"results": matches, "source": "local_db"}
    
    # Use LLM for broader search
    prompt = f"List {limit} bird species that match '{query}'. Include both common and scientific names. Format as JSON array."
    
    try:
        response = state.zero_shot_identifier.ollama.generate(prompt)
        # Parse response
        return {"results": response, "source": "llm"}
    except:
        return {"results": [], "source": "error"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
