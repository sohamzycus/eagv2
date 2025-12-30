"""
🐦 BirdSense - AI Bird Identification
Developed by Soham

A novel hybrid AI system for bird identification using:
- BirdNET (Cornell Lab) - Audio spectrogram analysis
- META SAM-Audio - Noise filtering & source separation
- Vision Models (LLaVA/GPT-4o) - Image analysis
- Text Models (phi4/GPT-4o) - Reasoning & validation

Supports multiple LLM backends:
- Ollama (Local)
- OpenAI (Public API)
- Azure OpenAI (Enterprise)

Run: python app.py
"""

import gradio as gr
import numpy as np
import time
import threading
from typing import Generator, Tuple, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# Import provider factory (handles all LLM connectivity)
from providers import provider_factory

# Import analysis functions (all identification logic)
from analysis import (
    identify_audio_streaming,
    identify_image_streaming,
    identify_description,
    identify_live_audio_chunk,
    get_enriched_bird_info,
    fetch_bird_image,
    BIRDNET_AVAILABLE
)

# Import feedback system
from feedback import (
    save_feedback,
    get_analytics,
    format_analytics_html
)


# ============ LIVE AUDIO STATE ============
# Thread pool for async enrichment - increased to handle many birds
_enrichment_executor = ThreadPoolExecutor(max_workers=10)

