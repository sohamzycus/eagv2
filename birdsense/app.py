"""
🐦 BirdSense - Local AI Bird Identification

Features:
- BirdNET (Cornell): Gold-standard audio identification (6000+ species)
- LLaVA: Vision-based image identification
- META SAM-Audio: Source separation for isolating bird calls from noise
- Multi-bird detection: Streaming identification

Requirements:
- Ollama: llava:7b, phi4
- Python: gradio, numpy, scipy, pillow, requests, tensorflow, birdnetlib

Run: python app.py
"""

import gradio as gr
import numpy as np
import scipy.signal as signal
from scipy.ndimage import gaussian_filter1d
from PIL import Image
import requests
import json
import re
import base64
import io
import urllib.parse
import time
import warnings
import tempfile
import os

# Import external prompts (no hardcoding in main app)
from prompts import (
    AUDIO_IDENTIFICATION_PROMPT,
    IMAGE_IDENTIFICATION_PROMPT,
    DESCRIPTION_IDENTIFICATION_PROMPT,
    get_audio_prompt,
    get_image_prompt,
    get_description_prompt,
    MODEL_INFO
)

# Import confusion correction rules (post-ML validation)
from confusion_rules import (
    validate_bird_identification,
    get_confusion_hint,
    CONFUSION_HINTS
)

# Import feedback system for audit & sample collection
from feedback import (
    log_prediction,
    save_feedback,
    save_sample,
    get_analytics,
    format_analytics_html,
    generate_session_id
)

# Suppress warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# ============ BIRDNET SETUP ============
BIRDNET_AVAILABLE = False
birdnet_analyzer = None

try:
    from birdnetlib import Recording
    from birdnetlib.analyzer import Analyzer
    birdnet_analyzer = Analyzer()
    BIRDNET_AVAILABLE = True
    print("✅ BirdNET (Cornell) loaded - 6000+ species!")
except Exception as e:
    print(f"⚠️ BirdNET not available: {e}")
    print("   Audio will use LLM fallback (less accurate)")

# ============ CONFIG ============
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEBUG = True

# Ollama models (for local)
OLLAMA_VISION_MODEL = "llava:7b"
OLLAMA_TEXT_MODEL = "phi4:latest"

# LiteLLM Enterprise API (Zycus - requires VPN)
# Set these via environment variables or .env file
# DO NOT hardcode API keys in source code!
LITELLM_API_KEY = os.environ.get("LITELLM_API_KEY", "")
LITELLM_API_BASE = os.environ.get("LITELLM_API_BASE", "https://litellm-rm.zycus.net")
LITELLM_VISION_MODEL = os.environ.get("LITELLM_VISION_MODEL", "gpt-4o-201124-payg-eastus")
LITELLM_TEXT_MODEL = os.environ.get("LITELLM_TEXT_MODEL", "gpt-5.2-payg-global")

# Try to load from .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
    # Reload after dotenv
    LITELLM_API_KEY = os.environ.get("LITELLM_API_KEY", LITELLM_API_KEY)
    LITELLM_API_BASE = os.environ.get("LITELLM_API_BASE", LITELLM_API_BASE)
    LITELLM_VISION_MODEL = os.environ.get("LITELLM_VISION_MODEL", LITELLM_VISION_MODEL)
    LITELLM_TEXT_MODEL = os.environ.get("LITELLM_TEXT_MODEL", LITELLM_TEXT_MODEL)
except ImportError:
    pass  # dotenv not installed, use environment variables directly

# Active backend selection (can be toggled via UI)
# Options: "ollama", "litellm", "auto"
ACTIVE_BACKEND = "auto"  # Auto selects based on availability

def set_backend(backend: str) -> str:
    """Set the active LLM backend."""
    global ACTIVE_BACKEND
    ACTIVE_BACKEND = backend
    return get_backend_status_html()

def get_effective_backend() -> str:
    """Get the effectively active backend (resolves 'auto')."""
    global ACTIVE_BACKEND, OLLAMA_AVAILABLE, LITELLM_AVAILABLE
    if ACTIVE_BACKEND == "auto":
        if OLLAMA_AVAILABLE:
            return "ollama"
        elif LITELLM_AVAILABLE:
            return "litellm"
        return "none"
    return ACTIVE_BACKEND

def get_model_info(task: str) -> dict:
    """Get info about the model being used for a task (vision/text/audio)."""
    backend = get_effective_backend()
    if backend in MODEL_INFO:
        return MODEL_INFO[backend].get(task, {"name": "Unknown", "provider": backend, "type": task})
    return {"name": "Not Available", "provider": "None", "type": task}

def get_backend_status_html() -> str:
    """Generate HTML status display for current backend - light/pastel theme."""
    backend = get_effective_backend()
    ollama_status = "🟢" if OLLAMA_AVAILABLE else "⚪"
    litellm_status = "🟢" if LITELLM_AVAILABLE else "⚪"
    litellm_key_status = "🔑" if LITELLM_API_KEY else ""
    
    error_html = ""
    
    if backend == "ollama":
        vision_model = "LLaVA 7B"
        text_model = "phi4 14B"
        bg_color = "#ecfdf5"  # Light green
        text_color = "#065f46"
        border_color = "#a7f3d0"
        status_text = "🟢 Ollama (Local)"
        badge_bg = "#d1fae5"
    elif backend == "litellm":
        if LITELLM_AVAILABLE:
            vision_model = "GPT-4o"
            text_model = "GPT-5.2"
            bg_color = "#f3e8ff"  # Light purple
            text_color = "#6b21a8"
            border_color = "#d8b4fe"
            status_text = "🟣 LiteLLM (Enterprise)"
            badge_bg = "#e9d5ff"
        else:
            vision_model = "⚠️"
            text_model = "⚠️"
            bg_color = "#fef3c7"  # Light orange/warning
            text_color = "#92400e"
            border_color = "#fcd34d"
            status_text = "⚠️ LiteLLM (Connecting...)"
            badge_bg = "#fde68a"
            if LITELLM_ERROR:
                error_html = f'<div style="width:100%;margin-top:8px;padding:8px;background:#fef2f2;border-radius:6px;font-size:0.85em;color:#991b1b;">❌ {LITELLM_ERROR}</div>'
    else:
        vision_model = "None"
        text_model = "None"
        bg_color = "#fef2f2"  # Light red
        text_color = "#991b1b"
        border_color = "#fecaca"
        status_text = "⚪ No Backend"
        badge_bg = "#fee2e2"
    
    birdnet_status = "🟢" if BIRDNET_AVAILABLE else "⚪"
    
    return f"""<div style="
        font-family: -apple-system, system-ui, sans-serif;
        padding: 10px 16px;
        background: {bg_color};
        border-radius: 10px;
        border: 1px solid {border_color};
        color: {text_color};
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
    ">
        <span style="font-weight: 600; background: {badge_bg}; padding: 4px 10px; border-radius: 6px;">{status_text}</span>
        <span>Vision: <b>{vision_model}</b></span>
        <span>Text: <b>{text_model}</b></span>
        <span>BirdNET: {birdnet_status}</span>
        <span style="opacity: 0.7; font-size: 0.85em; margin-left: auto;">
            Ollama: {ollama_status} | LiteLLM: {litellm_status} {litellm_key_status}
        </span>
        {error_html}
    </div>"""

