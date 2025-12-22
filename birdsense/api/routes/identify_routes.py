"""
🐦 BirdSense API - Bird Identification Routes
Developed by Soham

REST endpoints for audio, image, and description-based bird identification.
"""

import base64
import io
import time
import numpy as np
from PIL import Image
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form

from api.models import (
    IdentificationResponse, BirdResult,
    AudioIdentifyRequest, ImageIdentifyRequest, DescriptionIdentifyRequest,
    ErrorResponse
)
from api.auth import get_current_user

# Import analysis functions from main codebase
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from analysis import (
    identify_with_birdnet,
    extract_audio_features,
    hybrid_llm_validation,
    parse_birds,
    deduplicate_birds,
    get_enriched_bird_info,
    fetch_bird_image,
    SAMAudio,
    BIRDNET_AVAILABLE
)
from providers import provider_factory
from prompts import get_audio_prompt, get_image_prompt, get_description_prompt

router = APIRouter(prefix="/identify", tags=["Bird Identification"])


def format_bird_result(bird: dict, location: str = "") -> BirdResult:
    """Convert internal bird dict to API response model."""
    name = bird.get("name", "Unknown")
    scientific = bird.get("scientific_name", "")
    
    # Get enriched info
    enriched = get_enriched_bird_info(name, scientific, location)
    
    return BirdResult(
        name=name,
        scientific_name=scientific,
        confidence=bird.get("confidence", 50),
        reason=bird.get("reason", ""),
        source=bird.get("source", "LLM"),
        image_url=enriched.get("image_url") or fetch_bird_image(name, scientific),
        summary=enriched.get("summary"),
        habitat=enriched.get("habitat"),
        diet=enriched.get("diet"),
        conservation=enriched.get("conservation"),
        fun_facts=enriched.get("fun_facts"),
        india_info=enriched.get("india_info")
    )


# ============ AUDIO IDENTIFICATION ============