class LiveAudioState:
    """Manages state for live audio streaming with time-based chunking and async enrichment."""
    
    CHUNK_INTERVAL = 3.0  # Process every 3 seconds
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.audio_samples = []  # Raw audio samples
        self.sample_rate = 44100
        self.all_birds = {}  # name -> {bird_data, first_seen, last_seen, count, enrichment}
        self.enrichment_status = {}  # name -> "pending" | "loading" | "done" | "error"
        self.chunk_count = 0  # Number of 3-second chunks processed
        self.start_time = None
        self.last_process_time = None
        self.is_running = False
        self.total_samples = 0
        self._lock = threading.Lock()
    
    def add_audio(self, audio_data: np.ndarray, sr: int):
        """Add audio samples to buffer."""
        if self.start_time is None:
            self.start_time = time.time()
            self.last_process_time = self.start_time
        
        self.sample_rate = sr
        
        # Flatten if needed
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        self.audio_samples.extend(audio_data.tolist())
        self.total_samples += len(audio_data)
    
    def should_process(self) -> bool:
        """Check if 3 seconds have elapsed since last processing."""
        if self.last_process_time is None:
            return False
        
        elapsed = time.time() - self.last_process_time
        return elapsed >= self.CHUNK_INTERVAL
    
    def get_chunk_for_processing(self) -> Tuple[Optional[np.ndarray], int]:
        """Get 3 seconds of audio for processing and clear buffer."""
        if not self.audio_samples:
            return None, 0
        
        # Get samples for 3 seconds
        samples_needed = int(self.sample_rate * self.CHUNK_INTERVAL)
        
        # Take what we have (up to 3 seconds)
        chunk = np.array(self.audio_samples[:samples_needed], dtype=np.float64)
        
        # Keep any overflow for next chunk (sliding window)
        # But also keep last 1 second for context overlap
        overlap_samples = int(self.sample_rate * 1.0)
        if len(self.audio_samples) > overlap_samples:
            self.audio_samples = self.audio_samples[-overlap_samples:]
        else:
            self.audio_samples = []
        
        # Update timing
        self.last_process_time = time.time()
        self.chunk_count += 1
        
        return chunk, self.sample_rate
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since start."""
        if self.start_time is None:
            return 0
        return time.time() - self.start_time
    
    def get_next_chunk_time(self) -> float:
        """Get time until next chunk processing."""
        if self.last_process_time is None:
            return self.CHUNK_INTERVAL
        elapsed = time.time() - self.last_process_time
        return max(0, self.CHUNK_INTERVAL - elapsed)
    
    def _fetch_enrichment(self, bird_key: str, bird_name: str, scientific_name: str):
        """Background task to fetch FULL bird details including India-specific info."""
        try:
            with self._lock:
                self.enrichment_status[bird_key] = "loading"
            
            print(f"   🔄 Fetching details for {bird_name}...")
            
            # Fetch image first (fastest)
            image_url = fetch_bird_image(bird_name, scientific_name)
            
            # Get full enriched info (includes India info)
            info = get_enriched_bird_info(bird_name, scientific_name)
            
            # Extract India-specific info if available
            india_html = ""
            best_locations = ""
            india_info = info.get("india_info")
            found_in_india = False
            
            if india_info and isinstance(india_info, dict):
                found_in_india = india_info.get("found_in_india", False)
                
                if found_in_india:
                    india_parts = []
                    # Local names
                    local_names = india_info.get("local_names", {})
                    if local_names and isinstance(local_names, dict):
                        name_strs = []
                        for lang, lbl in [("hindi", "Hindi"), ("marathi", "Marathi"), ("tamil", "Tamil"), ("kannada", "Kannada"), ("bengali", "Bengali")]:
                            if local_names.get(lang) and local_names[lang].strip():
                                name_strs.append(f"<b>{lbl}:</b> {local_names[lang]}")
                        if name_strs:
                            india_parts.append(f"🗣️ {' | '.join(name_strs[:3])}")
                    if india_info.get("regions"):
                        india_parts.append(f"📍 <b>Regions:</b> {india_info['regions']}")
                    if india_info.get("best_season"):
                        india_parts.append(f"📅 <b>Best time:</b> {india_info['best_season']}")
                    if india_info.get("notable_locations"):
                        best_locations = india_info["notable_locations"]
                        india_parts.append(f"🔭 <b>Birding spots:</b> {best_locations}")
                    
                    india_html = "<br>".join(india_parts) if india_parts else "Common in India"
                else:
                    # Only show "not found" if we have valid info
                    india_html = "🌍 This species is not commonly found in India"
            
            # IUCN Conservation status
            conservation = info.get("conservation", "")
            iucn_display = ""
            if conservation:
                conservation_upper = conservation.upper()
                iucn_labels = {
                    "LC": ("Least Concern", "#22c55e"),
                    "NT": ("Near Threatened", "#84cc16"),
                    "VU": ("Vulnerable", "#f59e0b"),
                    "EN": ("Endangered", "#f97316"),
                    "CR": ("Critically Endangered", "#ef4444")
                }
                for code, (label, color) in iucn_labels.items():
                    if code in conservation_upper:
                        iucn_display = f'<span style="background:{color};color:white;padding:4px 10px;border-radius:6px;font-size:0.85em;font-weight:600">🛡️ IUCN: {label}</span>'
                        break
                if not iucn_display and conservation:
                    iucn_display = f'<span style="background:#64748b;color:white;padding:4px 10px;border-radius:6px;font-size:0.85em">🛡️ {conservation}</span>'
            
            with self._lock:
                if bird_key in self.all_birds:
                    self.all_birds[bird_key]["enrichment"] = {
                        "image_url": image_url or info.get("image_url"),
                        "summary": info.get("summary", ""),
                        "habitat": info.get("habitat", ""),
                        "diet": info.get("diet", ""),
                        "conservation": conservation,
                        "iucn_display": iucn_display,
                        "fun_facts": info.get("fun_facts", []),
                        "found_in_india": found_in_india,
                        "india_html": india_html,
                        "best_locations": best_locations,
                        "range": info.get("range", "")
                    }
                    self.enrichment_status[bird_key] = "done"
                    print(f"   ✅ Enrichment loaded for {bird_name} (India: {found_in_india})")
        except Exception as e:
            print(f"   ⚠️ Enrichment failed for {bird_name}: {e}")
            import traceback
            traceback.print_exc()
            with self._lock:
                self.enrichment_status[bird_key] = "error"
    
    def update_birds(self, new_birds: list):
        """Update bird detections with new results and trigger async enrichment."""
        current_time = self.get_elapsed_time()
        
        for bird in new_birds:
            name = bird.get("name", "")
            if not name:
                continue
            
            bird_key = name.lower()
            
            with self._lock:
                if bird_key in self.all_birds:
                    # Update existing bird
                    self.all_birds[bird_key]["count"] += 1
                    self.all_birds[bird_key]["last_seen"] = current_time
                    self.all_birds[bird_key]["confidence"] = max(
                        self.all_birds[bird_key]["confidence"],
                        bird.get("confidence", 50)
                    )
                else:
                    # New bird detected - add and trigger enrichment
                    self.all_birds[bird_key] = {
                        "name": bird.get("name"),
                        "scientific_name": bird.get("scientific_name", ""),
                        "confidence": bird.get("confidence", 50),
                        "first_seen": current_time,
                        "last_seen": current_time,
                        "count": 1,
                        "source": bird.get("source", "BirdNET"),
                        "enrichment": None  # Will be populated async
                    }
                    self.enrichment_status[bird_key] = "pending"
                    
                    # Trigger async enrichment
                    _enrichment_executor.submit(
                        self._fetch_enrichment,
                        bird_key,
                        bird.get("name", ""),
                        bird.get("scientific_name", "")
                    )
    
    def get_results_html(self) -> str:
        """Generate HTML for current results with FULL rich enrichment details."""
        elapsed = self.get_elapsed_time()
        next_chunk = self.get_next_chunk_time()
        
        # Recording indicator with pulsing animation
        styles = """<style>
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .recording-dot { animation: pulse 1.5s infinite; }
            .loading-spinner { animation: spin 1s linear infinite; display: inline-block; }
        </style>"""
        
        recording_indicator = """<span class='recording-dot' style='display:inline-block;width:12px;height:12px;background:#ef4444;border-radius:50%;margin-right:8px'></span>"""
        
        # Status bar
        status_html = f"""{styles}<div style='padding:12px;background:linear-gradient(135deg,#fef2f2,#fff);border:1px solid #fecaca;border-radius:8px;margin-bottom:12px'>
            <div style='display:flex;justify-content:space-between;align-items:center'>
                <div style='display:flex;align-items:center'>
                    {recording_indicator}
                    <span style='font-weight:600;color:#dc2626'>LIVE</span>
                    <span style='color:#64748b;margin-left:16px'>⏱️ {elapsed:.0f}s</span>
                    <span style='color:#64748b;margin-left:12px'>📊 {self.chunk_count} analyzed</span>
                </div>
                <div style='background:#e2e8f0;padding:4px 12px;border-radius:12px;font-size:0.85em'>
                    Next: <b>{next_chunk:.1f}s</b>
                </div>
            </div>
        </div>"""
        
        if not self.all_birds:
            return status_html + f"""<div style='padding:30px;text-align:center;color:#64748b;background:white;border-radius:8px;border:1px solid #e2e8f0'>
                <div style='font-size:2.5em;margin-bottom:10px'>🔍</div>
                <div style='font-size:1.1em'>Listening for birds...</div>
                <div style='margin-top:8px;font-size:0.9em'>
                    {f"Analyzed {self.chunk_count} chunks so far. " if self.chunk_count > 0 else ""}
                    Detection happens every 3 seconds.
                </div>
            </div>"""
        
        # Sort by confidence
        with self._lock:
            sorted_birds = sorted(self.all_birds.values(), key=lambda x: x["confidence"], reverse=True)
            enrichment_status = dict(self.enrichment_status)
        
        html = status_html + f"""<div style='padding:16px;background:#dcfce7;border-radius:8px;margin-bottom:12px'>
            <h3 style='margin:0'>🐦 Detected: {len(sorted_birds)} species</h3>
        </div>"""
        
        for idx, bird in enumerate(sorted_birds, 1):
            conf = bird["confidence"]
            conf_color = "#22c55e" if conf >= 70 else "#f59e0b" if conf >= 50 else "#ef4444"
            conf_bg = "#dcfce7" if conf >= 70 else "#fef3c7" if conf >= 50 else "#fef2f2"
            bird_key = bird["name"].lower()
            enrich_status = enrichment_status.get(bird_key, "pending")
            enrichment = bird.get("enrichment")
            
            # Time badge
            time_info = f"@{bird['first_seen']:.0f}s"
            if bird["count"] > 1:
                time_info += f" • {bird['count']}× detected"
            
            # Image section - larger like original
            if enrichment and enrichment.get("image_url"):
                image_html = f"""<div style='flex-shrink:0;margin-right:16px'>
                    <img src='{enrichment["image_url"]}' style='width:140px;height:140px;object-fit:cover;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.1)' 
                         onerror="this.onerror=null;this.parentElement.innerHTML='<div style=\\'width:140px;height:140px;background:linear-gradient(135deg,#dbeafe,#e0e7ff);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:3em\\'>🐦</div>'"/>
                </div>"""
            elif enrich_status == "loading":
                image_html = """<div style='flex-shrink:0;margin-right:16px'>
                    <div style='width:140px;height:140px;background:linear-gradient(135deg,#dbeafe,#e0e7ff);border-radius:12px;display:flex;align-items:center;justify-content:center'>
                        <span class='loading-spinner' style='font-size:2.5em'>⏳</span>
                    </div>
                </div>"""
            else:
                image_html = """<div style='flex-shrink:0;margin-right:16px'>
                    <div style='width:140px;height:140px;background:linear-gradient(135deg,#dbeafe,#e0e7ff);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:3em'>🐦</div>
                </div>"""
            
            # Header section
            header_html = f"""<div style='display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:8px'>
                <span style='font-size:1.2em;font-weight:700;color:#1e293b'>#{idx} {bird["name"]}</span>
                <span style='background:{conf_bg};color:{conf_color};padding:4px 12px;border-radius:20px;font-weight:600;font-size:0.85em'>{conf}%</span>
                <span style='background:#e2e8f0;padding:3px 10px;border-radius:4px;font-size:0.8em;color:#475569'>📊 {bird["source"]}</span>
            </div>
            <div style='color:#64748b;font-style:italic;font-size:0.95em'>{bird["scientific_name"]}</div>
            <div style='font-size:0.8em;color:#94a3b8;margin-top:4px'>{time_info}</div>"""
            
            # Full enrichment details section
            details_html = ""
            if enrichment:
                # Summary - full text
                if enrichment.get("summary"):
                    summary = enrichment["summary"]
                    details_html += f"""<div style='color:#475569;font-size:0.9em;line-height:1.5;margin:12px 0;padding:10px;background:#f8fafc;border-radius:8px;border-left:3px solid #3b82f6'>{summary}</div>"""
                
                # IUCN Conservation status - prominent
                if enrichment.get("iucn_display"):
                    details_html += f"""<div style='margin:10px 0'>{enrichment["iucn_display"]}</div>"""
                
                # Geographic Range
                if enrichment.get("range"):
                    details_html += f"""<div style='background:#dbeafe;color:#1e40af;padding:8px 12px;border-radius:6px;font-size:0.9em;margin:8px 0'>🌍 <b>Range:</b> {enrichment["range"]}</div>"""
                
                # Habitat - full
                if enrichment.get("habitat"):
                    details_html += f"""<div style='background:#ecfdf5;color:#065f46;padding:8px 12px;border-radius:6px;font-size:0.9em;margin:8px 0'>🏠 <b>Habitat:</b> {enrichment["habitat"]}</div>"""
                
                # Diet
                if enrichment.get("diet"):
                    details_html += f"""<div style='background:#fef3c7;color:#92400e;padding:8px 12px;border-radius:6px;font-size:0.9em;margin:8px 0'>🍽️ <b>Diet:</b> {enrichment["diet"]}</div>"""
                
                # India info - only show if we have actual info
                if enrichment.get("india_html"):
                    found_in_india = enrichment.get("found_in_india", False)
                    if found_in_india:
                        # Rich India info for birds found in India
                        details_html += f"""<div style='margin:10px 0;padding:12px;background:linear-gradient(135deg,#fff7ed,#ffedd5);border-radius:8px;border-left:3px solid #f97316'>
                            <div style='font-weight:600;color:#c2410c;margin-bottom:8px'>🇮🇳 India Information</div>
                            <div style='color:#7c2d12;font-size:0.9em;line-height:1.6'>{enrichment["india_html"]}</div>
                        </div>"""
                    else:
                        # Subtle note for non-Indian birds
                        details_html += f"""<div style='margin:8px 0;padding:8px 12px;background:#f1f5f9;border-radius:6px;font-size:0.85em;color:#64748b'>{enrichment["india_html"]}</div>"""
                
                # Fun facts
                fun_facts = enrichment.get("fun_facts", [])
                if fun_facts and isinstance(fun_facts, list) and len(fun_facts) > 0:
                    facts_items = "".join([f"<li style='margin:4px 0'>{fact}</li>" for fact in fun_facts[:2] if fact])
                    if facts_items:
                        details_html += f"""<div style='background:#fefce8;padding:10px 12px;border-radius:6px;font-size:0.9em;margin:8px 0'>
                            <b style='color:#854d0e'>💡 Fun Facts:</b>
                            <ul style='margin:6px 0 0 16px;padding:0;color:#713f12'>{facts_items}</ul>
                        </div>"""
            
            elif enrich_status == "loading":
                details_html = """<div style='margin-top:12px;padding:16px;background:#f8fafc;border-radius:8px;text-align:center'>
                    <span class='loading-spinner' style='font-size:1.5em;margin-right:8px'>⏳</span>
                    <span style='color:#64748b'>Loading bird details (image, IUCN status, habitat, India info)...</span>
                </div>"""
            
            # Build the bird card
            html += f"""<div style='padding:20px;background:white;border-radius:16px;margin-bottom:12px;border:1px solid #e2e8f0;box-shadow:0 2px 8px rgba(0,0,0,0.05)'>
                <div style='display:flex;align-items:flex-start'>
                    {image_html}
                    <div style='flex:1;min-width:0'>
                        {header_html}
                    </div>
                </div>
                {details_html}
            </div>"""
        
        return html


# Global state for live audio
live_audio_state = LiveAudioState()


# ============ UI HELPERS ============

def on_backend_change(selection: str) -> str:
    """Handle backend selection change."""
    if selection == "Ollama (Local)":
        provider_factory.set_active("ollama")
    elif selection == "LiteLLM (Enterprise)":
        provider_factory.set_active("cloud")
    else:  # Auto
        provider_factory.set_active("auto")
    return provider_factory.get_status_html()


def submit_feedback(correct: bool, species: str, notes: str) -> str:
    """Submit user feedback."""
    save_feedback({
        "correct": correct,
        "correct_species": species,
        "notes": notes
    })
    return "✅ Thank you for your feedback! This helps improve BirdSense."


def refresh_analytics() -> str:
    """Refresh analytics dashboard."""
    return format_analytics_html()


# ============ CREATE APP ============

def create_app():
    """Create the Gradio application."""
    
    with gr.Blocks(title="BirdSense - By Soham") as app:
        # Header
        gr.Markdown("""
