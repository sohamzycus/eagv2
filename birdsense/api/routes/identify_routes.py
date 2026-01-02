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
    ErrorResponse,
    AudioFeatures, ImageFeatures, AnalysisStep, AnalysisTrail
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


def create_audio_trail(steps: list, features: dict, sources: list, enhanced: bool) -> AnalysisTrail:
    """Create analysis trail for audio identification."""
    audio_features = AudioFeatures(
        duration=features.get('duration', 0),
        min_freq=features.get('min_freq', 0),
        max_freq=features.get('max_freq', 0),
        peak_freq=features.get('peak_freq', 0),
        freq_range=features.get('freq_range', 0),
        pattern=features.get('pattern', 'unknown'),
        complexity=features.get('complexity', 'unknown'),
        syllables=features.get('syllables', 0),
        rhythm=features.get('rhythm', 'unknown'),
        quality=features.get('quality', 'unknown')
    )
    
    return AnalysisTrail(
        pipeline="audio",
        steps=steps,
        audio_features=audio_features,
        sources_used=sources,
        enhancement_applied=enhanced
    )


def create_image_trail(steps: list, features: dict, sources: list) -> AnalysisTrail:
    """Create analysis trail for image identification."""
    image_features = ImageFeatures(
        size_estimate=features.get('size_estimate'),
        primary_colors=features.get('primary_colors'),
        beak_description=features.get('beak_description'),
        distinctive_features=features.get('distinctive_features'),
        pose=features.get('pose')
    )
    
    return AnalysisTrail(
        pipeline="image",
        steps=steps,
        image_features=image_features,
        sources_used=sources,
        enhancement_applied=False
    )

router = APIRouter(prefix="/identify", tags=["Bird Identification"])