def check_ollama_available():
    """Check if Ollama is running."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return resp.status_code == 200
    except:
        return False

LITELLM_ERROR = ""  # Store last error for display

def check_litellm_available():
    """Check if LiteLLM API is configured and accessible."""
    global LITELLM_ERROR
    
    if not LITELLM_API_KEY:
        LITELLM_ERROR = "API key not set. Create .env file with LITELLM_API_KEY"
        print(f"⚠️ LiteLLM: {LITELLM_ERROR}")
        return False
    
    if not LITELLM_API_BASE:
        LITELLM_ERROR = "API base URL not set"
        return False
    
    # Test actual connectivity
    try:
        print(f"🔍 Testing LiteLLM at {LITELLM_API_BASE}...")
        resp = requests.post(
            f"{LITELLM_API_BASE}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {LITELLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LITELLM_TEXT_MODEL,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5
            },
            timeout=15,
            verify=False  # Skip SSL verification for internal endpoints
        )
        if resp.status_code == 200:
            print(f"✅ LiteLLM connected! Model: {LITELLM_TEXT_MODEL}")
            LITELLM_ERROR = ""
            return True
        else:
            LITELLM_ERROR = f"API returned {resp.status_code}: {resp.text[:100]}"
            print(f"⚠️ LiteLLM: {LITELLM_ERROR}")
            return False
    except requests.exceptions.SSLError as e:
        LITELLM_ERROR = "SSL Error - Are you connected to VPN?"
        print(f"⚠️ LiteLLM SSL Error: {e}")
        print("   → This endpoint likely requires VPN access")
        return False
    except requests.exceptions.ConnectionError as e:
        LITELLM_ERROR = "Connection failed - Check VPN/network"
        print(f"⚠️ LiteLLM Connection Error: {e}")
        return False
    except Exception as e:
        LITELLM_ERROR = f"Error: {str(e)[:50]}"
        print(f"⚠️ LiteLLM Error: {e}")
        return False

# Suppress SSL warnings for internal LiteLLM endpoint
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OLLAMA_AVAILABLE = check_ollama_available()
LITELLM_AVAILABLE = check_litellm_available()

print(f"🔧 Config: LITELLM_API_KEY={'set' if LITELLM_API_KEY else 'not set'}, LITELLM_API_BASE={LITELLM_API_BASE}")

if OLLAMA_AVAILABLE:
    print("✅ Using Ollama (local) - LLaVA + phi4")
elif LITELLM_AVAILABLE:
    print(f"✅ Using LiteLLM API - {LITELLM_VISION_MODEL} + {LITELLM_TEXT_MODEL}")
else:
    print("❌ No LLM backend available")

# SAM-Audio config - Updated frequency bands for better owl detection
SAM_FREQ_BANDS = [
    (100, 500, "very_low"),  # Very large birds: owls hooting, bitterns
    (500, 1500, "low"),      # Large birds: crows, pigeons, owl screeches
    (1500, 3000, "medium"),  # Medium birds: thrushes, mynas
    (3000, 6000, "high"),    # Small birds: warblers, finches
    (6000, 10000, "very_high")  # Very small: some warblers
]

def log(msg):
    if DEBUG:
        print(f"[BirdSense] {msg}")


# ============ META SAM-AUDIO ============
# Inspired by Meta's Segment Anything Model - adapted for audio
# Separates overlapping bird calls and removes background noise

class SAMAudio:
    """META SAM-Audio inspired processing for bird call isolation."""
    
    @staticmethod
    def compute_spectrogram(audio: np.ndarray, sr: int) -> tuple:
        """Compute spectrogram for analysis."""
        nperseg = min(1024, len(audio) // 4)
        if nperseg < 64:
            nperseg = 64
        
        f, t, Sxx = signal.spectrogram(audio, sr, nperseg=nperseg, noverlap=nperseg//2)
        return f, t, Sxx
    
    @staticmethod
    def detect_bird_segments(audio: np.ndarray, sr: int) -> list:
        """
        Detect distinct bird call segments in audio.
        Returns list of (start_time, end_time, frequency_band) tuples.
        """
        segments = []
        
        # Compute envelope
        envelope = np.abs(signal.hilbert(audio))
        envelope = gaussian_filter1d(envelope, sigma=int(sr * 0.01))  # 10ms smoothing
        
        # Dynamic threshold
        threshold = np.mean(envelope) + 0.5 * np.std(envelope)
        
        # Find segments above threshold
        above = envelope > threshold
        changes = np.diff(above.astype(int))
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]
        
        # Handle edge cases
        if len(starts) == 0 or len(ends) == 0:
            return [(0, len(audio)/sr, "unknown")]
        
        if starts[0] > ends[0]:
            starts = np.insert(starts, 0, 0)
        if len(starts) > len(ends):
            ends = np.append(ends, len(audio))
        
        # Analyze each segment
        for start, end in zip(starts[:10], ends[:10]):  # Max 10 segments
            if end - start < sr * 0.05:  # Skip very short (<50ms)
                continue
            
            segment = audio[start:end]
            
            # Find dominant frequency
            fft = np.fft.rfft(segment)
            freqs = np.fft.rfftfreq(len(segment), 1/sr)
            peak_freq = freqs[np.argmax(np.abs(fft))]
            
            # Classify by frequency band
            band = "unknown"
            for low, high, name in SAM_FREQ_BANDS:
                if low <= peak_freq <= high:
                    band = name
                    break
            
            segments.append({
                "start": start / sr,
                "end": end / sr,
                "peak_freq": int(peak_freq),
                "band": band,
                "audio": segment
            })
        
        return segments
    
    @staticmethod
    def isolate_bird_call(audio: np.ndarray, sr: int, freq_range: tuple) -> np.ndarray:
        """
        Isolate bird call in specific frequency range.
        SAM-style: segment the "bird" from background noise.
        """
        low, high = freq_range
        nyq = sr / 2
        
        # Bandpass filter
        low_norm = max(low / nyq, 0.01)
        high_norm = min(high / nyq, 0.99)
        
        if low_norm >= high_norm:
            return audio
        
        b, a = signal.butter(4, [low_norm, high_norm], btype='band')
        filtered = signal.filtfilt(b, a, audio)
        
        # Spectral subtraction for noise reduction
        # Estimate noise from quietest 10% of signal
        envelope = np.abs(signal.hilbert(filtered))
        noise_level = np.percentile(envelope, 10)
        
        # Soft mask
        mask = np.clip((envelope - noise_level) / (np.max(envelope) - noise_level + 1e-10), 0, 1)
        mask = gaussian_filter1d(mask, sigma=int(sr * 0.005))
        
        return filtered * mask
    
    @staticmethod
    def separate_multiple_birds(audio: np.ndarray, sr: int) -> list:
        """
        Separate multiple bird calls using frequency band isolation.
        Returns list of isolated audio segments per potential bird.
        """
        isolated_birds = []
        
        for low, high, band_name in SAM_FREQ_BANDS:
            # Isolate this frequency band
            isolated = SAMAudio.isolate_bird_call(audio, sr, (low, high))
            
            # Check if there's significant energy in this band
            energy = np.sum(isolated ** 2)
            if energy > 0.01 * np.sum(audio ** 2):  # At least 1% of total energy
                isolated_birds.append({
                    "band": band_name,
                    "freq_range": (low, high),
                    "audio": isolated,
                    "energy": energy
                })
        
        # Sort by energy (most prominent first)
        isolated_birds.sort(key=lambda x: x["energy"], reverse=True)
        
        return isolated_birds


def extract_audio_features(audio: np.ndarray, sr: int) -> dict:
    """Extract comprehensive audio features for bird identification."""
    features = {
        "duration": round(len(audio) / sr, 2),
        "peak_freq": 0,
        "min_freq": 0,
        "max_freq": 0,
        "freq_range": 0,
        "syllables": 0,
        "freq_band": "unknown",
        "pattern": "unknown",
        "complexity": "simple",
        "quality": "unknown",
        "rhythm": "unknown"
    }
    
    try:
        # Normalize
        audio = audio.astype(np.float64)
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))
        
        # Frequency analysis
        fft = np.fft.rfft(audio)
        freqs = np.fft.rfftfreq(len(audio), 1/sr)
        magnitude = np.abs(fft)
        
        # Find dominant frequencies (where magnitude > 10% of max)
        threshold = 0.1 * np.max(magnitude)
        active_freqs = freqs[magnitude > threshold]
        
        if len(active_freqs) > 0:
            features["peak_freq"] = int(freqs[np.argmax(magnitude)])
            features["min_freq"] = int(np.min(active_freqs[active_freqs > 200]))  # Ignore very low
            features["max_freq"] = int(np.min([np.max(active_freqs), 12000]))  # Cap at 12kHz
            features["freq_range"] = features["max_freq"] - features["min_freq"]
        
        # Frequency band classification
        for low, high, band in SAM_FREQ_BANDS:
            if low <= features["peak_freq"] <= high:
                features["freq_band"] = band
                break
        
        # Syllable detection
        envelope = np.abs(signal.hilbert(audio))
        smooth_env = signal.savgol_filter(envelope, min(51, len(envelope)//10*2+1), 3) if len(envelope) > 51 else envelope
        threshold = np.mean(smooth_env) + 0.3 * np.std(smooth_env)
        syllable_count = np.sum(np.diff((smooth_env > threshold).astype(int)) > 0)
        features["syllables"] = int(syllable_count)
        
        # Pattern complexity analysis
        # Look at how much the frequency varies over time (for complex singers like nightingale)
        window_size = min(1024, len(audio) // 10)
        if window_size > 100:
            freq_variations = []
            for i in range(0, len(audio) - window_size, window_size // 2):
                chunk = audio[i:i + window_size]
                chunk_fft = np.fft.rfft(chunk)
                chunk_freqs = np.fft.rfftfreq(len(chunk), 1/sr)
                peak = chunk_freqs[np.argmax(np.abs(chunk_fft))]
                freq_variations.append(peak)
            
            if len(freq_variations) > 2:
                freq_std = np.std(freq_variations)
                # Nightingales have high frequency variation (many different notes)
                if freq_std > 1000:
                    features["complexity"] = "very complex (many note types)"
                elif freq_std > 500:
                    features["complexity"] = "complex (varied phrases)"
                elif freq_std > 200:
                    features["complexity"] = "moderate"
                else:
                    features["complexity"] = "simple (repetitive)"
        
        # Pattern classification (enhanced)
        if features["syllables"] > 15 and features["complexity"] == "very complex (many note types)":
            features["pattern"] = "rich melodious song with varied phrases"
        elif features["syllables"] > 10:
            features["pattern"] = "rapid complex trills"
        elif features["syllables"] > 5:
            features["pattern"] = "repeated phrases"
        elif features["syllables"] > 1:
            features["pattern"] = "simple phrase"
        else:
            features["pattern"] = "single note or call"
        
        # Rhythm analysis
        if syllable_count > 0 and features["duration"] > 0:
            rate = syllable_count / features["duration"]
            if rate > 8:
                features["rhythm"] = "very rapid"
            elif rate > 4:
                features["rhythm"] = "rapid"
            elif rate > 2:
                features["rhythm"] = "moderate"
            else:
                features["rhythm"] = "slow/deliberate"
        
        # Quality
        snr = np.max(np.abs(audio)) / (np.std(audio) + 1e-10)
        features["quality"] = "clear" if snr > 3 else "moderate" if snr > 1.5 else "faint"
        
    except Exception as e:
        log(f"Feature extraction error: {e}")
    
    return features


# ============ OLLAMA ============

def check_ollama():
    """Check Ollama or LiteLLM status."""
    # Check Ollama first
    if OLLAMA_AVAILABLE:
        try:
            resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                return {
                    "ok": True,
                    "vision": any("llava" in m.lower() for m in models),
                    "text": any(any(t in m.lower() for t in ["llama", "phi", "qwen", "mistral"]) for m in models),
                    "models": models,
                    "backend": "Ollama"
                }
        except:
            pass
    
    # Check LiteLLM
    if LITELLM_AVAILABLE:
        return {
            "ok": True,
            "vision": True,
            "text": True,
            "models": ["LiteLLM API"],
            "backend": "LiteLLM"
        }
    
    return {"ok": False, "vision": False, "text": False, "models": [], "backend": "None"}


def call_llava(image: Image.Image, prompt: str) -> str:
    """Call vision model based on selected backend."""
    backend = get_effective_backend()
    
    try:
        max_size = 800
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            image = image.resize((int(image.size[0]*ratio), int(image.size[1]*ratio)), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        img_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        if backend == "ollama" and OLLAMA_AVAILABLE:
            # Use local Ollama LLaVA
            model_info = get_model_info("vision")
            log(f"Calling {model_info['name']} via {model_info['provider']}...")
            resp = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_VISION_MODEL, "prompt": prompt, "images": [img_b64], "stream": False,
                      "options": {"temperature": 0.1, "num_predict": 1200}},
                timeout=120
            )
            if resp.status_code == 200:
                return resp.json().get("response", "")
        
        elif backend == "litellm" and LITELLM_AVAILABLE:
            # Use LiteLLM API with GPT-4o
            model_info = get_model_info("vision")
            log(f"Calling {model_info['name']} via {model_info['provider']}...")
            resp = requests.post(
                f"{LITELLM_API_BASE}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {LITELLM_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": LITELLM_VISION_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                            ]
                        }
                    ],
                    "max_tokens": 1200,
                    "temperature": 0.1
                },
                timeout=120,
                verify=False  # Skip SSL for internal endpoint
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                log(f"LiteLLM Vision error: {resp.status_code} - {resp.text[:500]}")
        else:
            log(f"No vision backend available (backend={backend})")
                
    except Exception as e:
        log(f"Vision model error: {e}")
    return ""


def call_text_model(prompt: str) -> str:
    """Call text model based on selected backend."""
    backend = get_effective_backend()
    
    try:
        if backend == "ollama" and OLLAMA_AVAILABLE:
            # Use local Ollama phi4
            model_info = get_model_info("text")
            log(f"Calling {model_info['name']} via {model_info['provider']}...")
            resp = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": OLLAMA_TEXT_MODEL, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.2, "num_predict": 800}},
                timeout=60
            )
            if resp.status_code == 200:
                return resp.json().get("response", "")
        
        elif backend == "litellm" and LITELLM_AVAILABLE:
            # Use LiteLLM API with GPT-5.2 (best reasoning)
            model_info = get_model_info("text")
            log(f"Calling {model_info['name']} via {model_info['provider']}...")
            resp = requests.post(
                f"{LITELLM_API_BASE}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {LITELLM_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": LITELLM_TEXT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": 0.2
                },
                timeout=60,
                verify=False  # Skip SSL for internal endpoint
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                log(f"LiteLLM Text error: {resp.status_code} - {resp.text[:200]}")
        else:
            log(f"No text backend available (backend={backend})")
                
    except Exception as e:
        log(f"Text model error: {e}")
    return ""


# ============ PARSING ============

def parse_birds(text: str) -> list:
    """Extract bird identifications from response."""
    birds = []
    if not text:
        return []
    
    # Clean up the response - remove markdown code blocks
    clean_text = text
    # Remove ```json ... ``` wrapper
    clean_text = re.sub(r'```json\s*', '', clean_text)
    clean_text = re.sub(r'```\s*$', '', clean_text)
    clean_text = re.sub(r'```', '', clean_text)
    clean_text = clean_text.strip()
    
    log(f"Parsing response: {clean_text[:200]}...")
    
    try:
        # Try to find JSON object
        match = re.search(r'\{[\s\S]*"birds"[\s\S]*\}', clean_text)
        if match:
            json_str = match.group()
            # Fix common JSON issues
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
            
            data = json.loads(json_str)
            for b in data.get("birds", []):
                name = b.get("name", "").strip()
                # Filter out generic/invalid names
                if name and name.lower() not in ["unknown", "bird", "the bird", "species 1", "species 2"]:
                    birds.append({
                        "name": name,
                        "scientific": b.get("scientific_name", ""),
                        "confidence": min(99, max(1, int(b.get("confidence", 70)))),
                        "reason": b.get("reason", "")
                    })
            log(f"Parsed {len(birds)} birds: {[b['name'] for b in birds]}")
    except Exception as e:
        log(f"JSON parse error: {e}")
        # Fallback extraction
        patterns = [r"(?:this is|identified as)\s+(?:a|an)?\s*([A-Z][a-z]+(?:\s[A-Za-z]+){0,2})"]
        for p in patterns:
            matches = re.findall(p, text)
            for m in matches:
                if len(m) > 3:
                    birds.append({"name": m.strip(), "scientific": "", "confidence": 65, "reason": "AI identified"})
                    break
    
    return birds[:5]


def get_bird_image(name: str) -> str:
    """
    Get bird image from multiple sources:
    1. Wikipedia REST API (primary - high quality)
    2. Wikipedia Media API (fallback)
    3. iNaturalist API (excellent bird photos)
    4. Placeholder (last resort)
    
    Note: Xeno-canto is for AUDIO only (spectrograms), not bird photographs.
    """
    if not name or len(name) < 2:
        return ""
    
    headers = {"User-Agent": "BirdSense/1.0 (Bird Identification App)"}
    clean_name = name.replace(' ', '_')
    
    # Source 1: Wikipedia REST API (best quality)
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean_name)}"
        resp = requests.get(url, timeout=5, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            # Try originalimage first (higher quality), then thumbnail
            if "originalimage" in data:
                img_url = data["originalimage"]["source"]
                log(f"Got Wikipedia original image for {name}")
                return img_url
            elif "thumbnail" in data:
                img_url = data["thumbnail"]["source"]
                log(f"Got Wikipedia thumbnail for {name}")
                return img_url
    except Exception as e:
        log(f"Wikipedia REST failed for {name}: {e}")
    
    # Source 2: Wikipedia Media API
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(name)}&prop=pageimages&pithumbwidth=400&format=json"
        resp = requests.get(url, timeout=5, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for pid, page in pages.items():
                if "thumbnail" in page:
                    img_url = page["thumbnail"]["source"]
                    log(f"Got Wikipedia API image for {name}")
                    return img_url
    except Exception as e:
        log(f"Wikipedia API failed for {name}: {e}")
    
    # Source 3: iNaturalist API (excellent community photos)
    try:
        url = f"https://api.inaturalist.org/v1/taxa?q={urllib.parse.quote(name)}&rank=species"
        resp = requests.get(url, timeout=5, headers=headers, verify=False)  # SSL workaround
        if resp.status_code == 200:
            data = resp.json()
            for taxon in data.get('results', []):
                if taxon.get('default_photo') and taxon.get('default_photo', {}).get('medium_url'):
                    img_url = taxon['default_photo']['medium_url']
                    log(f"Got iNaturalist image for {name}")
                    return img_url
    except Exception as e:
        log(f"iNaturalist failed for {name}: {e}")
    
    # Fallback: Placeholder with bird name
    log(f"Using placeholder for {name}")
    return f"https://via.placeholder.com/200x150/1a365d/ffffff?text={urllib.parse.quote(name[:15])}"


def format_bird_result(bird: dict, index: int) -> str:
    """Format single bird result with image as HTML for reliable rendering."""
    img_url = get_bird_image(bird['name'])
    
    # Confidence color
    if bird['confidence'] >= 80:
        conf_color = "#22c55e"  # green
        conf_bg = "#dcfce7"
    elif bird['confidence'] >= 60:
        conf_color = "#eab308"  # yellow
        conf_bg = "#fef9c3"
    else:
        conf_color = "#ef4444"  # red
        conf_bg = "#fee2e2"
    
    # Get confusion hint if available
    confusion_hint = get_confusion_hint(bird['name'])
    hint_html = f"""<div style="margin-top: 8px; padding: 8px; background: #fef3c7; border-radius: 6px; font-size: 0.85em; color: #92400e;">
        💡 {confusion_hint}
    </div>""" if confusion_hint else ""
    
    # Use HTML for reliable image display
    return f"""