@router.post(
    "/audio",
    response_model=IdentificationResponse,
    summary="Identify birds from audio",
    description="Upload audio file or send base64-encoded audio for bird identification using BirdNET + LLM hybrid."
)
async def identify_audio(
    audio_file: Optional[UploadFile] = File(None, description="Audio file (WAV, MP3, etc.)"),
    location: Optional[str] = Form(None, description="Location (e.g., Mumbai, India)"),
    month: Optional[str] = Form(None, description="Month (e.g., December)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Identify birds from audio using the BirdSense hybrid pipeline:
    1. META SAM-Audio source separation
    2. BirdNET spectrogram analysis
    3. LLM validation and enrichment
    
    Supports multiple bird detection from single audio.
    """
    start_time = time.time()
    
    if not audio_file:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    try:
        # Read audio file
        audio_bytes = await audio_file.read()
        filename = audio_file.filename or "unknown"
        content_type = audio_file.content_type or "unknown"
        print(f"📥 Received audio: {len(audio_bytes)} bytes, filename: {filename}, content_type: {content_type}")
        
        # Detect format from extension or content type
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        is_m4a = ext in ['m4a', 'aac', 'mp4'] or 'm4a' in content_type or 'mp4' in content_type
        is_mp3 = ext == 'mp3' or 'mp3' in content_type or 'mpeg' in content_type
        is_wav = ext == 'wav' or 'wav' in content_type
        
        print(f"📋 Format detection: ext={ext}, m4a={is_m4a}, mp3={is_mp3}, wav={is_wav}")
        
        audio_data = None
        sr = 44100  # Default sample rate
        
        # For M4A/AAC/MP3 formats, skip soundfile and go straight to pydub
        if is_m4a or is_mp3:
            print(f"🔄 Detected {ext.upper()} format, using pydub directly...")
            try:
                from pydub import AudioSegment
                # Use format hint for better compatibility
                format_hint = 'mp4' if is_m4a else 'mp3'
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=format_hint)
                sr = audio_segment.frame_rate
                # Handle stereo
                if audio_segment.channels > 1:
                    audio_segment = audio_segment.set_channels(1)
                samples = np.array(audio_segment.get_array_of_samples())
                audio_data = samples.astype(np.float64) / 32768.0
                print(f"✅ pydub: loaded {len(audio_data)} samples at {sr}Hz from {format_hint}")
            except Exception as pydub_err:
                print(f"⚠️ pydub failed for {ext}: {pydub_err}")
                # Try without format hint
                try:
                    audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
                    sr = audio_segment.frame_rate
                    if audio_segment.channels > 1:
                        audio_segment = audio_segment.set_channels(1)
                    samples = np.array(audio_segment.get_array_of_samples())
                    audio_data = samples.astype(np.float64) / 32768.0
                    print(f"✅ pydub (auto-detect): loaded {len(audio_data)} samples at {sr}Hz")
                except Exception as pydub_auto_err:
                    print(f"⚠️ pydub auto-detect also failed: {pydub_auto_err}")
        
        # Method 1: soundfile (best for WAV/FLAC)
        if audio_data is None:
            try:
                import soundfile as sf
                audio_data, sr = sf.read(io.BytesIO(audio_bytes))
                print(f"✅ soundfile: loaded {len(audio_data)} samples at {sr}Hz")
            except Exception as sf_err:
                print(f"⚠️ soundfile failed: {sf_err}")
        
        # Method 2: scipy.io.wavfile (for standard WAV)
        if audio_data is None:
            try:
                from scipy.io import wavfile
                sr, audio_data = wavfile.read(io.BytesIO(audio_bytes))
                audio_data = audio_data.astype(np.float64)
                # Normalize int16 to float
                if audio_data.dtype == np.int16 or np.max(np.abs(audio_data)) > 1:
                    audio_data = audio_data / 32768.0
                print(f"✅ scipy.io.wavfile: loaded {len(audio_data)} samples at {sr}Hz")
            except Exception as wav_err:
                print(f"⚠️ scipy.io.wavfile failed: {wav_err}")
        
        # Method 3: pydub with ffmpeg (last resort)
        if audio_data is None:
            try:
                from pydub import AudioSegment
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
                sr = audio_segment.frame_rate
                if audio_segment.channels > 1:
                    audio_segment = audio_segment.set_channels(1)
                samples = np.array(audio_segment.get_array_of_samples())
                audio_data = samples.astype(np.float64) / 32768.0
                print(f"✅ pydub (fallback): loaded {len(audio_data)} samples at {sr}Hz")
            except Exception as pydub_err:
                print(f"⚠️ pydub fallback failed: {pydub_err}")
        
        if audio_data is None:
            raise ValueError(f"Could not decode audio. Format: {ext}, ContentType: {content_type}. Try converting to MP3 or WAV.")
        
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Ensure float64
        audio_data = audio_data.astype(np.float64)
        
        # Normalize to [-1, 1]
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        
        print(f"✅ Audio ready: {len(audio_data)} samples, {sr}Hz, duration: {len(audio_data)/sr:.2f}s")
        
    except Exception as e:
        print(f"❌ Audio processing error: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing audio: {str(e)}")
    
    # Run identification pipeline
    all_birds = []
    model_info = provider_factory.get_model_info("text")
    
    try:
        # SAM-Audio separation
        sam = SAMAudio()
        separated_bands = sam.separate_multiple_birds(audio_data, sr)
        
        # BirdNET multi-pass analysis
        if BIRDNET_AVAILABLE:
            # Full audio
            full_results = identify_with_birdnet(audio_data, sr, location or "", month or "")
            if full_results:
                all_birds.extend(full_results)
            
            # Each frequency band
            for band in separated_bands[:3]:
                band_audio = band.get("audio")
                if band_audio is not None:
                    band_results = identify_with_birdnet(band_audio, sr, location or "", month or "")
                    for br in band_results:
                        br_name = br.get("name", "").lower()
                        existing = [r.get("name", "").lower() for r in all_birds]
                        if br_name and br_name not in existing:
                            br["source"] = f"BirdNET ({band['band']})"
                            all_birds.append(br)
        
        # Extract features for LLM
        features = extract_audio_features(audio_data, sr)
        
        # LLM validation if BirdNET found results
        if all_birds:
            validated = hybrid_llm_validation(all_birds, features, location or "", month or "")
            if validated:
                all_birds = validated
        else:
            # Fallback to LLM-only
            prompt = get_audio_prompt(provider_factory.active_provider or "ollama").format(
                min_freq=features['min_freq'], max_freq=features['max_freq'],
                peak_freq=features['peak_freq'], freq_range=features['freq_range'],
                pattern=features['pattern'], complexity=features['complexity'],
                syllables=features['syllables'], rhythm=features['rhythm'],
                duration=features['duration'], quality=features['quality'],
                location_info=f"- Location: {location}" if location else "",
                season_info=f"- Season: {month}" if month else ""
            )
            response = provider_factory.call_text(prompt)
            llm_birds = parse_birds(response)
            if llm_birds:
                all_birds = llm_birds
        
        # Deduplicate
        all_birds = deduplicate_birds(all_birds)
        
        # Format results
        bird_results = [format_bird_result(bird, location or "") for bird in all_birds]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return IdentificationResponse(
            success=True,
            birds=bird_results,
            total_birds=len(bird_results),
            processing_time_ms=processing_time,
            model_used=f"{model_info['name']} ({model_info['provider']})"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Identification error: {str(e)}")


@router.post(
    "/audio/base64",
    response_model=IdentificationResponse,
    summary="Identify birds from base64 audio"
)
async def identify_audio_base64(
    request: AudioIdentifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """Identify birds from base64-encoded audio data."""
    start_time = time.time()
    
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(request.audio_base64)
        
        import soundfile as sf
        audio_data, sr = sf.read(io.BytesIO(audio_bytes))
        
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        audio_data = audio_data.astype(np.float64)
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error decoding audio: {str(e)}")
    
    # Same identification logic as above
    all_birds = []
    model_info = provider_factory.get_model_info("text")
    
    try:
        if BIRDNET_AVAILABLE:
            results = identify_with_birdnet(audio_data, sr, request.location or "", request.month or "")
            if results:
                all_birds.extend(results)
        
        if not all_birds:
            features = extract_audio_features(audio_data, sr)
            prompt = get_audio_prompt(provider_factory.active_provider or "ollama").format(
                min_freq=features['min_freq'], max_freq=features['max_freq'],
                peak_freq=features['peak_freq'], freq_range=features['freq_range'],
                pattern=features['pattern'], complexity=features['complexity'],
                syllables=features['syllables'], rhythm=features['rhythm'],
                duration=features['duration'], quality=features['quality'],
                location_info=f"- Location: {request.location}" if request.location else "",
                season_info=f"- Season: {request.month}" if request.month else ""
            )
            response = provider_factory.call_text(prompt)
            llm_birds = parse_birds(response)
            if llm_birds:
                all_birds = llm_birds
        
        all_birds = deduplicate_birds(all_birds)
        bird_results = [format_bird_result(bird, request.location or "") for bird in all_birds]
        
        return IdentificationResponse(
            success=True,
            birds=bird_results,
            total_birds=len(bird_results),
            processing_time_ms=int((time.time() - start_time) * 1000),
            model_used=f"{model_info['name']} ({model_info['provider']})"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Identification error: {str(e)}")


# ============ IMAGE IDENTIFICATION ============

@router.post(
    "/image",
    response_model=IdentificationResponse,
    summary="Identify birds from image",
    description="Upload an image for bird identification using Vision AI."
)
async def identify_image(
    image_file: UploadFile = File(..., description="Image file (JPEG, PNG, etc.)"),
    location: Optional[str] = Form(None, description="Location for India-specific info"),
    current_user: dict = Depends(get_current_user)
):
    """
    Identify birds from an image using Vision AI (LLaVA or GPT-4o).
    
    Features:
    - Multi-bird detection
    - Feature-based analysis (beak, plumage, patterns)
    - India-specific information
    """
    start_time = time.time()
    
    try:
        image_bytes = await image_file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")
    
    model_info = provider_factory.get_model_info("vision")
    
    try:
        prompt = get_image_prompt(provider_factory.active_provider or "ollama")
        response = provider_factory.call_vision(image, prompt)
        
        if not response:
            raise HTTPException(status_code=500, detail="Vision model not responding")
        
        birds = parse_birds(response)
        birds = deduplicate_birds(birds)
        
        bird_results = [format_bird_result(bird, location or "") for bird in birds]
        
        return IdentificationResponse(
            success=True,
            birds=bird_results,
            total_birds=len(bird_results),
            processing_time_ms=int((time.time() - start_time) * 1000),
            model_used=f"{model_info['name']} ({model_info['provider']})"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Identification error: {str(e)}")


@router.post(
    "/image/base64",
    response_model=IdentificationResponse,
    summary="Identify birds from base64 image"
)
async def identify_image_base64(
    request: ImageIdentifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """Identify birds from base64-encoded image data."""
    start_time = time.time()
    
    try:
        image_bytes = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error decoding image: {str(e)}")
    
    model_info = provider_factory.get_model_info("vision")
    
    try:
        prompt = get_image_prompt(provider_factory.active_provider or "ollama")
        response = provider_factory.call_vision(image, prompt)
        
        if not response:
            raise HTTPException(status_code=500, detail="Vision model not responding")
        
        birds = parse_birds(response)
        birds = deduplicate_birds(birds)
        bird_results = [format_bird_result(bird, request.location or "") for bird in birds]
        
        return IdentificationResponse(
            success=True,
            birds=bird_results,
            total_birds=len(bird_results),
            processing_time_ms=int((time.time() - start_time) * 1000),
            model_used=f"{model_info['name']} ({model_info['provider']})"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Identification error: {str(e)}")


# ============ DESCRIPTION IDENTIFICATION ============

@router.post(
    "/description",
    response_model=IdentificationResponse,
    summary="Identify birds from text description",
    description="Describe a bird's appearance, behavior, or sounds for identification."
)
async def identify_description(
    request: DescriptionIdentifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Identify birds from a text description.
    
    Describe features like:
    - Colors and patterns
    - Size (sparrow-sized, crow-sized, etc.)
    - Behavior (feeding, flying, singing)
    - Sounds (chirping, whistling, etc.)
    - Location and habitat
    """
    start_time = time.time()
    
    if len(request.description) < 10:
        raise HTTPException(status_code=400, detail="Description too short. Please provide more details.")
    
    model_info = provider_factory.get_model_info("text")
    
    try:
        prompt_template = get_description_prompt(provider_factory.active_provider or "ollama")
        prompt = prompt_template.format(description=request.description)
        
        response = provider_factory.call_text(prompt)
        
        if not response:
            raise HTTPException(status_code=500, detail="Text model not responding")
        
        birds = parse_birds(response)
        birds = deduplicate_birds(birds)
        bird_results = [format_bird_result(bird, request.location or "") for bird in birds]
        
        return IdentificationResponse(
            success=True,
            birds=bird_results,
            total_birds=len(bird_results),
            processing_time_ms=int((time.time() - start_time) * 1000),
            model_used=f"{model_info['name']} ({model_info['provider']})"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Identification error: {str(e)}")