# 🐦 BirdSense - AI Bird Identification
**Developed by Soham**

**META SAM-Audio** | **BirdNET + LLM Hybrid** | **Multi-bird Detection**
""")
        
        # Backend selector and status
        with gr.Row():
            backend_selector = gr.Radio(
                choices=["Auto", "Ollama (Local)", "LiteLLM (Enterprise)"],
                value="Auto",
                label="🔧 LLM Backend",
                scale=2
            )
            status_display = gr.HTML(provider_factory.get_status_html(), scale=3)
        
        backend_selector.change(on_backend_change, [backend_selector], [status_display])
        
        # Tabs
        with gr.Tab("🎤 Live Audio"):
            gr.Markdown("""
### 🔴 Live Bird Detection
**Just click the microphone and start recording!** Birds are detected automatically every 3 seconds.
""")
            with gr.Row():
                with gr.Column(scale=1):
                    live_audio = gr.Audio(
                        sources=["microphone"],
                        type="numpy",
                        label="🎤 Click to Record (Detection starts automatically)",
                        streaming=True,
                        elem_id="live-audio-input"
                    )
                    live_loc = gr.Textbox(
                        label="📍 Location (optional)",
                        placeholder="e.g., Mumbai, India",
                        value=""
                    )
                    live_reset_btn = gr.Button("🔄 Reset Results", variant="secondary")
                with gr.Column(scale=2):
                    live_output = gr.HTML(
                        """<div style='padding:30px;text-align:center;color:#64748b;background:#f8fafc;border-radius:12px'>
                            <div style='font-size:4em;margin-bottom:10px'>🎤</div>
                            <div style='font-size:1.2em;font-weight:500'>Live Bird Detection</div>
                            <div style='margin-top:10px'>Click the <b>microphone button</b> above to start recording.<br>
                            Birds will be identified automatically every 3 seconds.</div>
                        </div>"""
                    )
            
            # Live audio event handlers
            def reset_live_detection():
                """Reset detection results."""
                live_audio_state.reset()
                return """<div style='padding:30px;text-align:center;color:#64748b;background:#f8fafc;border-radius:12px'>
                    <div style='font-size:4em;margin-bottom:10px'>🎤</div>
                    <div style='font-size:1.2em;font-weight:500'>Results Cleared</div>
                    <div style='margin-top:10px'>Click the <b>microphone button</b> to start a new detection session.</div>
                </div>"""
            
            def process_live_audio(audio_chunk, location):
                """Process incoming audio chunks - auto-starts on first audio, analyzes every 3 seconds."""
                if audio_chunk is None:
                    return live_audio_state.get_results_html() if live_audio_state.is_running else """<div style='padding:30px;text-align:center;color:#64748b;background:#f8fafc;border-radius:12px'>
                            <div style='font-size:4em;margin-bottom:10px'>🎤</div>
                            <div style='font-size:1.2em;font-weight:500'>Live Bird Detection</div>
                            <div style='margin-top:10px'>Click the <b>microphone button</b> above to start recording.</div>
                        </div>"""
                
                sr, audio_data = audio_chunk
                
                # Auto-start detection on first audio chunk
                if not live_audio_state.is_running:
                    live_audio_state.reset()
                    live_audio_state.is_running = True
                    print("🎤 Live detection auto-started!")
                
                # Add audio to buffer (accumulates until 3 seconds)
                live_audio_state.add_audio(audio_data, sr)
                
                # Only process when 3 seconds have elapsed
                if live_audio_state.should_process():
                    try:
                        # Get 3-second chunk for processing
                        chunk_audio, chunk_sr = live_audio_state.get_chunk_for_processing()
                        
                        if chunk_audio is not None and len(chunk_audio) > chunk_sr:  # At least 1 second
                            print(f"🎵 Processing chunk #{live_audio_state.chunk_count} @ {live_audio_state.chunk_count * 3}s ({len(chunk_audio)/chunk_sr:.1f}s audio)")
                            
                            # Identify birds in this chunk
                            birds = identify_live_audio_chunk(chunk_audio, chunk_sr, location)
                            
                            if birds:
                                print(f"   ✅ Found: {[b['name'] for b in birds]}")
                            else:
                                print(f"   ⚪ No birds detected")
                            
                            # Update cumulative results
                            live_audio_state.update_birds(birds)
                    except Exception as e:
                        print(f"Live audio processing error: {e}")
                
                return live_audio_state.get_results_html()
            
            live_reset_btn.click(reset_live_detection, [], [live_output])
            live_audio.stream(process_live_audio, [live_audio, live_loc], [live_output])
        
        with gr.Tab("🎵 Audio"):
            gr.Markdown("""