<div style="display: flex; gap: 16px; padding: 16px; margin: 12px 0; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <img src="{img_url}" alt="{bird['name']}" style="width: 150px; height: 150px; object-fit: cover; border-radius: 8px; flex-shrink: 0;" onerror="this.src='https://via.placeholder.com/150x150/1a365d/ffffff?text=Bird'">
    <div style="flex: 1;">
        <h3 style="margin: 0 0 4px 0; color: #1a202c; font-size: 1.3em;">{index}. {bird['name']}</h3>
        <p style="margin: 0 0 8px 0; color: #64748b; font-style: italic;">{bird.get('scientific', '') or 'Species'}</p>
        <span style="display: inline-block; padding: 4px 12px; background: {conf_bg}; color: {conf_color}; border-radius: 16px; font-weight: bold; font-size: 0.9em;">
            {bird['confidence']}% confidence
        </span>
        <p style="margin: 10px 0 0 0; color: #475569; line-height: 1.5;">{bird.get('reason', '')}</p>
        {hint_html}
    </div>
</div>
"""


# ============ BIRDNET + LLM HYBRID IDENTIFICATION ============
# Novel approach: Combines BirdNET pattern matching with LLM contextual reasoning

def identify_with_birdnet(audio_data, sr, location="", month=""):
    """
    Use BirdNET (Cornell) for audio identification.
    Returns list of candidates with confidence scores.
    """
    if not BIRDNET_AVAILABLE:
        log("BirdNET not available")
        return []
    
    try:
        import scipy.io.wavfile as wav
        
        # Ensure audio is float and normalized
        audio_float = audio_data.astype(np.float64)
        if np.max(np.abs(audio_float)) > 1.0:
            audio_float = audio_float / np.max(np.abs(audio_float))
        
        # BirdNET expects 48kHz - resample if needed
        target_sr = 48000
        if sr != target_sr:
            # Simple resampling
            duration = len(audio_float) / sr
            new_length = int(duration * target_sr)
            audio_float = np.interp(
                np.linspace(0, len(audio_float), new_length),
                np.arange(len(audio_float)),
                audio_float
            )
            sr = target_sr
        
        # Save to temp file (BirdNET requires file input)
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        # Convert to int16 for WAV
        audio_int16 = (audio_float * 32767).astype(np.int16)
        wav.write(temp_file.name, sr, audio_int16)
        
        log(f"BirdNET analyzing: {len(audio_int16)} samples at {sr}Hz")
        
        # Analyze with BirdNET
        recording = Recording(
            birdnet_analyzer,
            temp_file.name,
            lat=None,  # Could add geolocation
            lon=None,
            min_conf=0.1  # Get more candidates for LLM to evaluate
        )
        recording.analyze()
        
        # Clean up temp file
        try:
            os.unlink(temp_file.name)
        except:
            pass
        
        # Format results
        candidates = []
        for d in recording.detections:
            candidates.append({
                "name": d['common_name'],
                "scientific": d['scientific_name'],
                "confidence": int(d['confidence'] * 100),
                "source": "BirdNET",
                "start_time": d.get('start_time', 0),
                "end_time": d.get('end_time', 0)
            })
        
        log(f"BirdNET found {len(candidates)} candidates")
        return candidates
        
    except Exception as e:
        log(f"BirdNET error: {e}")
        import traceback
        traceback.print_exc()
        return []


def hybrid_llm_validation(birdnet_candidates, audio_features, location="", month=""):
    """
    Novel LLM validation layer - enhances BirdNET results with reasoning.
    
    IMPORTANT: BirdNET is the gold standard for audio. LLM ENHANCES, not overrides.
    - BirdNET confidence >= 70%: Trust it, LLM adds context
    - BirdNET confidence 40-70%: LLM validates/adjusts
    - BirdNET confidence < 40%: LLM may suggest alternatives
    """
    if not birdnet_candidates:
        return []
    
    # ALWAYS include high-confidence BirdNET results
    validated = []
    needs_llm_validation = []
    
    for candidate in birdnet_candidates[:5]:
        conf = candidate.get('confidence', 0)
        bird_entry = {
            "name": candidate['name'],
            "scientific_name": candidate.get('scientific', ''),
            "confidence": conf,
            "reason": f"BirdNET spectrogram match ({conf}% confidence)",
            "source": "BirdNET"
        }
        
        if conf >= 70:
            # High confidence - trust BirdNET, just add context
            validated.append(bird_entry)
        else:
            # Lower confidence - may need LLM validation
            needs_llm_validation.append(candidate)
    
    # If we have high-confidence results, optionally enhance with LLM reasoning
    if validated and not needs_llm_validation:
        # Just add context/reasoning to high-confidence results
        top_bird = validated[0]
        try:
            prompt = f"""The bird "{top_bird['name']}" was identified by BirdNET with {top_bird['confidence']}% confidence.
