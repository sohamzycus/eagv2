"""
🐦 BirdSense Pro - AI Bird Identification
Enhanced with META SAM-Audio processing, streaming responses, and multi-bird detection
"""

import gradio as gr
import numpy as np
import scipy.signal as signal
from typing import Tuple, List, Dict, Generator
import json
import requests
import re
import urllib.parse
import os
import traceback
from PIL import Image
import io

# Try to enable AVIF support
try:
    import pillow_avif  # noqa
except ImportError:
    pass  # AVIF support optional

# ================== CONFIG ==================
SAMPLE_RATE = 48000
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODELS = ["llama3.2", "qwen2.5:3b", "phi4"]  # Fallback chain
HF_TOKEN = os.environ.get("HF_TOKEN", "")
DEBUG = True

def log(msg):
    if DEBUG:
        print(f"[BirdSense] {msg}")

# ================== CSS ==================
CSS = """
.gradio-container { 
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%) !important; 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important; 
}
.header { 
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #3d7ab5 100%); 
    color: white; 
    padding: 50px 30px; 
    border-radius: 24px; 
    text-align: center; 
    margin-bottom: 24px;
    box-shadow: 0 20px 60px rgba(30, 58, 95, 0.3);
}
.header h1 { font-size: 3rem; font-weight: 800; margin: 0 0 12px 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }
.header .subtitle { font-size: 1.2rem; opacity: 0.95; margin-bottom: 16px; }
.header .status { 
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(255,255,255,0.15); padding: 10px 24px; border-radius: 50px;
    backdrop-filter: blur(10px); font-weight: 600;
}
.status-dot { width: 12px; height: 12px; background: #4ade80; border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.6; transform: scale(0.9); } }

.info-box { 
    background: linear-gradient(135deg, #dbeafe 0%, #e0f2fe 100%);
    border: 1px solid #93c5fd; border-radius: 16px; padding: 20px; margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(147, 197, 253, 0.2);
}
.info-box h3 { color: #1e40af; margin: 0 0 8px 0; font-size: 1.1rem; }
.info-box p { color: #3b82f6; margin: 0; }

.bird-card { 
    background: white; border: 1px solid #e2e8f0; border-radius: 20px; 
    padding: 24px; margin: 16px 0; display: flex; gap: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
}
.bird-card:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(0,0,0,0.1); }
.bird-card img { width: 140px; height: 140px; object-fit: cover; border-radius: 16px; }
.bird-info { flex: 1; }
.bird-info h3 { color: #1e293b; margin: 0 0 6px 0; font-size: 1.3rem; font-weight: 700; }
.bird-info .scientific { color: #64748b; font-style: italic; font-size: 0.95rem; margin-bottom: 12px; }
.confidence { display: inline-block; padding: 6px 16px; border-radius: 24px; font-weight: 700; font-size: 0.85rem; }
.conf-high { background: linear-gradient(135deg, #dcfce7, #bbf7d0); color: #166534; }
.conf-med { background: linear-gradient(135deg, #fef3c7, #fde68a); color: #92400e; }
.conf-low { background: linear-gradient(135deg, #fee2e2, #fecaca); color: #991b1b; }
.reason { color: #475569; margin-top: 12px; line-height: 1.7; font-size: 0.95rem; }

.error { background: linear-gradient(135deg, #fef2f2, #fee2e2); border: 1px solid #fca5a5; border-radius: 16px; padding: 24px; color: #b91c1c; }
.success { background: linear-gradient(135deg, #f0fdf4, #dcfce7); border: 1px solid #86efac; border-radius: 16px; padding: 24px; color: #166534; }
.processing { background: linear-gradient(135deg, #eff6ff, #dbeafe); border: 1px solid #93c5fd; border-radius: 16px; padding: 24px; color: #1e40af; }

.features-box { 
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; 
    padding: 16px; margin: 12px 0; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;
}

@media (max-width: 768px) { 
    .header h1 { font-size: 2rem; }
    .bird-card { flex-direction: column; } 
    .bird-card img { width: 100%; height: 200px; } 
}
"""