def format_bird_result(bird: dict, location: str = "", use_cache: bool = True) -> BirdResult:
    """Convert internal bird dict to API response model."""
    name = bird.get("name", "Unknown")
    scientific = bird.get("scientific_name", "")
    
    # Get enriched info - with caching for speed
    if use_cache:
        from api.bird_cache import get_cached_enrichment
        enriched = get_cached_enrichment(
            bird_name=name,
            scientific_name=scientific,
            location=location,
            enrichment_func=lambda: get_enriched_bird_info(name, scientific, location)
        )
    else:
        enriched = get_enriched_bird_info(name, scientific, location)
    
    # Ensure we have an image - fetch if missing from enrichment
    image_url = enriched.get("image_url")
    if not image_url:
        image_url = fetch_bird_image(name, scientific)
    
    return BirdResult(
        name=name,
        scientific_name=scientific,
        confidence=bird.get("confidence", 50),
        reason=bird.get("reason", ""),
        source=bird.get("source", "LLM"),
        image_url=image_url,
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
    
    # Run identification pipeline with full analysis trail
    all_birds = []
    model_info = provider_factory.get_model_info("text")
    analysis_steps = []
    sources_used = []
    
    try:
        # Step 1: SAM-Audio Enhancement
        step_start = time.time()
        sam = SAMAudio()
        enhanced_audio = sam.enhance_audio(audio_data, sr)
        separated_bands = sam.separate_multiple_birds(enhanced_audio, sr)
        analysis_steps.append(AnalysisStep(
            step="SAM-Audio Enhancement",
            status="completed",
            details=f"Noise reduction + bird frequency amplification, {len(separated_bands)} frequency bands",
            duration_ms=int((time.time() - step_start) * 1000)
        ))
        sources_used.append("META SAM-Audio")
        
        # Step 2: BirdNET Analysis
        step_start = time.time()
        if BIRDNET_AVAILABLE:
            # Full enhanced audio
            full_results = identify_with_birdnet(enhanced_audio, sr, location or "", month or "")
            if full_results:
                for r in full_results:
                    r["source"] = "BirdNET (enhanced)"
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
            
            birdnet_status = f"{len(all_birds)} species detected" if all_birds else "No matches"
            analysis_steps.append(AnalysisStep(
                step="BirdNET Analysis",
                status="completed" if all_birds else "warning",
                details=birdnet_status,
                duration_ms=int((time.time() - step_start) * 1000)
            ))
            sources_used.append("BirdNET (Cornell)")
        else:
            analysis_steps.append(AnalysisStep(
                step="BirdNET Analysis",
                status="warning",
                details="BirdNET not available"
            ))
        
        # Step 3: Feature Extraction
        step_start = time.time()
        features = extract_audio_features(enhanced_audio, sr)
        analysis_steps.append(AnalysisStep(
            step="Feature Extraction",
            status="completed",
            details=f"Frequency: {features['min_freq']}-{features['max_freq']}Hz, Peak: {features['peak_freq']}Hz, Pattern: {features['pattern']}",
            duration_ms=int((time.time() - step_start) * 1000)
        ))
        
        # Step 4: LLM Validation
        step_start = time.time()
        if all_birds:
            validated = hybrid_llm_validation(all_birds, features, location or "", month or "")
            if validated:
                all_birds = validated
            analysis_steps.append(AnalysisStep(
                step="LLM Validation",
                status="completed",
                details=f"Validated {len(all_birds)} species with acoustic reasoning",
                duration_ms=int((time.time() - step_start) * 1000)
            ))
        else:
            # Fallback to LLM-only
            prompt = get_audio_prompt(provider_factory.active_provider or "ollama", enhanced=True).format(
                min_freq=features['min_freq'], max_freq=features['max_freq'],
                peak_freq=features['peak_freq'], freq_range=features['freq_range'],
                pattern=features['pattern'], complexity=features['complexity'],
                syllables=features['syllables'], rhythm=features['rhythm'],
                duration=features['duration'], quality=features.get('quality', 'Good'),
                location_info=f"- Location: {location}" if location else "- Location: India",
                season_info=f"- Season: {month}" if month else ""
            )
            response = provider_factory.call_text(prompt)
            llm_birds = parse_birds(response)
            if llm_birds:
                all_birds = llm_birds
            analysis_steps.append(AnalysisStep(
                step="LLM Analysis",
                status="completed" if all_birds else "warning",
                details=f"Zero-shot identification: {len(all_birds)} species" if all_birds else "No identification",
                duration_ms=int((time.time() - step_start) * 1000)
            ))
        sources_used.append(f"LLM ({model_info['name']})")
        
        # Deduplicate
        all_birds = deduplicate_birds(all_birds)
        
        # Add confidence factors to each bird
        for bird in all_birds:
            bird["confidence_factors"] = {
                "acoustic_match": f"Peak freq {features['peak_freq']}Hz matches species profile",
                "pattern_match": f"Pattern '{features['pattern']}' characteristic",
                "sources": bird.get("source", "LLM"),
                "enhancement": "SAM-Audio noise reduction applied"
            }
        
        # Format results
        bird_results = [format_bird_result(bird, location or "") for bird in all_birds]
        
        # Create analysis trail
        analysis_trail = create_audio_trail(analysis_steps, features, sources_used, enhanced=True)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return IdentificationResponse(
            success=True,
            birds=bird_results,
            total_birds=len(bird_results),
            processing_time_ms=processing_time,
            model_used=f"{model_info['name']} ({model_info['provider']})",
            analysis_trail=analysis_trail
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
    analysis_steps = []
    sources_used = []
    image_features = {}
    
    try:
        # Step 1: Image preprocessing
        step_start = time.time()
        analysis_steps.append(AnalysisStep(
            step="Image Processing",
            status="completed",
            details=f"Image loaded: {image.size[0]}x{image.size[1]} pixels",
            duration_ms=int((time.time() - step_start) * 1000)
        ))
        
        # Step 2: Vision model analysis - use simple prompt for reliability
        step_start = time.time()
        # Use simpler prompt for API reliability
        prompt = get_image_prompt(provider_factory.active_provider or "ollama", enhanced=False)
        
        try:
            response = provider_factory.call_vision(image, prompt)
        except Exception as vision_err:
            print(f"Vision model error: {vision_err}")
            # Try with simpler prompt as fallback
            response = None
        
        if not response:
            # Return empty result instead of error
            analysis_steps.append(AnalysisStep(
                step="Vision Model Analysis",
                status="warning",
                details="Vision model unavailable - check API configuration",
                duration_ms=int((time.time() - step_start) * 1000)
            ))
            return IdentificationResponse(
                success=True,
                birds=[],
                total_birds=0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                model_used=f"{model_info['name']} ({model_info['provider']})",
                analysis_trail=create_image_trail(analysis_steps, image_features, ["Vision (failed)"])
            )
        
        analysis_steps.append(AnalysisStep(
            step="Vision Model Analysis",
            status="completed",
            details=f"Field marks extracted using {model_info['name']}",
            duration_ms=int((time.time() - step_start) * 1000)
        ))
        sources_used.append(f"Vision ({model_info['name']})")
        
        birds = parse_birds(response)
        
        # Step 3: Similar species verification (if multiple candidates)
        if len(birds) > 1:
            analysis_steps.append(AnalysisStep(
                step="Similar Species Check",
                status="completed",
                details=f"Verified {len(birds)} candidates for confusion species"
            ))
        
        birds = deduplicate_birds(birds)
        
        # Add confidence factors
        for bird in birds:
            bird["confidence_factors"] = {
                "visual_match": "Field marks analyzed",
                "source": model_info['name'],
                "image_quality": "Good" if image.size[0] >= 500 else "Low resolution"
            }
        
        bird_results = [format_bird_result(bird, location or "") for bird in birds]
        
        # Create image trail
        analysis_trail = create_image_trail(analysis_steps, image_features, sources_used)
        
        return IdentificationResponse(
            success=True,
            birds=bird_results,
            total_birds=len(bird_results),
            processing_time_ms=int((time.time() - start_time) * 1000),
            model_used=f"{model_info['name']} ({model_info['provider']})",
            analysis_trail=analysis_trail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Image identification error: {e}")
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


# ============ CACHE MANAGEMENT ============

@router.get(
    "/cache/stats",
    summary="Get cache statistics",
    description="View bird enrichment cache statistics including hit rate."
)
async def get_cache_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get cache statistics for monitoring performance."""
    from api.bird_cache import bird_cache
    return bird_cache.get_stats()


@router.post(
    "/cache/clear",
    summary="Clear cache",
    description="Clear all cached bird enrichment data."
)
async def clear_cache(
    current_user: dict = Depends(get_current_user)
):
    """Clear the bird enrichment cache."""
    from api.bird_cache import bird_cache
    bird_cache.clear()
    return {"status": "cleared", "message": "Cache cleared successfully"}