Audio features: {audio_features['min_freq']}-{audio_features['max_freq']}Hz, {audio_features['pattern']} pattern.
Location: {location or 'Unknown'}

In 1-2 sentences, explain why this identification makes sense (or note any concerns).
Just the explanation, no JSON."""
            
            reason = call_text_model(prompt)
            if reason and len(reason) < 300:
                top_bird['reason'] = f"BirdNET ({top_bird['confidence']}%): {reason.strip()}"
        except:
            pass  # Keep original reason if LLM fails
        
        return validated
    
    # For lower-confidence candidates, ask LLM to help validate
    if needs_llm_validation:
        candidates_text = "\n".join([
            f"- {c['name']} ({c.get('scientific', '')}): {c.get('confidence', 0)}%"
            for c in needs_llm_validation
        ])
        
        prompt = f"""BirdNET detected these candidates (lower confidence):
{candidates_text}

Audio: {audio_features['min_freq']}-{audio_features['max_freq']}Hz, {audio_features['pattern']} pattern, {audio_features['complexity']} complexity
Location: {location or 'Unknown'}, Season: {month or 'Unknown'}

Which is most likely correct? Consider frequency-to-size correlation and call patterns.
Respond with JSON: {{"birds": [{{"name": "...", "scientific_name": "...", "confidence": 60, "reason": "..."}}]}}"""
        
        response = call_text_model(prompt)
        llm_validated = parse_birds(response)
        
        if llm_validated:
            # Merge: keep BirdNET names but use LLM confidence adjustments
            for llm_bird in llm_validated:
                llm_bird['source'] = 'BirdNET+LLM'
                validated.append(llm_bird)
        else:
            # LLM failed - use BirdNET results as-is
            for candidate in needs_llm_validation:
                validated.append({
                    "name": candidate['name'],
                    "scientific_name": candidate.get('scientific', ''),
                    "confidence": candidate.get('confidence', 50),
                    "reason": f"BirdNET detection ({candidate.get('confidence', 50)}%)",
                    "source": "BirdNET"
                })
    
    return validated


def deduplicate_birds(birds: list) -> list:
    """Remove duplicate birds, keeping highest confidence."""
    seen = {}
    for bird in birds:
        name = bird['name'].lower().strip()
        if name not in seen or bird['confidence'] > seen[name]['confidence']:
            seen[name] = bird
    return list(seen.values())


def identify_audio_streaming(audio_input, location="", month=""):
    """
    BirdSense Hybrid Audio Identification (by Soham)
    
    Pipeline:
    1. META SAM-Audio: Noise filtering & bird call isolation
    2. BirdNET: Spectrogram pattern matching (6000+ species)
    3. Acoustic Features: Frequency, complexity, rhythm analysis
    4. LLM Validation: Contextual reasoning & deduplication
    """
    if audio_input is None:
        yield "<p style='color:#dc2626'>⚠️ Please upload or record audio</p>"
        return
    
    if isinstance(audio_input, tuple):
        sr, audio_data = audio_input
    else:
        yield "<p style='color:#dc2626'>❌ Invalid audio format</p>"
        return
    
    if len(audio_data) == 0:
        yield "<p style='color:#dc2626'>❌ Empty audio</p>"
        return
    
    # Convert to mono
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # Normalize
    audio_data = audio_data.astype(np.float64)
    if np.max(np.abs(audio_data)) > 0:
        audio_data = audio_data / np.max(np.abs(audio_data))
    
    # ========== ANALYSIS TRAIL ==========
    trail = []
    backend = get_effective_backend()
    audio_model = get_model_info("audio")
    text_model = get_model_info("text")
    
    def update_trail(step, status="⏳"):
        trail_html = "".join([f"<div style='padding:4px 0;color:#64748b'>{t}</div>" for t in trail])
        model_badge = f"""<div style='font-size:0.8em;color:#3b82f6;margin-bottom:8px'>
            🤖 Model: <b>{audio_model['name']}</b> ({audio_model['provider']})
        </div>"""
        return f"""<div style='padding:16px;background:#dbeafe;border-radius:8px'>
            <h3>🧠 BirdSense Analysis Trail</h3>
            {model_badge}
            {trail_html}
            <div style='padding:4px 0;font-weight:bold'>{status} {step}</div>
        </div>"""
    
    # ========== STAGE 1: META SAM-Audio Filtering ==========
    trail.append("✅ Audio loaded")
    yield update_trail("Stage 1/4: META SAM-Audio noise filtering...")
    
    sam = SAMAudio()
    segments = sam.detect_bird_segments(audio_data, sr)
    
    # Apply noise reduction
    if len(segments) > 0:
        # Use detected segments for cleaner analysis
        enhanced_audio = audio_data.copy()
        trail.append(f"✅ SAM-Audio: Detected {len(segments)} bird call segment(s)")
    else:
        enhanced_audio = audio_data
        trail.append("✅ SAM-Audio: Using full audio (no distinct segments)")
    
    yield update_trail("Stage 2/4: BirdNET spectrogram analysis...")
    
    # ========== STAGE 2: BirdNET Analysis ==========
    birdnet_results = []
    if BIRDNET_AVAILABLE:
        birdnet_results = identify_with_birdnet(enhanced_audio, sr, location, month)
        if birdnet_results:
            trail.append(f"✅ BirdNET: Found {len(birdnet_results)} candidate(s)")
        else:
            trail.append("⚠️ BirdNET: No confident matches")
    else:
        trail.append("⚠️ BirdNET: Not available")
    
    yield update_trail("Stage 3/4: Acoustic feature extraction...")
    
    # ========== STAGE 3: Acoustic Feature Extraction ==========
    features = extract_audio_features(enhanced_audio, sr)
    trail.append(f"✅ Features: {features['min_freq']}-{features['max_freq']}Hz, {features['pattern']}")
    
    features_html = f"""<div style='padding:12px;background:#f1f5f9;border-radius:8px;margin:8px 0'>
        <b>🎵 Acoustic Features:</b><br>
        • Frequency: {features['min_freq']}-{features['max_freq']} Hz (Peak: {features['peak_freq']} Hz)<br>
        • Pattern: {features['pattern']} | Complexity: {features['complexity']}<br>
        • Syllables: {features['syllables']} | Rhythm: {features['rhythm']}
    </div>"""
    
    yield update_trail("Stage 4/4: LLM validation & reasoning...")
    
    # ========== STAGE 4: LLM Validation & Streaming Results ==========
    all_birds = []
    result_html = ""
    
    if BIRDNET_AVAILABLE and birdnet_results:
        trail.append("✅ LLM: Validating BirdNET candidates...")
        
        # Hybrid: LLM validates BirdNET candidates
        validated_birds = hybrid_llm_validation(birdnet_results, features, location, month)
        
        if validated_birds:
            # Deduplicate birds
            validated_birds = deduplicate_birds(validated_birds)
            all_birds.extend(validated_birds)
            trail.append(f"✅ Validated: {len(validated_birds)} unique species")
    
    # If no BirdNET results or need more, use LLM-only
    if not all_birds:
        trail.append(f"🔍 {text_model['name']}: Analyzing acoustic features...")
        
        # Use model-specific prompt
        prompt_template = get_audio_prompt(backend)
        prompt = prompt_template.format(
            min_freq=features['min_freq'],
            max_freq=features['max_freq'],
            peak_freq=features['peak_freq'],
            freq_range=features['freq_range'],
            pattern=features['pattern'],
            complexity=features['complexity'],
            syllables=features['syllables'],
            rhythm=features['rhythm'],
            duration=features['duration'],
            quality=features['quality'],
            location_info=f"- Location: {location}" if location else "",
            season_info=f"- Season: {month}" if month else ""
        )
        
        response = call_text_model(prompt)
        llm_birds = parse_birds(response)
        if llm_birds:
            all_birds.extend(llm_birds)
            trail.append(f"✅ LLM identified: {len(llm_birds)} species")
    
    # ========== FINAL: Deduplicate and Stream Results ==========
    all_birds = deduplicate_birds(all_birds)
    
    if all_birds:
        # Build final result with streaming
        trail_html = "".join([f"<div style='padding:2px 0;color:#64748b;font-size:0.9em'>{t}</div>" for t in trail])
        
        result_html = f"""<div style='padding:16px;background:#dcfce7;border-radius:8px;margin-bottom:16px'>
            <h3>✅ BirdSense Results</h3>
            <p>Identified <b>{len(all_birds)}</b> unique species</p>
            <details style='margin-top:8px'>
                <summary style='cursor:pointer;color:#059669'>View analysis trail</summary>
                <div style='padding:8px;background:#f0fdf4;border-radius:4px;margin-top:8px'>{trail_html}</div>
            </details>
        </div>"""
        
        result_html += features_html
        
        # Stream each bird result
        for i, bird in enumerate(all_birds, 1):
            result_html += format_bird_result(bird, i)
            yield result_html  # Stream as each bird is added
            time.sleep(0.2)  # Brief pause for streaming effect
    else:
        yield f"""<div style='padding:16px;background:#fef2f2;border-radius:8px'>
            <h3>❌ No Birds Identified</h3>
            <p>Could not identify birds from this audio.</p>
            {features_html}
            <p style='color:#64748b;margin-top:8px'>Try a clearer recording or longer audio clip.</p>
        </div>"""


# ============ LEGACY SAM-AUDIO (kept for reference) ============

def identify_audio_streaming_legacy(audio_input, location="", month=""):
    """Legacy SAM-Audio based identification (fallback)."""
    # ... original SAM-Audio code for reference ...
    pass


# ============ ORIGINAL SAM-AUDIO STREAMING (for frequency band separation) ============

def identify_audio_with_sam(audio_input, location="", month=""):
    """
    Original META SAM-Audio approach for multi-bird detection.
    Separates birds by frequency bands.
    """
    if audio_input is None:
        yield "<p style='color:#dc2626'>⚠️ Please upload or record audio</p>"
        return
    
    if isinstance(audio_input, tuple):
        sr, audio_data = audio_input
    else:
        yield "<p style='color:#dc2626'>❌ Invalid audio format</p>"
        return
    
    if len(audio_data) == 0:
        yield "<p style='color:#dc2626'>❌ Empty audio</p>"
        return
    
    # Convert to mono
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # Normalize
    audio_data = audio_data.astype(np.float64)
    if np.max(np.abs(audio_data)) > 0:
        audio_data = audio_data / np.max(np.abs(audio_data))
    
    yield "<div style='padding:16px;background:#dbeafe;border-radius:8px'><h3>🔊 Processing with META SAM-Audio...</h3><p>Isolating bird calls from background noise...</p></div>"
    
    # Step 1: SAM-Audio separation
    sam = SAMAudio()
    segments = sam.detect_bird_segments(audio_data, sr)
    
    yield f"<div style='padding:16px;background:#dbeafe;border-radius:8px'><h3>🔊 SAM-Audio Analysis</h3><p>Detected <b>{len(segments)}</b> distinct call segment(s). Analyzing frequency bands...</p></div>"
    
    # Step 2: Separate by frequency bands
    isolated_birds = sam.separate_multiple_birds(audio_data, sr)
    
    if not isolated_birds:
        yield "<p style='color:#dc2626'>❌ No bird calls detected in audio. Try a clearer recording.</p>"
        return
    
    result = f"""<div style='padding:16px;background:#dcfce7;border-radius:8px;margin-bottom:16px'>
        <h3>🔊 META SAM-Audio Analysis Complete</h3>
        <p>Detected <b>{len(isolated_birds)}</b> potential bird(s) in different frequency bands</p>
    </div>"""
    yield result
    
    # Step 3: Stream identification for each isolated bird
    all_birds = []
    
    for i, bird_audio in enumerate(isolated_birds[:3]):  # Max 3 birds
        band = bird_audio["band"]
        freq_range = bird_audio["freq_range"]
        audio_segment = bird_audio["audio"]
        
        yield result + f"<div style='padding:12px;background:#fef3c7;border-radius:8px;margin:8px 0'><p>🎵 Analyzing Bird #{i+1} ({band} frequency: {freq_range[0]}-{freq_range[1]} Hz)...</p></div>"
        
        # Extract features from isolated segment
        features = extract_audio_features(audio_segment, sr)
        
        features_html = f"""<div style='padding:12px;background:#f1f5f9;border-radius:8px;margin:8px 0;font-size:0.9em'>
            <b>🎵 Audio Analysis:</b><br>
            • <b>Frequency Range:</b> {features['min_freq']}-{features['max_freq']} Hz (Peak: {features['peak_freq']} Hz)<br>
            • <b>Pattern:</b> {features['pattern']}<br>
            • <b>Complexity:</b> {features['complexity']}<br>
            • <b>Syllables:</b> {features['syllables']} | <b>Rhythm:</b> {features['rhythm']}<br>
            • <b>Duration:</b> {features['duration']}s | <b>Quality:</b> {features['quality']}
        </div>"""
        
        # Build prompt from external template (no hardcoded species)
        prompt = AUDIO_IDENTIFICATION_PROMPT.format(
            min_freq=features['min_freq'],
            max_freq=features['max_freq'],
            peak_freq=features['peak_freq'],
            freq_range=features['freq_range'],
            pattern=features['pattern'],
            complexity=features['complexity'],
            syllables=features['syllables'],
            rhythm=features['rhythm'],
            duration=features['duration'],
            quality=features['quality'],
            location_info=f"- Location: {location}" if location else "",
            season_info=f"- Season: {month}" if month else ""
        )
        
        response = call_text_model(prompt)
        birds = parse_birds(response)
        
        if birds:
            bird = birds[0]
            all_birds.append(bird)
            result += features_html
            result += format_bird_result(bird, i+1)
            yield result
        else:
            result += f"<div style='padding:12px;background:#fef2f2;border-radius:8px;margin:8px 0'><p>Could not identify bird in this frequency band</p></div>"
            yield result
    
    # Final summary
    if all_birds:
        summary_items = "".join([f"<li><b>{bird['name']}</b> ({bird['confidence']}%)</li>" for bird in all_birds])
        result += f"<div style='padding:16px;background:#dcfce7;border-radius:8px;margin-top:16px'><h3>✅ Summary: {len(all_birds)} Bird(s) Identified</h3><ol>{summary_items}</ol></div>"
        yield result
    else:
        yield result + "<p style='color:#dc2626'>❌ Could not identify any birds. Try a clearer recording.</p>"


def identify_image_streaming(image):
    """
    BirdSense Image Identification (by Soham)
    
    Pipeline:
    1. Image preprocessing
    2. Vision model analysis (LLaVA or GPT-4o)
    3. Feature-based identification
    4. Deduplication & streaming results
    """
    if image is None:
        yield "<p style='color:#dc2626'>⚠️ Please upload an image</p>"
        return
    
    if not isinstance(image, Image.Image):
        image = Image.fromarray(np.array(image))
    image = image.convert("RGB")
    
    # Get current backend and model info
    backend = get_effective_backend()
    vision_model = get_model_info("vision")
    
    # Analysis trail
    trail = ["✅ Image loaded"]
    
    def update_trail(step):
        trail_html = "".join([f"<div style='padding:2px 0;color:#64748b;font-size:0.9em'>{t}</div>" for t in trail])
        model_badge = f"""<div style='font-size:0.8em;color:#3b82f6;margin-bottom:8px'>
            🤖 Model: <b>{vision_model['name']}</b> ({vision_model['provider']})
        </div>"""
        return f"""<div style='padding:16px;background:#dbeafe;border-radius:8px'>
            <h3>🔍 BirdSense Image Analysis</h3>
            {model_badge}
            {trail_html}
            <div style='padding:4px 0;font-weight:bold'>⏳ {step}</div>
        </div>"""
    
    yield update_trail(f"Analyzing with {vision_model['name']}...")
    
    # Use model-specific prompt
    prompt = get_image_prompt(backend)
    response = call_llava(image, prompt)
    
    if not response:
        error_msg = "Vision model not responding."
        if backend == "ollama":
            error_msg += " Run: <code>ollama pull llava:7b</code>"
        elif backend == "litellm":
            error_msg += " Check LiteLLM connection."
        yield f"<p style='color:#dc2626'>❌ {error_msg}</p>"
        return
    
    trail.append(f"✅ {vision_model['name']} analysis complete")
    yield update_trail("Parsing identification results...")
    
    birds = parse_birds(response)
    
    if not birds:
        yield f"""<div style='padding:16px;background:#fef2f2;border-radius:8px'>
            <h3>❌ Could not identify birds</h3>
            <details><summary>View raw response</summary>
            <pre style='background:#f1f5f9;padding:8px;border-radius:4px;overflow:auto;font-size:0.8em'>{response[:500]}</pre>
            </details>
        </div>"""
        return
    
    # Deduplicate birds
    birds = deduplicate_birds(birds)
    trail.append(f"✅ Identified {len(birds)} unique species")
    
    # Build final result with streaming
    trail_html = "".join([f"<div style='padding:2px 0;color:#64748b;font-size:0.9em'>{t}</div>" for t in trail])
    
    result = f"""<div style='padding:16px;background:#dcfce7;border-radius:8px;margin-bottom:16px'>
        <h3>✅ BirdSense Results</h3>
        <p>Identified <b>{len(birds)}</b> unique species</p>
        <details style='margin-top:8px'>
            <summary style='cursor:pointer;color:#059669'>View analysis trail</summary>
            <div style='padding:8px;background:#f0fdf4;border-radius:4px;margin-top:8px'>{trail_html}</div>
        </details>
    </div>"""
    
    # Stream each bird result
    for i, bird in enumerate(birds, 1):
        result += format_bird_result(bird, i)
        yield result
        time.sleep(0.2)


def identify_description(description):
    """
    BirdSense Description Identification (by Soham)
    """
    if not description or len(description) < 5:
        yield "<p style='color:#dc2626'>⚠️ Please enter a description</p>"
        return
    
    # Get current backend and model info
    backend = get_effective_backend()
    text_model = get_model_info("text")
    
    trail = ["✅ Description received"]
    
    def update_trail(step):
        trail_html = "".join([f"<div style='padding:2px 0;color:#64748b;font-size:0.9em'>{t}</div>" for t in trail])
        model_badge = f"""<div style='font-size:0.8em;color:#3b82f6;margin-bottom:8px'>
            🤖 Model: <b>{text_model['name']}</b> ({text_model['provider']})
        </div>"""
        return f"""<div style='padding:16px;background:#dbeafe;border-radius:8px'>
            <h3>📝 BirdSense Description Analysis</h3>
            {model_badge}
            {trail_html}
            <div style='padding:4px 0;font-weight:bold'>⏳ {step}</div>
        </div>"""
    
    yield update_trail(f"Analyzing with {text_model['name']}...")
    
    # Use model-specific prompt
    prompt_template = get_description_prompt(backend)
    prompt = prompt_template.format(description=description)
    
    response = call_text_model(prompt)
    trail.append(f"✅ {text_model['name']} analysis complete")
    
    birds = parse_birds(response)
    
    if not birds:
        yield f"""<div style='padding:16px;background:#fef2f2;border-radius:8px'>
            <h3>❌ Could not identify bird</h3>
            <p>Try providing more details about colors, size, behavior.</p>
        </div>"""
        return
    
    # Deduplicate
    birds = deduplicate_birds(birds)
    trail.append(f"✅ Matched {len(birds)} species")
    
    trail_html = "".join([f"<div style='padding:2px 0;color:#64748b;font-size:0.9em'>{t}</div>" for t in trail])
    
    result = f"""<div style='padding:16px;background:#dcfce7;border-radius:8px;margin-bottom:16px'>
        <h3>✅ BirdSense Results</h3>
        <p>Matched <b>{len(birds)}</b> species from description</p>
        <details style='margin-top:8px'>
            <summary style='cursor:pointer;color:#059669'>View analysis trail</summary>
            <div style='padding:8px;background:#f0fdf4;border-radius:4px;margin-top:8px'>{trail_html}</div>
        </details>
    </div>"""
    
    for i, bird in enumerate(birds, 1):
        result += format_bird_result(bird, i)
        yield result
        time.sleep(0.2)


# ============ BIRDNET BENCHMARK ============

def run_birdnet_benchmark():
    """
    Benchmark info - comparing BirdSense vs BirdNET.
    BirdNET: https://github.com/kahst/BirdNET-Analyzer
    """
    return """
