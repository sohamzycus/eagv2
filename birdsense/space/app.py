"""
🐦 BirdSense - Cloud Version (HuggingFace Spaces / Render)
Developed by Soham

Uses cloud AI APIs instead of local Ollama for serverless deployment.
Supports: Replicate, Together AI, or HuggingFace Inference API

Environment Variables Required:
- REPLICATE_API_TOKEN (get free at replicate.com)
- Or: TOGETHER_API_KEY (get free at together.ai)
"""

import gradio as gr
import numpy as np
from scipy import signal
from scipy.ndimage import uniform_filter1d
from PIL import Image
import requests
import json
import re
import base64
import io
import os
import warnings

# Import feedback system
from feedback import (
    log_prediction,
    save_feedback,
    get_analytics,
    format_analytics_html,
)

warnings.filterwarnings('ignore')

# ============ CLOUD API CONFIG ============
# Priority: Replicate > Together > HuggingFace
REPLICATE_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "")
TOGETHER_KEY = os.environ.get("TOGETHER_API_KEY", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

def get_api_provider():
    """Determine which cloud API to use."""
    if REPLICATE_TOKEN:
        return "replicate"
    elif TOGETHER_KEY:
        return "together"
    elif HF_TOKEN:
        return "huggingface"
    else:
        return None

API_PROVIDER = get_api_provider()

# ============ CLOUD MODEL CALLS ============

def call_vision_model_cloud(image: Image.Image, prompt: str) -> str:
    """Call cloud vision model (LLaVA equivalent)."""
    
    # Convert image to base64
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    if API_PROVIDER == "replicate":
        return call_replicate_vision(img_base64, prompt)
    elif API_PROVIDER == "together":
        return call_together_vision(img_base64, prompt)
    elif API_PROVIDER == "huggingface":
        return call_hf_vision(img_base64, prompt)
    else:
        return json.dumps({
            "birds": [{"name": "Unknown", "confidence": 0, "reason": "No API configured"}],
            "error": "Please set REPLICATE_API_TOKEN or TOGETHER_API_KEY"
        })


def call_text_model_cloud(prompt: str) -> str:
    """Call cloud text model (Llama/phi4 equivalent)."""
    
    if API_PROVIDER == "replicate":
        return call_replicate_text(prompt)
    elif API_PROVIDER == "together":
        return call_together_text(prompt)
    elif API_PROVIDER == "huggingface":
        return call_hf_text(prompt)
    else:
        return json.dumps({
            "birds": [{"name": "Unknown", "confidence": 0}],
            "error": "No API configured"
        })


# ============ REPLICATE API ============

def call_replicate_vision(img_base64: str, prompt: str) -> str:
    """Call Replicate's LLaVA model."""
    try:
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {REPLICATE_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "version": "yorickvp/llava-13b:b5f6212d032508382d61ff00469ddbd4d8e3ac33c0f29a2f13af7e75a2f48be5",
                "input": {
                    "image": f"data:image/jpeg;base64,{img_base64}",
                    "prompt": prompt,
                    "max_tokens": 1000
                }
            },
            timeout=60
        )
        
        if response.status_code == 201:
            pred = response.json()
            # Poll for result
            get_url = pred.get("urls", {}).get("get")
            if get_url:
                for _ in range(30):  # Wait up to 30 seconds
                    import time
                    time.sleep(1)
                    result = requests.get(get_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
                    data = result.json()
                    if data.get("status") == "succeeded":
                        output = data.get("output", "")
                        return "".join(output) if isinstance(output, list) else str(output)
                    elif data.get("status") == "failed":
                        return json.dumps({"birds": [], "error": "Model failed"})
        
        return json.dumps({"birds": [], "error": f"API error: {response.status_code}"})
    except Exception as e:
        return json.dumps({"birds": [], "error": str(e)})


def call_replicate_text(prompt: str) -> str:
    """Call Replicate's Llama model."""
    try:
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {REPLICATE_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "version": "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
                "input": {
                    "prompt": prompt,
                    "max_tokens": 1000
                }
            },
            timeout=60
        )
        
        if response.status_code == 201:
            pred = response.json()
            get_url = pred.get("urls", {}).get("get")
            if get_url:
                for _ in range(30):
                    import time
                    time.sleep(1)
                    result = requests.get(get_url, headers={"Authorization": f"Token {REPLICATE_TOKEN}"})
                    data = result.json()
                    if data.get("status") == "succeeded":
                        output = data.get("output", "")
                        return "".join(output) if isinstance(output, list) else str(output)
                    elif data.get("status") == "failed":
                        return json.dumps({"birds": []})
        
        return json.dumps({"birds": []})
    except Exception as e:
        return json.dumps({"birds": [], "error": str(e)})