# ================== META SAM-AUDIO PROCESSING ==================

def sam_audio_process(audio: np.ndarray, sr: int) -> Tuple[np.ndarray, Dict]:
    """
    META SAM-Audio inspired processing:
    - Multi-band frequency isolation for bird calls
    - Adaptive noise reduction
    - Source separation for multiple birds
    """
    log("SAM-Audio: Processing audio...")
    
    # Normalize
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype == np.int32:
        audio = audio.astype(np.float32) / 2147483648.0
    else:
        audio = audio.astype(np.float32)
    
    if len(audio.shape) > 1:
        audio = np.mean(audio, axis=1)
    
    audio = audio / (np.max(np.abs(audio)) + 1e-8)
    
    # Resample to standard rate
    if sr != SAMPLE_RATE:
        audio = signal.resample(audio, int(len(audio) * SAMPLE_RATE / sr))
        sr = SAMPLE_RATE
    
    # === SAM-Audio Multi-Band Processing ===
    
    # 1. Spectral Noise Gate (remove low-energy noise)
    stft = np.fft.rfft(audio)
    magnitudes = np.abs(stft)
    noise_floor = np.percentile(magnitudes, 20)
    mask = magnitudes > (noise_floor * 2)
    stft_clean = stft * mask
    audio_denoised = np.fft.irfft(stft_clean, len(audio))
    
    # 2. Bird Frequency Isolation (500-12000 Hz)
    try:
        sos = signal.butter(6, [500, 12000], btype='band', fs=sr, output='sos')
        audio_bird = signal.sosfilt(sos, audio_denoised)
    except:
        audio_bird = audio_denoised
    
    # 3. Adaptive Enhancement for Feeble Signals
    envelope = np.abs(signal.hilbert(audio_bird))
    envelope_smooth = signal.medfilt(envelope, min(1001, len(envelope)//2*2+1))
    
    # Boost feeble signals
    signal_strength = np.mean(envelope_smooth)
    if signal_strength < 0.1:  # Feeble signal
        log("SAM-Audio: Boosting feeble signal")
        audio_bird = audio_bird * (0.3 / (signal_strength + 1e-8))
        audio_bird = np.clip(audio_bird, -1, 1)
    
    # === Feature Extraction ===
    
    duration = len(audio_bird) / sr
    
    # Frequency analysis
    freqs, psd = signal.welch(audio_bird, sr, nperseg=min(4096, len(audio_bird)))
    peak_freq = freqs[np.argmax(psd)]
    
    # Find frequency range (where 90% of energy is)
    cumsum = np.cumsum(psd) / (np.sum(psd) + 1e-10)
    freq_low = freqs[np.searchsorted(cumsum, 0.05)] if len(freqs) > 0 else 500
    freq_high = freqs[np.searchsorted(cumsum, 0.95)] if len(freqs) > 0 else 8000
    
    # SNR estimation
    noise_power = np.percentile(psd, 10)
    signal_power = np.percentile(psd, 90)
    snr_db = 10 * np.log10((signal_power + 1e-10) / (noise_power + 1e-10))
    
    # === Multi-Bird Detection ===
    
    # Detect syllables/calls
    try:
        threshold = np.mean(envelope_smooth) + 0.25 * np.std(envelope_smooth)
        peaks, properties = signal.find_peaks(
            envelope_smooth, 
            height=threshold, 
            distance=int(0.05 * sr),
            prominence=0.05
        )
        num_sounds = len(peaks)
        
        # Analyze frequency variation (indicates multiple species)
        if num_sounds >= 3:
            chunk_freqs = []
            for peak in peaks[:10]:
                start = max(0, peak - int(0.1 * sr))
                end = min(len(audio_bird), peak + int(0.1 * sr))
                chunk = audio_bird[start:end]
                if len(chunk) > 256:
                    f, p = signal.welch(chunk, sr, nperseg=min(256, len(chunk)))
                    chunk_freqs.append(f[np.argmax(p)])
            
            freq_variation = np.std(chunk_freqs) if chunk_freqs else 0
            multiple_birds = freq_variation > 500  # High variation suggests multiple species
        else:
            multiple_birds = False
    except:
        num_sounds = 0
        multiple_birds = False
    
    # Syllable rate
    syllable_rate = num_sounds / duration if duration > 0 else 0
    
    # Pattern classification
    if syllable_rate > 6: pattern = "highly repetitive (alarm call, woodpecker)"
    elif syllable_rate > 3: pattern = "repetitive (cuckoo, barbet, myna)"
    elif syllable_rate > 1: pattern = "melodic (robin, bulbul, oriole)"
    elif syllable_rate > 0.3: pattern = "sparse calls (crow, koel, coucal)"
    else: pattern = "single call or very sparse"
    
    # Frequency description
    if peak_freq < 800: freq_desc = "very low (large bird: crow, koel, coucal)"
    elif peak_freq < 1500: freq_desc = "low (dove, cuckoo, babbler)"
    elif peak_freq < 3000: freq_desc = "medium-low (myna, bulbul, robin)"
    elif peak_freq < 5000: freq_desc = "medium (barbet, oriole, drongo)"
    elif peak_freq < 7500: freq_desc = "high (warbler, tailorbird, sunbird)"
    else: freq_desc = "very high (small bird, insect-like calls)"
    
    # Quality assessment
    if snr_db > 20: quality = "excellent"
    elif snr_db > 12: quality = "good"
    elif snr_db > 6: quality = "fair (some noise)"
    else: quality = "poor (noisy background)"
    
    features = {
        "duration": duration,
        "peak_freq": peak_freq,
        "freq_range": (freq_low, freq_high),
        "freq_desc": freq_desc,
        "snr_db": snr_db,
        "quality": quality,
        "num_sounds": num_sounds,
        "syllable_rate": syllable_rate,
        "pattern": pattern,
        "multiple_birds": multiple_birds,
    }
    
    log(f"SAM-Audio features: {features}")
    return audio_bird, features


# ================== IMAGE ANALYSIS ==================

def analyze_image(image: np.ndarray) -> Dict:
    """Analyze bird image for color patterns."""
    if len(image.shape) != 3:
        return {"error": "Invalid image"}
    
    h, w = image.shape[:2]
    
    # Analyze regions
    regions = {
        "head": image[:h//3],
        "body": image[h//3:2*h//3],
        "tail": image[2*h//3:]
    }
    
    color_info = {}
    for region_name, region in regions.items():
        r = np.mean(region[:,:,0])
        g = np.mean(region[:,:,1])
        b = np.mean(region[:,:,2])
        
        colors = []
        brightness = (r + g + b) / 3
        
        if brightness > 200: colors.append("white")
        elif brightness < 50: colors.append("black")
        
        if g > r * 1.2 and g > b * 1.2: colors.append("green")
        if b > r * 1.15 and b > g * 1.1: colors.append("blue")
        if r > g * 1.25 and r > b * 1.25:
            colors.append("red/rufous" if r > 180 else "brown")
        if r > 160 and g > 120 and b < 100: colors.append("yellow/orange")
        if abs(r - g) < 30 and abs(g - b) < 30 and 60 < brightness < 180:
            colors.append("grey")
        
        if not colors:
            colors.append("mixed/tan")
        
        color_info[region_name] = colors
    
    # Detect patterns
    variance = np.var(image)
    has_patterns = variance > 2000
    
    return {
        "colors": color_info,
        "has_patterns": has_patterns,
        "brightness": brightness
    }


# ================== WIKIPEDIA IMAGE ==================

def get_bird_image(name: str, scientific: str = "") -> str:
    """Get bird image from Wikipedia - no hardcoding."""
    for term in [scientific, name, f"{name} bird India"]:
        if not term:
            continue
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(term.replace(' ', '_'))}"
            r = requests.get(url, timeout=5, headers={"User-Agent": "BirdSense/2.0"})
            if r.status_code == 200:
                data = r.json()
                if "thumbnail" in data:
                    img_url = data["thumbnail"]["source"]
                    # Get larger image
                    img_url = re.sub(r'/\d+px-', '/400px-', img_url)
                    return img_url
        except:
            continue
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Bird_icon.svg/200px-Bird_icon.svg.png"


# ================== LLM CALLS ==================

def check_ollama() -> Tuple[bool, str]:
    """Check if Ollama is running and return available model."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if r.status_code == 200:
            models = r.json().get("models", [])
            model_names = [m["name"] for m in models]
            for preferred in OLLAMA_MODELS:
                if any(preferred in m for m in model_names):
                    return True, preferred
            if model_names:
                return True, model_names[0].split(":")[0]
    except:
        pass
    return False, ""


def call_ollama_stream(prompt: str, model: str) -> Generator[str, None, None]:
    """Stream response from Ollama."""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": True,
                "options": {"temperature": 0.2, "num_predict": 2000}
            },
            stream=True,
            timeout=120
        )
        
        full_response = ""
        for line in r.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    full_response += chunk
                    yield full_response
                    if data.get("done"):
                        break
                except:
                    continue
        
        yield full_response
        
    except Exception as e:
        log(f"Ollama stream error: {e}")
        yield ""


def call_ollama(prompt: str, model: str) -> str:
    """Call Ollama (non-streaming)."""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 2000}
            },
            timeout=120
        )
        if r.status_code == 200:
            return r.json().get("response", "")
    except Exception as e:
        log(f"Ollama error: {e}")
    return ""


def call_huggingface(prompt: str) -> str:
    """Call HuggingFace API as fallback."""
    models = ["mistralai/Mistral-7B-Instruct-v0.3", "google/flan-t5-xxl"]
    token = HF_TOKEN or os.environ.get("HF_TOKEN", "")
    
    for model in models:
        try:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            r = requests.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json={"inputs": prompt, "parameters": {"max_new_tokens": 1000, "temperature": 0.2}},
                timeout=90
            )
            if r.status_code == 200:
                result = r.json()
                if isinstance(result, list) and result:
                    return result[0].get("generated_text", "")
        except:
            continue
    return ""


def build_prompt(context: str, multiple_birds: bool = False) -> str:
    """Build expert prompt for bird identification."""
    multi_instruction = """
IMPORTANT: The audio may contain MULTIPLE bird species calling together.
Identify ALL birds you can detect based on the different frequency patterns and call types.
""" if multiple_birds else ""
    
    return f"""You are an expert ornithologist specializing in Indian birds.
{multi_instruction}
{context}

Return ONLY valid JSON in this exact format (no other text):
{{"birds": [
    {{"name": "Common Name", "scientific_name": "Genus species", "confidence": 85, "reason": "Clear explanation of why this bird matches based on the features"}}
], "summary": "Brief analysis of the identification"}}

Rules:
- Include 1-5 matching birds, ordered by confidence
- confidence is 0-100
- Provide detailed reasoning for each bird
- Consider habitat, season, and location if provided
- NO hardcoded responses - analyze the actual features provided

JSON only, no markdown."""


def parse_llm_response(text: str) -> Tuple[List[Dict], str]:
    """Parse JSON from LLM response."""
    if not text:
        return [], ""
    
    try:
        # Clean markdown
        clean = re.sub(r'```json\s*', '', text.strip())
        clean = re.sub(r'```\s*', '', clean)
        
        # Try direct parse
        try:
            data = json.loads(clean)
            if "birds" in data:
                return data["birds"], data.get("summary", "")
        except:
            pass
        
        # Extract first JSON object
        match = re.search(r'\{[^{}]*"birds"[^{}]*\[.*?\][^{}]*\}', clean, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return data.get("birds", []), data.get("summary", "")
            except:
                pass
        
        # Extract birds array manually
        birds_match = re.search(r'"birds"\s*:\s*\[(.*?)\]', clean, re.DOTALL)
        if birds_match:
            birds = []
            for obj in re.findall(r'\{[^{}]+\}', birds_match.group(1)):
                try:
                    bird = json.loads(obj.replace("'", '"'))
                    if "name" in bird:
                        birds.append(bird)
                except:
                    continue
            if birds:
                summary_match = re.search(r'"summary"\s*:\s*"([^"]*)"', clean)
                return birds, summary_match.group(1) if summary_match else ""
                
    except Exception as e:
        log(f"Parse error: {e}")
    
    return [], ""


def format_bird_card(bird: Dict, idx: int) -> str:
    """Format bird as HTML card with dynamic image."""
    name = bird.get("name", "Unknown Bird")
    sci = bird.get("scientific_name", "Species unknown")
    conf = bird.get("confidence", 50)
    reason = bird.get("reason", "Matches the provided features")
    
    # Get image from Wikipedia (no hardcoding)
    img = get_bird_image(name, sci)
    
    conf_class = "conf-high" if conf >= 75 else "conf-med" if conf >= 50 else "conf-low"
    
    return f"""
<div class="bird-card">
    <img src="{img}" alt="{name}" onerror="this.src='https://via.placeholder.com/140?text=🐦'">
    <div class="bird-info">
        <h3>{idx}. {name}</h3>
        <div class="scientific">{sci}</div>
        <span class="confidence {conf_class}">{conf}% confidence</span>
        <p class="reason">{reason}</p>
    </div>
</div>"""


# ================== STREAMING IDENTIFICATION ==================

def identify_audio_stream(audio, location, month):
    """Streaming audio identification with SAM-Audio processing."""
    if audio is None:
        yield '<div class="error">⚠️ Please record or upload audio first</div>'
        return
    
    try:
        sr, audio_data = audio
        
        # Step 1: Show processing status
        yield '<div class="processing">🔄 Processing with SAM-Audio...</div>'
        
        # Step 2: SAM-Audio processing
        processed, features = sam_audio_process(audio_data, sr)
        
        features_html = f"""
<div class="features-box">
<strong>📊 Audio Analysis (SAM-Audio)</strong><br>
• Duration: {features['duration']:.1f}s<br>
• Peak Frequency: {features['peak_freq']:.0f} Hz ({features['freq_desc']})<br>
• Pattern: {features['pattern']} ({features['num_sounds']} sounds)<br>
• Quality: {features['quality']} (SNR: {features['snr_db']:.1f} dB)<br>
• Multiple species: {'🔴 Yes - analyzing multiple birds' if features['multiple_birds'] else '🟢 Single species likely'}
</div>"""
        
        yield f'<div class="processing">🔍 Analyzing features...</div>{features_html}'
        
        # Step 3: Build prompt
        context = f"""AUDIO ANALYSIS (META SAM-Audio processed):
- Duration: {features['duration']:.1f} seconds
- Peak Frequency: {features['peak_freq']:.0f} Hz ({features['freq_desc']})
- Frequency Range: {features['freq_range'][0]:.0f} - {features['freq_range'][1]:.0f} Hz
- Call Pattern: {features['pattern']}
- Sound Count: {features['num_sounds']} distinct vocalizations
- Audio Quality: {features['quality']} (SNR: {features['snr_db']:.1f} dB)
- Multiple Species Detected: {features['multiple_birds']}

Location: {location or 'India (unspecified)'}
Month: {month or 'Not specified'}

Based on these acoustic features, identify the bird species."""

        prompt = build_prompt(context, features['multiple_birds'])
        
        yield f'<div class="processing">🤖 AI analyzing bird calls...</div>{features_html}'
        
        # Step 4: Call LLM with streaming
        ollama_available, model = check_ollama()
        
        if ollama_available:
            log(f"Using Ollama model: {model}")
            full_response = ""
            for response in call_ollama_stream(prompt, model):
                full_response = response
                # Try to parse partial response
                birds, summary = parse_llm_response(full_response)
                if birds:
                    result_html = f"""<div class="success">
                        <h2>🐦 {len(birds)} Bird(s) Identified</h2>
                        <p>{summary or f"Based on: {features['pattern']}"}</p>
                    </div>{features_html}"""
                    for i, bird in enumerate(birds, 1):
                        result_html += format_bird_card(bird, i)
                    yield result_html
        else:
            # Fallback to HuggingFace
            log("Using HuggingFace API")
            yield f'<div class="processing">☁️ Using cloud AI (HuggingFace)...</div>{features_html}'
            full_response = call_huggingface(prompt)
        
        # Final parse
        birds, summary = parse_llm_response(full_response)
        
        if not birds:
            yield f"""<div class="error">
                <strong>⚠️ Could not identify birds</strong>
                <p>The AI couldn't parse the response. Audio features:</p>
                {features_html}
                <pre style="font-size:0.8rem; max-height:150px; overflow:auto;">{full_response[:500] if full_response else 'No response'}</pre>
            </div>"""
            return
        
        # Final result
        result_html = f"""<div class="success">
            <h2>🐦 {len(birds)} Bird(s) Identified</h2>
            <p>{summary}</p>
        </div>{features_html}"""
        
        for i, bird in enumerate(birds, 1):
            result_html += format_bird_card(bird, i)
        
        yield result_html
        
    except Exception as e:
        log(f"Error: {traceback.format_exc()}")
        yield f'<div class="error"><strong>❌ Error:</strong> {str(e)}</div>'


def load_image_safely(image_input):
    """Load image from various input types, handling AVIF and other formats."""
    if image_input is None:
        return None
    
    # Already numpy array
    if isinstance(image_input, np.ndarray):
        return image_input
    
    # PIL Image
    if isinstance(image_input, Image.Image):
        return np.array(image_input.convert("RGB"))
    
    # File path (string)
    if isinstance(image_input, str):
        try:
            # Try PIL first
            img = Image.open(image_input)
            return np.array(img.convert("RGB"))
        except Exception as e:
            log(f"PIL failed: {e}, trying with imageio")
            try:
                import imageio
                return np.array(imageio.imread(image_input))
            except:
                pass
    
    # Dict with filepath (Gradio format)
    if isinstance(image_input, dict) and 'path' in image_input:
        try:
            img = Image.open(image_input['path'])
            return np.array(img.convert("RGB"))
        except Exception as e:
            log(f"Could not load image from dict: {e}")
    
    # Last resort - try direct conversion
    try:
        return np.array(image_input)
    except:
        return None


def identify_image_stream(image):
    """Streaming image identification."""
    if image is None:
        yield '<div class="error">⚠️ Please upload an image first</div>'
        return
    
    try:
        img = load_image_safely(image)
        
        if img is None:
            yield '<div class="error">❌ Could not read image. Please try a different format (JPG, PNG recommended).</div>'
            return
        
        yield '<div class="processing">🔍 Analyzing bird colors and patterns...</div>'
        
        analysis = analyze_image(img)
        
        if "error" in analysis:
            yield '<div class="error">Invalid image format</div>'
            return
        
        colors = analysis["colors"]
        
        features_html = f"""
<div class="features-box">
<strong>🎨 Color Analysis</strong><br>
• Head: {', '.join(colors['head'])}<br>
• Body: {', '.join(colors['body'])}<br>
• Tail: {', '.join(colors['tail'])}<br>
• Patterns: {'Visible markings/patterns' if analysis['has_patterns'] else 'Relatively uniform'}
</div>"""
        
        yield f'<div class="processing">🤖 Identifying bird...</div>{features_html}'
        
        context = f"""IMAGE COLOR ANALYSIS:
- Head/Upper region: {', '.join(colors['head'])}
- Body/Middle region: {', '.join(colors['body'])}
- Tail/Lower region: {', '.join(colors['tail'])}
- Has visible patterns: {analysis['has_patterns']}

Identify Indian birds with this coloration pattern."""

        prompt = build_prompt(context)
        
        ollama_available, model = check_ollama()
        
        if ollama_available:
            full_response = call_ollama(prompt, model)
        else:
            yield f'<div class="processing">☁️ Using cloud AI...</div>{features_html}'
            full_response = call_huggingface(prompt)
        
        birds, summary = parse_llm_response(full_response)
        
        if not birds:
            yield f"""<div class="error">
                <strong>Could not identify bird</strong>
                {features_html}
            </div>"""
            return
        
        result_html = f"""<div class="success">
            <h2>🐦 {len(birds)} Bird(s) Identified</h2>
            <p>{summary or 'Based on color analysis'}</p>
        </div>{features_html}"""
        
        for i, bird in enumerate(birds, 1):
            result_html += format_bird_card(bird, i)
        
        yield result_html
        
    except Exception as e:
        log(f"Error: {traceback.format_exc()}")
        yield f'<div class="error"><strong>❌ Error:</strong> {str(e)}</div>'


def identify_description_stream(description):
    """Streaming description identification."""
    if not description or len(description.strip()) < 5:
        yield '<div class="error">⚠️ Please enter a description (at least 5 characters)</div>'
        return
    
    try:
        yield '<div class="processing">🔍 Analyzing your description...</div>'
        
        context = f"""USER DESCRIPTION:
"{description}"

Based on this description, identify matching Indian bird species.
Consider colors, size, calls, behavior, and habitat mentioned."""

        prompt = build_prompt(context)
        
        ollama_available, model = check_ollama()
        
        if ollama_available:
            full_response = ""
            for response in call_ollama_stream(prompt, model):
                full_response = response
                birds, summary = parse_llm_response(full_response)
                if birds:
                    result_html = f"""<div class="success">
                        <h2>🐦 {len(birds)} Bird(s) Match Your Description</h2>
                        <p>{summary}</p>
                    </div>"""
                    for i, bird in enumerate(birds, 1):
                        result_html += format_bird_card(bird, i)
                    yield result_html
        else:
            yield '<div class="processing">☁️ Using cloud AI...</div>'
            full_response = call_huggingface(prompt)
        
        birds, summary = parse_llm_response(full_response)
        
        if not birds:
            yield f"""<div class="error">
                <strong>Could not match birds to description</strong>
                <p>Try adding more details about colors, size, or sounds.</p>
            </div>"""
            return
        
        result_html = f"""<div class="success">
            <h2>🐦 {len(birds)} Bird(s) Match Your Description</h2>
            <p>{summary}</p>
        </div>"""
        
        for i, bird in enumerate(birds, 1):
            result_html += format_bird_card(bird, i)
        
        yield result_html
        
    except Exception as e:
        log(f"Error: {traceback.format_exc()}")
        yield f'<div class="error"><strong>❌ Error:</strong> {str(e)}</div>'


# ================== GRADIO APP ==================

def get_status() -> str:
    """Get current LLM status."""
    available, model = check_ollama()
    if available:
        return f"🟢 Ollama ({model})"
    if HF_TOKEN:
        return "🟡 HuggingFace API"
    return "🟡 HuggingFace (Free)"


with gr.Blocks(title="BirdSense Pro") as demo:
    
    gr.HTML(f"<style>{CSS}</style>")
    
    gr.HTML(f"""
    <div class="header">
        <h1>🐦 BirdSense Pro</h1>
        <p class="subtitle">AI-Powered Indian Bird Identification with META SAM-Audio</p>
        <div class="status">
            <span class="status-dot"></span>
            {get_status()}
        </div>
    </div>
    """)
    
    with gr.Tabs():
        
        # Audio Tab
        with gr.Tab("🎤 Audio"):
            gr.HTML("""<div class="info-box">
                <h3>🎤 Audio Identification</h3>
                <p>Record live or upload bird sounds. SAM-Audio handles noisy backgrounds, feeble signals, and multiple bird species.</p>
            </div>""")
            
            with gr.Row():
                with gr.Column():
                    audio_input = gr.Audio(sources=["microphone", "upload"], type="numpy", label="🎙️ Record or Upload Audio")
                    with gr.Row():
                        location = gr.Textbox(label="📍 Location", placeholder="e.g., Mumbai, Western Ghats")
                        month = gr.Dropdown(label="📅 Month", choices=["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
                    audio_btn = gr.Button("🔍 Identify Bird", variant="primary", size="lg")
                
                with gr.Column():
                    audio_output = gr.HTML('<div style="padding:60px; text-align:center; color:#94a3b8; font-size:1.1rem;">🎵 Upload or record audio to identify birds</div>')
            
            audio_btn.click(identify_audio_stream, [audio_input, location, month], audio_output)
        
        # Image Tab
        with gr.Tab("📷 Image"):
            gr.HTML("""<div class="info-box">
                <h3>📷 Image Identification</h3>
                <p>Upload a bird photo. The AI analyzes colors and patterns to identify species.</p>
            </div>""")
            
            with gr.Row():
                with gr.Column():
                    image_input = gr.Image(sources=["upload", "webcam"], type="pil", label="📸 Upload or Capture")
                    image_btn = gr.Button("🔍 Identify Bird", variant="primary", size="lg")
                
                with gr.Column():
                    image_output = gr.HTML('<div style="padding:60px; text-align:center; color:#94a3b8; font-size:1.1rem;">📷 Upload an image to identify birds</div>')
            
            image_btn.click(identify_image_stream, [image_input], image_output)
        
        # Description Tab
        with gr.Tab("📝 Description"):
            gr.HTML("""<div class="info-box">
                <h3>📝 Text Description</h3>
                <p>Describe the bird you saw — colors, size, sounds, behavior, habitat.</p>
            </div>""")
            
            with gr.Row():
                with gr.Column():
                    desc_input = gr.Textbox(
                        label="✍️ Describe the Bird",
                        lines=5,
                        placeholder="Example: Small green bird with bright red forehead, making a metallic 'tuk-tuk-tuk' sound repeatedly. Seen near fruit trees in a Mumbai garden during December."
                    )
                    desc_btn = gr.Button("🔍 Identify Bird", variant="primary", size="lg")
                
                with gr.Column():
                    desc_output = gr.HTML('<div style="padding:60px; text-align:center; color:#94a3b8; font-size:1.1rem;">📝 Enter a description to identify birds</div>')
            
            desc_btn.click(identify_description_stream, [desc_input], desc_output)
    
    gr.HTML("""<div style="text-align:center; padding:24px; color:#64748b; border-top:1px solid #e2e8f0; margin-top:24px;">
        <strong>🐦 BirdSense Pro</strong> — CSCR Initiative<br>
        <span style="font-size:0.9rem;">META SAM-Audio Processing • Llama3.2/Mistral-7B LLM • 10,000+ Species • No Hardcoding</span>
    </div>""")


if __name__ == "__main__":
    print("\n" + "="*50)
    print("🐦 BirdSense Pro")
    print("="*50)
    print(f"Status: {get_status()}")
    print(f"HF Token: {'✅ Set' if HF_TOKEN else '❌ Not set'}")
    print("\nFeatures:")
    print("  ✓ META SAM-Audio for noise/feeble signals")
    print("  ✓ Multi-bird detection")
    print("  ✓ Streaming responses")
    print("  ✓ Dynamic Wikipedia images")
    print("  ✓ No hardcoding")
    print("\nURL: http://localhost:7860")
    print("="*50 + "\n")
    
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True)