## 📊 BirdNET Benchmark Comparison

### What is BirdNET?
BirdNET is the industry-leading bird audio identification system developed by Cornell Lab of Ornithology and Chemnitz University.

### Key Metrics to Compare

| Metric | BirdNET | BirdSense (Current) |
|--------|---------|---------------------|
| **Species Coverage** | 6,000+ globally | Open (LLM knowledge) |
| **Accuracy (Top-1)** | ~80-90% | TBD - needs testing |
| **Accuracy (Top-3)** | ~95% | TBD |
| **Processing** | CNN classifier | LLM reasoning |
| **Multi-bird** | Limited | ✅ SAM-Audio separation |
| **Noise handling** | Good | ✅ SAM-Audio filtering |
| **Explainability** | Low | ✅ High (reasoning) |
| **Custom training** | Difficult | ✅ Easy (fine-tune LLM) |

### How to Benchmark

1. **Get test dataset**: Download XC samples from xeno-canto.org
2. **Run both systems**: Same audio through BirdNET and BirdSense
3. **Compare**: Accuracy, speed, explanations

### To Run BirdNET Locally:

```bash
pip install birdnetlib
```

```python
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

analyzer = Analyzer()
recording = Recording(analyzer, "bird_audio.wav")
recording.analyze()
print(recording.detections)
```