### Audio Identification with META SAM-Audio + BirdNET
- **SAM-Audio**: Isolates bird calls from noise
- **BirdNET (Cornell)**: 6000+ species recognition
- **LLM Validation**: Contextual reasoning
""")
            with gr.Row():
                with gr.Column():
                    audio_in = gr.Audio(
                        sources=["upload", "microphone"],
                        type="numpy",
                        label="Bird Call"
                    )
                    with gr.Row():
                        loc = gr.Textbox(label="Location", placeholder="e.g., Mumbai, India")
                        mon = gr.Dropdown(
                            label="Month",
                            choices=[""] + ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                        )
                    audio_btn = gr.Button("🔍 Identify Birds", variant="primary")
                with gr.Column():
                    audio_out = gr.HTML(
                        "<p style='color:#64748b;padding:40px;text-align:center'>🎵 Upload audio to identify birds</p>"
                    )
            audio_btn.click(identify_audio_streaming, [audio_in, loc, mon], audio_out)
        
        with gr.Tab("📷 Image"):
            gr.Markdown("""
### Image Identification with Vision AI
- **Feature analysis**: Beak, plumage, patterns
- **Multi-bird detection**: All birds in image
- **Species-level ID**: Specific species names
- **India-specific info**: Local names, habitats, birding spots
""")
            with gr.Row():
                with gr.Column():
                    img_in = gr.Image(
                        sources=["upload", "webcam"],
                        type="pil",
                        label="Bird Photo"
                    )
                    img_loc = gr.Textbox(
                        label="📍 Location (optional)", 
                        placeholder="e.g., Mumbai, India - for local names & info"
                    )
                    img_btn = gr.Button("🔍 Identify Birds", variant="primary")
                with gr.Column():
                    img_out = gr.HTML(
                        "<p style='color:#64748b;padding:40px;text-align:center'>📷 Upload image to identify birds</p>"
                    )
            img_btn.click(identify_image_streaming, [img_in, img_loc], img_out)
        
        with gr.Tab("📝 Description"):
            gr.Markdown("### Describe the bird - colors, size, behavior, sounds")
            with gr.Row():
                with gr.Column():
                    desc_in = gr.Textbox(
                        label="Description",
                        lines=4,
                        placeholder="Large blue and yellow parrot with red beak..."
                    )
                    desc_loc = gr.Textbox(
                        label="📍 Location (optional)", 
                        placeholder="e.g., Kerala, India - for local names & info"
                    )
                    desc_btn = gr.Button("🔍 Identify", variant="primary")
                with gr.Column():
                    desc_out = gr.HTML(
                        "<p style='color:#64748b;padding:40px;text-align:center'>📝 Enter description to identify</p>"
                    )
            desc_btn.click(identify_description, [desc_in, desc_loc], desc_out)
        
        with gr.Tab("📝 Feedback"):
            gr.Markdown("""
