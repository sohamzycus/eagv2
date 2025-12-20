"""
BirdSense Production API Server.

FastAPI-based REST API with:
- Audio file upload and identification
- Streaming responses (SSE)
- LLM-enhanced reasoning
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
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
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
from llm.reasoning import BirdReasoningEngine, ReasoningContext
from audio.sam_audio import SAMAudioEnhancer, SAMAudioConfig

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
    use_llm: bool = Field(True, description="Use LLM for enhanced reasoning")


class SpeciesPrediction(BaseModel):
    """Single species prediction."""
    rank: int
    species_id: int
    common_name: str
    scientific_name: str
    hindi_name: Optional[str]
    confidence: float
    call_description: str


class IdentificationResponse(BaseModel):
    """Full identification response."""
    request_id: str
    timestamp: str
    audio_duration: float
    audio_quality: str
    quality_score: float
    
    predictions: List[SpeciesPrediction]
    top_prediction: str
    top_confidence: float
    uncertainty: float
    
    llm_reasoning: Optional[Dict[str, Any]] = None
    novelty_alert: Optional[Dict[str, Any]] = None
    
    processing_time_ms: float


class SpeciesInfo(BaseModel):
    """Species information."""
    id: int
    common_name: str
    scientific_name: str
    hindi_name: Optional[str]
    family: str
    conservation_status: str
    endemic_to_india: bool
    migratory_status: str
    habitats: List[str]
    call_description: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    ollama_available: bool
    species_count: int
    gpu_available: bool
    timestamp: str


# Global state
class AppState:
    """Application state container."""
    preprocessor: Optional[AudioPreprocessor] = None
    classifier: Optional[BirdAudioClassifier] = None
    novelty_detector: Optional[NoveltyDetector] = None
    species_db: Optional[IndiaSpeciesDatabase] = None
    reasoning_engine: Optional[BirdReasoningEngine] = None
    sam_audio: Optional[SAMAudioEnhancer] = None  # SAM-Audio for source separation
    device: str = "cpu"
    model_loaded: bool = False


state = AppState()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="BirdSense API",
        description="Intelligent Bird Recognition System for CSCR Initiative",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS for web clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.on_event("startup")
    async def startup():
        """Initialize models on startup."""
        logger.info("Starting BirdSense API...")
        
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
        
        # Initialize classifier
        num_classes = state.species_db.get_num_classes()
        state.classifier = BirdAudioClassifier(
            num_classes=num_classes,
            encoder_architecture='cnn',
            embedding_dim=384
        )
        state.classifier.to(state.device)
        state.classifier.eval()
        
        # Load trained weights if available
        checkpoint_path = Path("checkpoints/best_calibrated.pt")
        if checkpoint_path.exists():
            checkpoint = torch.load(checkpoint_path, map_location=state.device)
            state.classifier.load_state_dict(checkpoint['model_state_dict'])
            logger.info("Loaded trained model weights")
        else:
            logger.warning("No trained weights found, using random initialization")
        
        # Initialize LLM reasoning
        try:
            # Use qwen2.5:3b as recommended model
            ollama_config = OllamaConfig(model="qwen2.5:3b")
            state.reasoning_engine = BirdReasoningEngine(
                ollama_config=ollama_config,
                species_db=state.species_db
            )
            status = state.reasoning_engine.check_ollama_status()
            if status["status"] == "ready":
                logger.info(f"Ollama ready with model: {ollama_config.model}")
            else:
                logger.warning(f"Ollama not ready: {status}")
        except Exception as e:
            logger.warning(f"LLM reasoning disabled: {e}")
            state.reasoning_engine = None
        
        # Initialize SAM-Audio for improved source separation
        try:
            state.sam_audio = SAMAudioEnhancer()
            if state.sam_audio.initialize():
                logger.info("SAM-Audio loaded for improved source separation")
            else:
                logger.info("SAM-Audio using fallback spectral separation")
        except Exception as e:
            logger.warning(f"SAM-Audio initialization failed: {e}")
            state.sam_audio = None
        
        state.model_loaded = True
        logger.info("BirdSense API ready!")
    
    # Serve webapp static files
    webapp_path = Path(__file__).parent.parent / "webapp"
    if webapp_path.exists():
        app.mount("/app", StaticFiles(directory=str(webapp_path), html=True), name="webapp")
        logger.info(f"Serving webapp from {webapp_path}")
    
    return app


app = create_app()


# Helper functions
def process_audio_file(file_content: bytes) -> tuple:
    """Process uploaded audio file."""
    try:
        # Read audio
        audio_io = io.BytesIO(file_content)
        audio, sr = sf.read(audio_io)
        
        # Convert to mono if stereo
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        return audio.astype(np.float32), sr
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid audio file: {str(e)}")


async def run_identification(
    audio: np.ndarray,
    request: IdentificationRequest
) -> Dict[str, Any]:
    """Run full identification pipeline."""
    import time
    start_time = time.time()
    
    # Preprocess
    result = state.preprocessor.process(audio, return_waveform=True)
    mel_specs = result['mel_specs']
    
    # Get audio quality
    sr = state.preprocessor.config.sample_rate
    quality = state.preprocessor.get_audio_quality_assessment(audio, sr)
    
    # Run classifier
    predictions_list = []
    embeddings_list = []
    
    with torch.no_grad():
        for mel_spec in mel_specs:
            x = torch.tensor(mel_spec).unsqueeze(0).to(state.device)
            preds = state.classifier.predict(x, top_k=10)
            predictions_list.append(preds)
            embeddings_list.append(preds['embeddings'])
    
    # Aggregate predictions
    if len(predictions_list) == 1:
        top_indices = predictions_list[0]['top_indices'][0].cpu().tolist()
        top_probs = predictions_list[0]['top_probabilities'][0].cpu().tolist()
        uncertainty = float(predictions_list[0]['uncertainty'][0])
        embedding = predictions_list[0]['embeddings'][0]
    else:
        # Average across chunks
        all_probs = torch.stack([p['top_probabilities'][0] for p in predictions_list])
        avg_probs = all_probs.mean(dim=0).cpu()
        top_probs, reorder = torch.sort(avg_probs, descending=True)
        top_probs = top_probs.tolist()
        top_indices = predictions_list[0]['top_indices'][0][reorder].cpu().tolist()
        uncertainty = float(np.mean([p['uncertainty'][0].item() for p in predictions_list]))
        embedding = torch.stack([e[0] for e in embeddings_list]).mean(dim=0)
    
    # Build species predictions
    species_predictions = []
    for rank, (idx, prob) in enumerate(zip(top_indices[:5], top_probs[:5]), 1):
        species = state.species_db.get_species(idx)
        if species:
            species_predictions.append({
                'rank': rank,
                'species_id': idx,
                'common_name': species.common_name,
                'scientific_name': species.scientific_name,
                'hindi_name': species.hindi_name,
                'confidence': float(prob),
                'call_description': species.call_description
            })
    
    response = {
        'audio_duration': result['duration'],
        'audio_quality': quality['quality_label'],
        'quality_score': quality['quality_score'],
        'predictions': species_predictions,
        'top_prediction': species_predictions[0]['common_name'] if species_predictions else 'Unknown',
        'top_confidence': float(top_probs[0]) if top_probs else 0.0,
        'uncertainty': uncertainty
    }
    
    # LLM reasoning
    if request.use_llm and state.reasoning_engine:
        try:
            context = ReasoningContext(
                audio_predictions=[(p['species_id'], p['confidence']) for p in species_predictions],
                audio_quality=quality['quality_label'],
                latitude=request.latitude,
                longitude=request.longitude,
                location_name=request.location_name,
                month=request.month,
                user_description=request.description
            )
            
            reasoning_result = state.reasoning_engine.reason(context)
            
            response['llm_reasoning'] = {
                'species': reasoning_result.species_name,
                'confidence': reasoning_result.confidence,
                'confidence_level': 'high' if reasoning_result.confidence > 0.7 else 
                                   'medium' if reasoning_result.confidence > 0.4 else 'low',
                'reasoning': reasoning_result.reasoning,
                'alternatives': [a[0] for a in reasoning_result.alternative_species],
                'novelty_flag': reasoning_result.novelty_flag,
                'novelty_explanation': reasoning_result.novelty_explanation
            }
            
            # Update confidence based on LLM reasoning
            if reasoning_result.confidence > response['top_confidence']:
                response['top_confidence'] = reasoning_result.confidence
                response['top_prediction'] = reasoning_result.species_name
            
        except Exception as e:
            logger.error(f"LLM reasoning error: {e}")
            response['llm_reasoning'] = {'error': str(e)}
    
    processing_time = (time.time() - start_time) * 1000
    response['processing_time_ms'] = processing_time
    
    return response


async def stream_identification(
    audio: np.ndarray,
    request: IdentificationRequest
) -> AsyncGenerator[str, None]:
    """Stream identification results using Server-Sent Events."""
    
    # Step 1: Audio analysis
    yield f"data: {json.dumps({'step': 'analyzing', 'message': 'Analyzing audio quality...'})}\n\n"
    await asyncio.sleep(0.1)
    
    sr = state.preprocessor.config.sample_rate
    quality = state.preprocessor.get_audio_quality_assessment(audio, sr)
    
    yield f"data: {json.dumps({'step': 'quality', 'quality': quality['quality_label'], 'score': quality['quality_score']})}\n\n"
    
    # Step 2: Preprocessing
    yield f"data: {json.dumps({'step': 'preprocessing', 'message': 'Generating spectrogram...'})}\n\n"
    await asyncio.sleep(0.1)
    
    result = state.preprocessor.process(audio)
    mel_specs = result['mel_specs']
    
    yield f"data: {json.dumps({'step': 'preprocessed', 'chunks': len(mel_specs), 'duration': result['duration']})}\n\n"
    
    # Step 3: Neural network inference
    yield f"data: {json.dumps({'step': 'classifying', 'message': 'Running neural network...'})}\n\n"
    await asyncio.sleep(0.1)
    
    with torch.no_grad():
        x = torch.tensor(mel_specs[0]).unsqueeze(0).to(state.device)
        preds = state.classifier.predict(x, top_k=5)
    
    # Build predictions
    top_indices = preds['top_indices'][0].cpu().tolist()
    top_probs = preds['top_probabilities'][0].cpu().tolist()
    
    predictions = []
    for rank, (idx, prob) in enumerate(zip(top_indices, top_probs), 1):
        species = state.species_db.get_species(idx)
        if species:
            pred = {
                'rank': rank,
                'species': species.common_name,
                'confidence': round(float(prob) * 100, 1)
            }
            predictions.append(pred)
            yield f"data: {json.dumps({'step': 'prediction', 'prediction': pred})}\n\n"
            await asyncio.sleep(0.05)
    
    # Step 4: LLM reasoning (if enabled)
    if request.use_llm and state.reasoning_engine:
        yield f"data: {json.dumps({'step': 'reasoning', 'message': 'Consulting AI for analysis...'})}\n\n"
        
        try:
            context = ReasoningContext(
                audio_predictions=[(idx, prob) for idx, prob in zip(top_indices, top_probs)],
                audio_quality=quality['quality_label'],
                location_name=request.location_name,
                month=request.month
            )
            
            # Stream reasoning from LLM
            reasoning_result = state.reasoning_engine.reason(context)
            
            yield f"data: {json.dumps({'step': 'llm_result', 'species': reasoning_result.species_name, 'confidence': round(reasoning_result.confidence * 100, 1), 'reasoning': reasoning_result.reasoning})}\n\n"
            
            if reasoning_result.novelty_flag:
                yield f"data: {json.dumps({'step': 'novelty_alert', 'message': reasoning_result.novelty_explanation})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'step': 'llm_error', 'error': str(e)})}\n\n"
    
    # Step 5: Complete
    final_result = {
        'step': 'complete',
        'top_species': predictions[0]['species'] if predictions else 'Unknown',
        'confidence': predictions[0]['confidence'] if predictions else 0,
        'all_predictions': predictions
    }
    yield f"data: {json.dumps(final_result)}\n\n"


# API Routes
@app.get("/", response_class=JSONResponse)
async def root():
    """API root - welcome message."""
    return {
        "message": "🐦 BirdSense API - Intelligent Bird Recognition",
        "version": "1.0.0",
        "webapp": "/app",  # Web interface for researchers
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Check API health and model status."""
    ollama_available = False
    if state.reasoning_engine:
        try:
            status = state.reasoning_engine.check_ollama_status()
            ollama_available = status.get("status") == "ready"
        except:
            pass
    
    return HealthResponse(
        status="healthy" if state.model_loaded else "initializing",
        model_loaded=state.model_loaded,
        ollama_available=ollama_available,
        species_count=state.species_db.get_num_classes() if state.species_db else 0,
        gpu_available=torch.cuda.is_available(),
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/status")
async def detailed_status():
    """Get detailed system status."""
    return {
        "status": "healthy" if state.model_loaded else "initializing",
        "components": {
            "classifier": state.classifier is not None,
            "preprocessor": state.preprocessor is not None,
            "species_db": state.species_db is not None,
            "llm_reasoning": state.reasoning_engine is not None,
            "sam_audio": state.sam_audio is not None
        },
        "device": state.device,
        "species_count": state.species_db.get_num_classes() if state.species_db else 0,
        "sam_audio_available": state.sam_audio.processor.is_available() if state.sam_audio else False
    }


@app.post("/api/v1/identify", response_model=IdentificationResponse)
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
    Identify bird species from audio file.
    
    Upload an audio recording and receive species predictions
    with confidence scores and optional LLM-enhanced reasoning.
    """
    if not state.model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    # Read and process audio
    content = await audio.read()
    audio_data, sr = process_audio_file(content)
    
    # Create request
    request = IdentificationRequest(
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
        description=description,
        month=month,
        use_llm=use_llm
    )
    
    # Run identification
    result = await run_identification(audio_data, request)
    
    # Build response
    return IdentificationResponse(
        request_id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        audio_duration=result['audio_duration'],
        audio_quality=result['audio_quality'],
        quality_score=result['quality_score'],
        predictions=[SpeciesPrediction(**p) for p in result['predictions']],
        top_prediction=result['top_prediction'],
        top_confidence=result['top_confidence'],
        uncertainty=result['uncertainty'],
        llm_reasoning=result.get('llm_reasoning'),
        novelty_alert=result.get('novelty_alert'),
        processing_time_ms=result['processing_time_ms']
    )


@app.post("/api/v1/identify/stream")
async def identify_bird_stream(
    audio: UploadFile = File(...),
    location_name: Optional[str] = Query(None),
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
    
    request = IdentificationRequest(
        location_name=location_name,
        use_llm=use_llm
    )
    
    return StreamingResponse(
        stream_identification(audio_data, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@app.get("/api/v1/species", response_model=List[SpeciesInfo])
async def list_species(
    endemic_only: bool = Query(False, description="Filter to India endemic species"),
    habitat: Optional[str] = Query(None, description="Filter by habitat")
):
    """List all supported bird species."""
    if not state.species_db:
        raise HTTPException(status_code=503, detail="Database not loaded")
    
    species_list = state.species_db.get_all_species()
    
    if endemic_only:
        species_list = [s for s in species_list if s.endemic_to_india]
    
    if habitat:
        species_list = [s for s in species_list 
                       if any(habitat.lower() in h.lower() for h in s.habitats)]
    
    return [
        SpeciesInfo(
            id=s.id,
            common_name=s.common_name,
            scientific_name=s.scientific_name,
            hindi_name=s.hindi_name,
            family=s.family,
            conservation_status=s.conservation_status,
            endemic_to_india=s.endemic_to_india,
            migratory_status=s.migratory_status,
            habitats=s.habitats,
            call_description=s.call_description
        )
        for s in species_list
    ]


@app.get("/api/v1/species/{species_id}", response_model=SpeciesInfo)
async def get_species(species_id: int):
    """Get details for a specific species."""
    if not state.species_db:
        raise HTTPException(status_code=503, detail="Database not loaded")
    
    species = state.species_db.get_species(species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    
    return SpeciesInfo(
        id=species.id,
        common_name=species.common_name,
        scientific_name=species.scientific_name,
        hindi_name=species.hindi_name,
        family=species.family,
        conservation_status=species.conservation_status,
        endemic_to_india=species.endemic_to_india,
        migratory_status=species.migratory_status,
        habitats=species.habitats,
        call_description=species.call_description
    )


@app.get("/api/v1/species/{species_id}/description")
async def get_species_description(species_id: int):
    """Get AI-generated description for a species."""
    if not state.species_db:
        raise HTTPException(status_code=503, detail="Database not loaded")
    
    species = state.species_db.get_species(species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    
    if state.reasoning_engine:
        try:
            description = state.reasoning_engine.generate_description(species_id)
            return {"species": species.common_name, "description": description}
        except Exception as e:
            return {"species": species.common_name, "description": species.call_description, "error": str(e)}
    
    return {"species": species.common_name, "description": species.call_description}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