### Our Advantages

1. **META SAM-Audio**: Better source separation than BirdNET
2. **Explainability**: LLM explains WHY it identified a species
3. **Multi-modal**: Audio + Image + Description
4. **Customizable**: Fine-tune on regional species

### Run Benchmark Test

Upload the same audio to both systems and compare!
"""


# ============ UI ============

def submit_feedback(is_correct, correct_species, notes):
    """Handle feedback submission."""
    save_feedback(
        prediction_id="latest",
        is_correct=is_correct,
        correct_species=correct_species if not is_correct else None,
        user_notes=notes
    )
    return "✅ Thank you for your feedback! This helps improve BirdSense."


def refresh_analytics():
    """Refresh analytics dashboard."""
    return format_analytics_html()


def create_app():
    status = check_ollama()
    
    with gr.Blocks(title="BirdSense - By Soham") as app:
        gr.Markdown("""
# 🐦 BirdSense - AI Bird Identification
**Developed by Soham**

**META SAM-Audio** | **BirdNET + LLM Hybrid** | **Multi-bird Detection**
""")
        
        # Backend selector and status display
        with gr.Row():
            backend_selector = gr.Radio(
                choices=["Auto", "Ollama (Local)", "LiteLLM (Enterprise)"],
                value="Auto",
                label="🔧 LLM Backend",
                scale=2
            )
            status_display = gr.HTML(get_backend_status_html(), scale=3)
        
        def on_backend_change(selection):
            global ACTIVE_BACKEND
            if selection == "Ollama (Local)":
                ACTIVE_BACKEND = "ollama"
            elif selection == "LiteLLM (Enterprise)":
                ACTIVE_BACKEND = "litellm"
            else:
                ACTIVE_BACKEND = "auto"
            return get_backend_status_html()
        
        backend_selector.change(on_backend_change, [backend_selector], [status_display])
        
        with gr.Tab("🎵 Audio"):
            gr.Markdown("""