# ============ TOGETHER AI API ============

def call_together_vision(img_base64: str, prompt: str) -> str:
    """Call Together AI's vision model."""
    try:
        response = requests.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {TOGETHER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/Llama-Vision-Free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                        ]
                    }
                ],
                "max_tokens": 1000
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return json.dumps({"birds": [], "error": f"API error: {response.status_code}"})
    except Exception as e:
        return json.dumps({"birds": [], "error": str(e)})


def call_together_text(prompt: str) -> str:
    """Call Together AI's text model."""
    try:
        response = requests.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {TOGETHER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return json.dumps({"birds": []})
    except Exception as e:
        return json.dumps({"birds": [], "error": str(e)})


# ============ HUGGINGFACE API ============

def call_hf_vision(img_base64: str, prompt: str) -> str:
    """Call HuggingFace Inference API."""
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/llava-hf/llava-1.5-7b-hf",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt, "parameters": {"max_new_tokens": 500}},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()[0].get("generated_text", "")
        return json.dumps({"birds": []})
    except Exception as e:
        return json.dumps({"birds": [], "error": str(e)})


def call_hf_text(prompt: str) -> str:
    """Call HuggingFace text model."""
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt, "parameters": {"max_new_tokens": 500}},
            timeout=60
        )
        if response.status_code == 200:
            return response.json()[0].get("generated_text", "")
        return json.dumps({"birds": []})
    except Exception as e:
        return json.dumps({"birds": [], "error": str(e)})


# ============ AUDIO PROCESSING (META SAM-Audio) ============

SAM_FREQ_BANDS = {
    "very_low": (100, 500),
    "low": (500, 1500),
    "mid": (1500, 4000),
    "high": (4000, 8000),
    "very_high": (8000, 12000)
}

def extract_audio_features(audio_data, sr):
    """Extract acoustic features for bird identification."""
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)
    
    audio_data = audio_data.astype(np.float32)
    audio_data = audio_data / (np.max(np.abs(audio_data)) + 1e-8)
    
    features = {
        "duration": len(audio_data) / sr,
        "sample_rate": sr,
        "bands": {}
    }
    
    # Analyze frequency bands
    for band_name, (low, high) in SAM_FREQ_BANDS.items():
        nyq = sr / 2
        if high > nyq:
            high = nyq - 1
        if low >= high:
            continue
            
        try:
            b, a = signal.butter(4, [low/nyq, high/nyq], btype='band')
            filtered = signal.filtfilt(b, a, audio_data)
            energy = np.sqrt(np.mean(filtered**2))
            features["bands"][band_name] = round(float(energy), 4)
        except:
            features["bands"][band_name] = 0.0
    
    # Dominant band
    if features["bands"]:
        features["dominant_band"] = max(features["bands"], key=features["bands"].get)
    
    # Frequency estimation
    try:
        freqs, psd = signal.welch(audio_data, sr, nperseg=min(2048, len(audio_data)))
        peak_idx = np.argmax(psd)
        features["peak_freq"] = int(freqs[peak_idx])
        
        # Frequency range
        threshold = np.max(psd) * 0.1
        active = freqs[psd > threshold]
        if len(active) > 0:
            features["min_freq"] = int(active[0])
            features["max_freq"] = int(active[-1])
            features["freq_range"] = features["max_freq"] - features["min_freq"]
    except:
        features["peak_freq"] = 0
    
    return features


# ============ RESULT FORMATTING ============