### Help Improve BirdSense!
Your feedback helps us train better models.
""")
            with gr.Row():
                with gr.Column():
                    feedback_correct = gr.Radio(
                        choices=["✅ Correct", "❌ Incorrect"],
                        label="Was the identification correct?",
                        value="✅ Correct"
                    )
                    feedback_species = gr.Textbox(
                        label="Correct Species (if wrong)",
                        placeholder="Enter the correct species name..."
                    )
                    feedback_notes = gr.Textbox(
                        label="Additional Notes",
                        placeholder="Any other feedback...",
                        lines=2
                    )
                    feedback_btn = gr.Button("📤 Submit Feedback", variant="primary")
                with gr.Column():
                    feedback_result = gr.Markdown("*Submit feedback to help improve the model*")
            
            feedback_btn.click(
                lambda c, s, n: submit_feedback(c == "✅ Correct", s, n),
                [feedback_correct, feedback_species, feedback_notes],
                feedback_result
            )
        
        with gr.Tab("📊 Analytics"):
            gr.Markdown("### Usage Analytics & Model Performance")
            analytics_display = gr.HTML(format_analytics_html())
            refresh_btn = gr.Button("🔄 Refresh Analytics")
            refresh_btn.click(refresh_analytics, outputs=analytics_display)
        
        with gr.Tab("ℹ️ About"):
            birdnet_status = "✅" if BIRDNET_AVAILABLE else "❌"
            gr.Markdown(f"""