### Audio Identification with META SAM-Audio + BirdNET
- **SAM-Audio**: Isolates bird calls from noise
- **BirdNET (Cornell)**: 6000+ species recognition
- **LLM Validation**: Contextual reasoning
""")
            with gr.Row():
                with gr.Column():
                    audio_in = gr.Audio(sources=["upload", "microphone"], type="numpy", label="Bird Call")
                    with gr.Row():
                        loc = gr.Textbox(label="Location", placeholder="e.g., Mumbai, India")
                        mon = gr.Dropdown(label="Month", choices=[""] + ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
                    audio_btn = gr.Button("🔍 Identify Birds", variant="primary")
                with gr.Column():
                    audio_out = gr.HTML("<p style='color:#64748b;padding:40px;text-align:center'>🎵 Upload audio to identify birds</p>")
            audio_btn.click(identify_audio_streaming, [audio_in, loc, mon], audio_out)
        
        with gr.Tab("📷 Image"):
            gr.Markdown("""
### Image Identification with LLaVA Vision
- **Feature analysis**: Beak, plumage, patterns
- **Multi-bird detection**: All birds in image
- **Species-level ID**: Specific species names
""")
            with gr.Row():
                with gr.Column():
                    img_in = gr.Image(sources=["upload", "webcam"], type="pil", label="Bird Photo")
                    img_btn = gr.Button("🔍 Identify Birds", variant="primary")
                with gr.Column():
                    img_out = gr.HTML("<p style='color:#64748b;padding:40px;text-align:center'>📷 Upload image to identify birds</p>")
            img_btn.click(identify_image_streaming, [img_in], img_out)
        
        with gr.Tab("📝 Description"):
            gr.Markdown("### Describe the bird - colors, size, behavior, sounds")
            with gr.Row():
                with gr.Column():
                    desc_in = gr.Textbox(label="Description", lines=4, placeholder="Large blue and yellow parrot with red beak...")
                    desc_btn = gr.Button("🔍 Identify", variant="primary")
                with gr.Column():
                    desc_out = gr.HTML("<p style='color:#64748b;padding:40px;text-align:center'>📝 Enter description to identify</p>")
            desc_btn.click(identify_description, [desc_in], desc_out)
        
        with gr.Tab("📝 Feedback"):
            gr.Markdown("""