def get_bird_image(bird_name):
    """Fetch bird image from Wikipedia."""
    try:
        search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{bird_name.replace(' ', '_')}"
        resp = requests.get(search_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if "thumbnail" in data:
                return data["thumbnail"]["source"]
    except:
        pass
    return None


def parse_birds(response_text):
    """Parse bird data from LLM response."""
    try:
        # Extract JSON from markdown
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            response_text = json_match.group(1)
        
        data = json.loads(response_text)
        return data.get("birds", [])
    except:
        return []


def deduplicate_birds(birds):
    """Deduplicate birds by name, keeping highest confidence."""
    seen = {}
    for bird in birds:
        name = bird.get('name', '').lower()
        if name and (name not in seen or bird.get('confidence', 0) > seen[name].get('confidence', 0)):
            seen[name] = bird
    return list(seen.values())


def format_bird_result(birds):
    """Format bird results as HTML."""
    if not birds:
        return "<p>No birds identified</p>"
    
    html = "<div style='display:grid;gap:16px;'>"
    
    for bird in birds[:5]:
        name = bird.get('name', 'Unknown')
        conf = bird.get('confidence', 0)
        reason = bird.get('reason', '')
        
        img_url = get_bird_image(name)
        img_html = f"<img src='{img_url}' style='width:120px;height:120px;object-fit:cover;border-radius:8px;'/>" if img_url else ""
        
        html += f"""
        <div style='display:flex;gap:16px;padding:16px;background:#f8fafc;border-radius:12px;'>
            {img_html}
            <div>
                <h3 style='margin:0;color:#1e40af;'>{name}</h3>
                <div style='color:#64748b;'>Confidence: {conf}%</div>
                <div style='margin-top:8px;font-size:0.9em;'>{reason}</div>
            </div>
        </div>
        """
    
    html += "</div>"
    return html


# ============ IDENTIFICATION FUNCTIONS ============

from prompts import (
    AUDIO_IDENTIFICATION_PROMPT,
    IMAGE_IDENTIFICATION_PROMPT,
    DESCRIPTION_IDENTIFICATION_PROMPT
)


def identify_audio(audio_input, location="", month=""):
    """Identify bird from audio using cloud API."""
    if audio_input is None:
        return "<p style='color:#ef4444;'>Please upload audio</p>"
    
    try:
        sr, audio_data = audio_input
        features = extract_audio_features(audio_data, sr)
        
        prompt = AUDIO_IDENTIFICATION_PROMPT.format(
            duration=features.get('duration', 0),
            peak_freq=features.get('peak_freq', 0),
            dominant_band=features.get('dominant_band', 'unknown'),
            min_freq=features.get('min_freq', 0),
            max_freq=features.get('max_freq', 0),
            freq_range=features.get('freq_range', 0),
            location=location or "unknown",
            month=month or "unknown"
        )
        
        response = call_text_model_cloud(prompt)
        birds = parse_birds(response)
        birds = deduplicate_birds(birds)
        
        # Log prediction
        log_prediction("audio", birds, features)
        
        return format_bird_result(birds)
        
    except Exception as e:
        return f"<p style='color:#ef4444;'>Error: {str(e)}</p>"


def identify_image(image_input):
    """Identify bird from image using cloud vision API."""
    if image_input is None:
        return "<p style='color:#ef4444;'>Please upload an image</p>"
    
    try:
        if not isinstance(image_input, Image.Image):
            image_input = Image.fromarray(image_input)
        
        image_input = image_input.convert("RGB")
        
        response = call_vision_model_cloud(image_input, IMAGE_IDENTIFICATION_PROMPT)
        birds = parse_birds(response)
        birds = deduplicate_birds(birds)
        
        # Log prediction
        log_prediction("image", birds)
        
        return format_bird_result(birds)
        
    except Exception as e:
        return f"<p style='color:#ef4444;'>Error: {str(e)}</p>"


def identify_description(description):
    """Identify bird from description."""
    if not description or not description.strip():
        return "<p style='color:#ef4444;'>Please enter a description</p>"
    
    try:
        prompt = DESCRIPTION_IDENTIFICATION_PROMPT.format(description=description)
        response = call_text_model_cloud(prompt)
        birds = parse_birds(response)
        birds = deduplicate_birds(birds)
        
        # Log prediction
        log_prediction("description", birds)
        
        return format_bird_result(birds)
        
    except Exception as e:
        return f"<p style='color:#ef4444;'>Error: {str(e)}</p>"


# ============ GRADIO UI ============

def submit_feedback(is_correct, correct_species, notes):
    """Handle feedback submission."""
    save_feedback("latest", is_correct, correct_species if not is_correct else None, notes)
    return "✅ Thank you! Your feedback helps improve BirdSense."


def create_app():
    api_status = "✅ " + API_PROVIDER.title() if API_PROVIDER else "❌ No API configured"
    
    with gr.Blocks(title="BirdSense - By Soham") as app:
        gr.Markdown(f"""
# 🐦 BirdSense - AI Bird Identification
**Developed by Soham** | Cloud Version

API: {api_status}
""")
        
        if not API_PROVIDER:
            gr.Markdown("""
⚠️ **Setup Required**: Set one of these environment variables:
- `REPLICATE_API_TOKEN` - Get free at [replicate.com](https://replicate.com)
- `TOGETHER_API_KEY` - Get free at [together.ai](https://together.ai)
- `HF_TOKEN` - Get at [huggingface.co](https://huggingface.co/settings/tokens)
""")
        
        with gr.Tab("🎵 Audio"):
            with gr.Row():
                with gr.Column():
                    audio_in = gr.Audio(sources=["upload", "microphone"], type="numpy", label="Bird Call")
                    with gr.Row():
                        loc = gr.Textbox(label="Location", placeholder="e.g., Mumbai")
                        mon = gr.Dropdown(label="Month", choices=[""] + ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
                    audio_btn = gr.Button("🔍 Identify", variant="primary")
                with gr.Column():
                    audio_out = gr.HTML("<p style='color:#64748b;padding:40px;text-align:center'>Upload audio</p>")
            audio_btn.click(identify_audio, [audio_in, loc, mon], audio_out)
        
        with gr.Tab("📷 Image"):
            with gr.Row():
                with gr.Column():
                    img_in = gr.Image(sources=["upload", "webcam"], type="pil", label="Bird Photo")
                    img_btn = gr.Button("🔍 Identify", variant="primary")
                with gr.Column():
                    img_out = gr.HTML("<p style='color:#64748b;padding:40px;text-align:center'>Upload image</p>")
            img_btn.click(identify_image, [img_in], img_out)
        
        with gr.Tab("📝 Description"):
            with gr.Row():
                with gr.Column():
                    desc_in = gr.Textbox(label="Description", lines=4, placeholder="Large blue and yellow parrot...")
                    desc_btn = gr.Button("🔍 Identify", variant="primary")
                with gr.Column():
                    desc_out = gr.HTML("<p style='color:#64748b;padding:40px;text-align:center'>Enter description</p>")
            desc_btn.click(identify_description, [desc_in], desc_out)
        
        with gr.Tab("📝 Feedback"):
            gr.Markdown("### Help Improve BirdSense!")
            with gr.Row():
                with gr.Column():
                    fb_correct = gr.Radio(["✅ Correct", "❌ Incorrect"], label="Was the ID correct?", value="✅ Correct")
                    fb_species = gr.Textbox(label="Correct Species (if wrong)", placeholder="e.g., House Sparrow")
                    fb_notes = gr.Textbox(label="Notes", lines=2)
                    fb_btn = gr.Button("📤 Submit Feedback", variant="primary")
                with gr.Column():
                    fb_result = gr.Markdown("*Submit feedback to help improve*")
            fb_btn.click(lambda c, s, n: submit_feedback(c == "✅ Correct", s, n), [fb_correct, fb_species, fb_notes], fb_result)
        
        with gr.Tab("📊 Analytics"):
            analytics = gr.HTML(format_analytics_html())
            refresh_btn = gr.Button("🔄 Refresh")
            refresh_btn.click(format_analytics_html, outputs=analytics)
        
        gr.Markdown("---\n**🐦 BirdSense by Soham** | Submit feedback to help improve!")
    
    return app


# ============ MAIN ============

if __name__ == "__main__":
    print("🐦 BirdSense - Cloud Version")
    print("=" * 40)
    print(f"API Provider: {API_PROVIDER or 'None configured'}")
    print("=" * 40)
    
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860)