### About BirdSense
**Developed by Soham**

A novel hybrid AI system combining:
- **BirdNET (Cornell Lab)** - Spectrogram pattern matching (6000+ species) {birdnet_status}
- **META SAM-Audio** - Noise filtering & bird call isolation
- **Vision Models** - LLaVA 7B (local) or GPT-4o (cloud)
- **Text Models** - phi4 14B (local) or GPT-4o (cloud)

#### 🔧 Backend Options
| Backend | Vision | Text | Quality |
|---------|--------|------|---------|
| Ollama (Local) | LLaVA 7B | phi4 14B | ⭐⭐⭐⭐ |
| Cloud (Azure/OpenAI) | GPT-4o | GPT-4o | ⭐⭐⭐⭐⭐ |

#### 📊 Architecture
```
AUDIO → SAM-Audio → BirdNET → LLM Validation → Results
IMAGE → Vision Model → Feature Analysis → Results
TEXT  → Text Model → Reasoning → Results
```

#### 🙏 Acknowledgments
- Cornell Lab of Ornithology (BirdNET)
- Meta AI (LLaVA)
- OpenAI / Azure (GPT models)
- Ollama team
""")
        
        # Footer
        gr.Markdown("""
---
**🐦 BirdSense by Soham** | Help improve: Submit feedback after each identification!
""")
    
    return app


# ============ MAIN ============

if __name__ == "__main__":
    print("🐦 BirdSense - AI Bird Identification")
    print("=" * 50)
    print("Developed by Soham")
    print("=" * 50)
    print(f"BirdNET: {'✅' if BIRDNET_AVAILABLE else '❌'}")
    print("=" * 50)
    
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, show_error=True)