### Help Improve BirdSense!
Your feedback helps us train better models. Please let us know if the identification was correct.
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
            gr.Markdown("""
### About BirdSense
**Developed by Soham**

A novel hybrid AI system combining:
- **BirdNET (Cornell Lab)** - Spectrogram pattern matching (6000+ species)
- **Vision Models** - LLaVA 7B (local) or GPT-4o (enterprise)
- **Text Models** - phi4 14B (local) or GPT-5.2 (enterprise)
- **META SAM-Audio** - Noise filtering & bird call isolation

#### 🔧 Backend Options
| Backend | Vision | Text | Quality |
|---------|--------|------|---------|
| Ollama (Local) | LLaVA 7B | phi4 14B | ⭐⭐⭐⭐ |
| LiteLLM (Enterprise) | GPT-4o | GPT-5.2 | ⭐⭐⭐⭐⭐ |

#### 📊 Architecture
```
AUDIO → SAM-Audio → BirdNET → LLM Validation → Results
IMAGE → Vision Model → Feature Analysis → Results
TEXT  → Text Model → Reasoning → Results
```

#### 🙏 Acknowledgments
- Cornell Lab of Ornithology (BirdNET)
- Meta AI (LLaVA)
- OpenAI (GPT models)
- Ollama team
""")
        
        gr.Markdown("""
---
**🐦 BirdSense by Soham** | Help improve: Submit feedback after each identification!
""")
    
    return app


# ============ MAIN ============

if __name__ == "__main__":
    print("🐦 BirdSense - AI Bird Identification")
    print("=" * 50)
    print("Features:")
    print("  • META SAM-Audio for source separation")
    print("  • Multi-bird streaming detection")
    print("  • BirdNET benchmark comparison")
    print("=" * 50)
    
    status = check_ollama()
    print(f"Ollama: {'✅' if status['ok'] else '❌'}")
    print(f"LLaVA: {'✅' if status['vision'] else '❌ Run: ollama pull llava:7b'}")
    print(f"Llama3.2: {'✅' if status['text'] else '❌ Run: ollama pull llama3.2'}")
    print("=" * 50)
    
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, show_error=True)
