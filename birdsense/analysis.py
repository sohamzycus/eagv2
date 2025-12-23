"""
🐦 BirdSense - Bird Analysis Module
Developed by Soham

Contains all bird identification logic:
- Audio analysis (META SAM-Audio + BirdNET + LLM)
- Image analysis (Vision models)
- Description analysis (Text models)
"""

import numpy as np
import scipy.signal as signal
from scipy.ndimage import gaussian_filter1d
from PIL import Image
import json
import re
import tempfile
import os
import time
from typing import List, Dict, Any, Optional, Generator

from providers import provider_factory
from prompts import get_audio_prompt, get_image_prompt, get_description_prompt, get_enrichment_prompt

# Import enhanced corrections and filters
try:
    from enhanced_prompts import (
        filter_non_indian_birds, 
        apply_acoustic_correction, 
        CONFUSION_SPECIES_MATRIX,
        get_confusion_prompt
    )
    ENHANCED_CORRECTIONS_AVAILABLE = True
except ImportError:
    ENHANCED_CORRECTIONS_AVAILABLE = False
    print("⚠️ Enhanced corrections not available")

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


# ============ SAM-AUDIO CONFIG ============
SAM_FREQ_BANDS = [
    (100, 500, "very_low"),    # Owls hooting, bitterns
    (500, 1500, "low"),        # Crows, doves, owl screeches
    (1500, 3000, "medium"),    # Thrushes, mynas
    (3000, 6000, "high"),      # Finches, sparrows
    (6000, 10000, "very_high") # Warblers
]


# ============ META SAM-AUDIO CLASS ============
class SAMAudio:
    """META SAM-inspired audio source separation and enhancement for bird calls."""
    
    def __init__(self):
        self.freq_bands = SAM_FREQ_BANDS
        self.bird_freq_low = 300   # Hz - lower bound for bird calls
        self.bird_freq_high = 10000  # Hz - upper bound for bird calls
    
    def enhance_audio(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        🔊 META SAM-Audio Enhancement Pipeline:
        1. Bandpass filter to bird frequency range (300-10000 Hz)
        2. Spectral noise reduction
        3. Dynamic range compression
        4. Normalization
        
        This MUST be called before BirdNET or LLM analysis!
        """
        if len(audio) < 1024:
            return audio
        
        try:
            # Step 1: Bandpass filter to bird frequencies (300-10000 Hz)
            nyq = sr / 2
            low_norm = self.bird_freq_low / nyq
            high_norm = min(self.bird_freq_high / nyq, 0.99)
            
            if low_norm < high_norm and low_norm > 0:
                b, a = signal.butter(4, [low_norm, high_norm], btype='band')
                audio = signal.filtfilt(b, a, audio)
            
            # Step 2: Spectral noise reduction (simple spectral subtraction)
            # Estimate noise from quietest 10% of signal
            frame_size = min(2048, len(audio) // 8)
            if frame_size > 256:
                num_frames = len(audio) // frame_size
                frame_energies = []
                for i in range(num_frames):
                    frame = audio[i*frame_size:(i+1)*frame_size]
                    frame_energies.append(np.sum(frame**2))
                
                # Find noise floor from quietest frames
                sorted_energies = sorted(frame_energies)
                noise_threshold = sorted_energies[max(0, int(num_frames * 0.1))]
                
                # Apply soft gating - reduce quiet parts, keep bird calls
                for i in range(num_frames):
                    if frame_energies[i] < noise_threshold * 2:
                        # Reduce noise in quiet parts
                        start = i * frame_size
                        end = (i + 1) * frame_size
                        audio[start:end] *= 0.3  # Attenuate noise
            
            # Step 3: Dynamic range compression (make quiet parts louder)
            # Compute envelope
            envelope = np.abs(signal.hilbert(audio))
            envelope = gaussian_filter1d(envelope, sigma=sr//100)  # Smooth ~10ms
            
            # Compress dynamic range
            max_env = np.max(envelope) + 1e-10
            compression_ratio = 0.5  # Reduce dynamic range by 50%
            
            # Apply compression to make bird calls more prominent
            gain = (envelope / max_env) ** (-compression_ratio + 1)
            gain = np.clip(gain, 0.5, 3.0)  # Limit gain range
            audio = audio * gain
            
            # Step 4: Final normalization
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / max_val * 0.95  # Leave headroom
            
            return audio
            
        except Exception as e:
            print(f"SAM-Audio enhancement error: {e}")
            return audio
    
    def amplify_bird_frequencies(self, audio: np.ndarray, sr: int, 
                                   target_freq: int = None) -> np.ndarray:
        """
        Selectively amplify specific bird frequency ranges.
        Useful when we know the expected bird's frequency from BirdNET hints.
        """
        if len(audio) < 1024:
            return audio
        
        try:
            # Default: amplify mid-range bird frequencies (1000-4000 Hz)
            if target_freq is None:
                low_freq = 1000
                high_freq = 4000
            else:
                # Create band around target frequency
                low_freq = max(300, target_freq - 500)
                high_freq = min(10000, target_freq + 500)
            
            nyq = sr / 2
            low_norm = low_freq / nyq
            high_norm = min(high_freq / nyq, 0.99)
            
            if low_norm < high_norm and low_norm > 0:
                # Create bandpass for target frequencies
                b, a = signal.butter(3, [low_norm, high_norm], btype='band')
                enhanced_band = signal.filtfilt(b, a, audio)
                
                # Mix enhanced band with original (boost by 2x)
                audio = audio + enhanced_band * 1.5
                
                # Normalize
                max_val = np.max(np.abs(audio))
                if max_val > 0:
                    audio = audio / max_val * 0.95
            
            return audio
            
        except Exception as e:
            print(f"Frequency amplification error: {e}")
            return audio
    
    def detect_bird_segments(self, audio: np.ndarray, sr: int) -> List[Dict]:
        """Detect bird call segments using energy analysis."""
        segments = []
        
        # Compute spectrogram
        nperseg = min(1024, len(audio) // 4)
        if nperseg < 64:
            return segments
        
        f, t, Sxx = signal.spectrogram(audio, sr, nperseg=nperseg, noverlap=nperseg//2)
        
        # Focus on bird frequency range (500-8000 Hz)
        bird_mask = (f >= 500) & (f <= 8000)
        bird_energy = np.sum(Sxx[bird_mask, :], axis=0)
        
        # Smooth and threshold
        bird_energy = gaussian_filter1d(bird_energy, sigma=3)
        threshold = np.mean(bird_energy) + 0.5 * np.std(bird_energy)
        
        # Find segments above threshold
        above = bird_energy > threshold
        changes = np.diff(above.astype(int))
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]
        
        if above[0]:
            starts = np.insert(starts, 0, 0)
        if above[-1]:
            ends = np.append(ends, len(above) - 1)
        
        min_segments = min(len(starts), len(ends))
        for i in range(min_segments):
            start_time = t[starts[i]] if starts[i] < len(t) else t[-1]
            end_time = t[ends[i]] if ends[i] < len(t) else t[-1]
            if end_time - start_time > 0.1:  # Min 100ms
                segments.append({
                    "start": start_time,
                    "end": end_time,
                    "energy": float(np.mean(bird_energy[starts[i]:ends[i]+1]))
                })
        
        return segments[:10]
    
    def separate_multiple_birds(self, audio: np.ndarray, sr: int) -> List[Dict]:
        """Separate multiple birds by frequency bands."""
        isolated_birds = []
        
        for low, high, band_name in self.freq_bands:
            # Bandpass filter
            nyq = sr / 2
            low_norm = low / nyq
            high_norm = min(high / nyq, 0.99)
            
            if low_norm >= high_norm or low_norm <= 0:
                continue
            
            try:
                b, a = signal.butter(4, [low_norm, high_norm], btype='band')
                filtered = signal.filtfilt(b, a, audio)
                
                # Check energy in band
                energy = np.sum(filtered ** 2)
                if energy > 0.001 * np.sum(audio ** 2):
                    isolated_birds.append({
                        "band": band_name,
                        "freq_range": (low, high),
                        "audio": filtered,
                        "energy": energy
                    })
            except Exception:
                continue
        
        isolated_birds.sort(key=lambda x: x["energy"], reverse=True)
        return isolated_birds[:3]


# ============ FEATURE EXTRACTION ============
def extract_audio_features(audio: np.ndarray, sr: int) -> Dict[str, Any]:
    """Extract acoustic features for bird identification."""
    features = {
        "duration": round(len(audio) / sr, 2),
        "min_freq": 0, "max_freq": 0, "peak_freq": 0, "freq_range": 0,
        "pattern": "unknown", "syllables": 0, "complexity": "unknown",
        "rhythm": "unknown", "quality": "unknown"
    }
    
    if len(audio) < 1024:
        return features
    
    try:
        # Compute spectrogram
        nperseg = min(2048, len(audio) // 2)
        f, t, Sxx = signal.spectrogram(audio, sr, nperseg=nperseg, noverlap=nperseg//2)
        
        # Find peak frequencies
        power = np.sum(Sxx, axis=1)
        peak_idx = np.argmax(power)
        features["peak_freq"] = int(f[peak_idx])
        
        # Frequency range (where 90% of energy is)
        cumsum = np.cumsum(power)
        total = cumsum[-1]
        if total > 0:
            low_idx = np.searchsorted(cumsum, 0.05 * total)
            high_idx = np.searchsorted(cumsum, 0.95 * total)
            features["min_freq"] = int(f[max(0, low_idx)])
            features["max_freq"] = int(f[min(len(f)-1, high_idx)])
            features["freq_range"] = features["max_freq"] - features["min_freq"]
        
        # Pattern analysis
        energy_over_time = np.sum(Sxx, axis=0)
        energy_smooth = gaussian_filter1d(energy_over_time, sigma=2)
        
        if len(energy_smooth) > 2:
            peaks, _ = signal.find_peaks(energy_smooth, height=np.mean(energy_smooth))
            features["syllables"] = len(peaks)
            
            if len(peaks) > 5:
                features["pattern"] = "complex_song"
            elif len(peaks) > 2:
                features["pattern"] = "repeated_phrases"
            else:
                features["pattern"] = "simple_call"
        
        # Complexity
        freq_variation = np.std(power) / (np.mean(power) + 1e-10)
        features["complexity"] = "high" if freq_variation > 1.5 else "medium" if freq_variation > 0.5 else "low"
        
        # Rhythm
        if features["syllables"] > 0 and features["duration"] > 0:
            rate = features["syllables"] / features["duration"]
            features["rhythm"] = "fast" if rate > 5 else "moderate" if rate > 2 else "slow/deliberate"
        
        # Quality (SNR estimate)
        snr = np.max(np.abs(audio)) / (np.std(audio) + 1e-10)
        features["quality"] = "clear" if snr > 3 else "moderate" if snr > 1.5 else "faint"
        
    except Exception as e:
        print(f"Feature extraction error: {e}")
    
    return features


# ============ BIRDNET IDENTIFICATION ============
def identify_with_birdnet(audio: np.ndarray, sr: int, location: str = "", month: str = "") -> List[Dict]:
    """Identify birds using BirdNET."""
    if not BIRDNET_AVAILABLE or birdnet_analyzer is None:
        return []
    
    results = []
    temp_path = None
    
    try:
        # Save to temp WAV file
        from scipy.io import wavfile
        
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Resample to 48kHz if needed
        if sr != 48000:
            from scipy import signal as sig
            num_samples = int(len(audio_int16) * 48000 / sr)
            audio_int16 = sig.resample(audio_int16, num_samples).astype(np.int16)
            sr = 48000
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        wavfile.write(temp_path, sr, audio_int16)
        
        # Create Recording with lower confidence to catch more birds
        lat, lon = None, None
        recording = Recording(
            birdnet_analyzer,
            temp_path,
            lat=lat, lon=lon,
            min_conf=0.2  # Lower threshold to detect more species
        )
        recording.analyze()
        
        # Process results - get up to 10 detections
        for detection in recording.detections[:10]:
            species = detection.get('common_name', detection.get('scientific_name', 'Unknown'))
            scientific = detection.get('scientific_name', '')
            confidence = detection.get('confidence', 0)
            
            results.append({
                "name": species,
                "scientific": scientific,
                "confidence": int(confidence * 100),
                "source": "BirdNET"
            })
        
    except Exception as e:
        print(f"BirdNET error: {e}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass
    
    return results


# ============ PARSING HELPERS ============
def parse_birds(response: str) -> List[Dict]:
    """Parse bird identification from LLM response."""
    if not response:
        return []
    
    # Try to extract JSON
    try:
        # Handle markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        # Find JSON object
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            data = json.loads(json_str)
            
            birds = data.get("birds", [])
            result = []
            for bird in birds:
                if isinstance(bird, dict) and bird.get("name"):
                    result.append({
                        "name": bird.get("name", "Unknown"),
                        "scientific_name": bird.get("scientific_name", ""),
                        "confidence": bird.get("confidence", 50),
                        "reason": bird.get("reason", "")
                    })
            return result
    except json.JSONDecodeError:
        pass
    
    return []


def deduplicate_birds(birds: List[Dict]) -> List[Dict]:
    """Remove duplicate birds, keeping highest confidence."""
    seen = {}
    for bird in birds:
        name = bird.get("name", "").lower().strip()
        if name and (name not in seen or bird.get("confidence", 0) > seen[name].get("confidence", 0)):
            seen[name] = bird
    return list(seen.values())


def fetch_bird_image(bird_name: str, scientific_name: str = "") -> Optional[str]:
    """Fetch bird image - prioritize mobile-friendly sources (iNaturalist)."""
    import requests
    import urllib.parse
    
    headers = {
        "User-Agent": "BirdSense/1.0 (Bird Identification App)"
    }
    
    # 1. PRIORITY: iNaturalist (works on mobile, high quality photos)
    try:
        search_term = scientific_name if scientific_name else bird_name
        inaturalist_url = f"https://api.inaturalist.org/v1/taxa?q={search_term}&rank=species&is_active=true&per_page=5"
        resp = requests.get(inaturalist_url, headers=headers, timeout=8, verify=False)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            for taxon in results:
                # Verify it's a bird (Aves class)
                if taxon.get("iconic_taxon_name") == "Aves" or "bird" in str(taxon.get("preferred_common_name", "")).lower():
                    if taxon.get("default_photo"):
                        img_url = taxon["default_photo"].get("medium_url") or taxon["default_photo"].get("original_url")
                        if img_url:
                            # Use medium size for better mobile loading
                            img_url = img_url.replace("/square.", "/medium.").replace("/small.", "/medium.")
                            print(f"✅ Found image via iNaturalist for: {bird_name}")
                            return img_url
    except Exception as e:
        print(f"iNaturalist error for {bird_name}: {e}")
    
    # 2. Try eBird/Macaulay Library (Cornell - excellent bird photos)
    try:
        search_term = scientific_name if scientific_name else bird_name
        # Macaulay Library search
        ml_url = f"https://search.macaulaylibrary.org/api/v1/search?taxonCode=&q={urllib.parse.quote(search_term)}&mediaType=photo&sort=rating_rank_desc&count=1"
        resp = requests.get(ml_url, headers=headers, timeout=5, verify=False)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", {}).get("content", [])
            if results and len(results) > 0:
                asset_id = results[0].get("assetId")
                if asset_id:
                    img_url = f"https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{asset_id}/640"
                    print(f"✅ Found image via Macaulay Library for: {bird_name}")
                    return img_url
    except Exception as e:
        print(f"Macaulay Library error for {bird_name}: {e}")
    
    # 3. Fallback: Use Unsplash source (always works, returns relevant bird image)
    # This is a redirect URL that returns a random image matching the query
    query = urllib.parse.quote(f"{bird_name} bird")
    unsplash_url = f"https://source.unsplash.com/600x400/?{query}"
    print(f"📷 Using Unsplash fallback for: {bird_name}")
    return unsplash_url


def get_enriched_bird_info(bird_name: str, scientific_name: str = "", location: str = "") -> Dict[str, Any]:
    """Get enriched info using LLM - ALWAYS includes India info."""
    info = {
        "summary": "",
        "habitat": "",
        "diet": "",
        "fun_facts": [],
        "conservation": "",
        "range": "",
        "image_url": None,
        "india_info": None
    }
    
    # First fetch image
    info["image_url"] = fetch_bird_image(bird_name, scientific_name)
    
    # Try Wikipedia for basic info
    try:
        import requests
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": bird_name,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "exsentences": 6,
            "redirects": 1
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                if "extract" in page and len(page["extract"]) > 50:
                    info["summary"] = page["extract"][:400]
    except:
        pass
    
    # ALWAYS use India-specific prompt to get local names (useful for Indian users)
    try:
        # Always use India prompt to get local names and India presence info
        prompt = get_enrichment_prompt(bird_name, scientific_name, "India")
        response = provider_factory.call_text(prompt)
        
        if response:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                llm_info = json.loads(response[start:end])
                
                # Merge LLM info
                if llm_info.get("summary"):
                    info["summary"] = llm_info["summary"]
                if llm_info.get("habitat"):
                    info["habitat"] = llm_info["habitat"]
                if llm_info.get("diet"):
                    info["diet"] = llm_info["diet"]
                if llm_info.get("fun_facts"):
                    info["fun_facts"] = llm_info["fun_facts"]
                if llm_info.get("conservation"):
                    info["conservation"] = llm_info["conservation"]
                if llm_info.get("range"):
                    info["range"] = llm_info["range"]
                # Always include india_info if available
                if llm_info.get("india_info"):
                    info["india_info"] = llm_info["india_info"]
                    
    except Exception as e:
        print(f"LLM enrichment error: {e}")
    
    return info


def format_bird_result(bird: Dict, index: int, include_enrichment: bool = True, location: str = "", total_birds: int = 1) -> str:
    """Format a single bird result as rich HTML with image, details, and India info. Uses accordion if multiple birds."""
    name = bird.get("name", "Unknown")
    scientific = bird.get("scientific_name", "")
    confidence = bird.get("confidence", 50)
    reason = bird.get("reason", "")
    source = bird.get("source", "LLM")
    
    # Confidence color
    if confidence >= 70:
        conf_color = "#22c55e"
        conf_bg = "#dcfce7"
    elif confidence >= 50:
        conf_color = "#f59e0b"
        conf_bg = "#fef3c7"
    else:
        conf_color = "#ef4444"
        conf_bg = "#fef2f2"
    
    # Fetch enriched info (always includes India info)
    enriched = {"image_url": None, "summary": "", "habitat": "", "diet": "", "fun_facts": [], "conservation": "", "india_info": None}
    if include_enrichment:
        enriched = get_enriched_bird_info(name, scientific, location)
    
    # Image HTML
    img_url = enriched.get("image_url") or fetch_bird_image(name, scientific)
    if img_url:
        image_html = f'''<div style="flex-shrink:0;margin-right:20px;">
            <img src="{img_url}" style="width:180px;height:180px;object-fit:cover;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.15);" 
                 onerror="this.onerror=null;this.parentElement.innerHTML='<div style=\\'width:180px;height:180px;background:linear-gradient(135deg,#dbeafe,#e0e7ff);border-radius:12px;display:flex;align-items:center;justify-content:center;color:#3b82f6;font-size:4em\\'>🐦</div>'"
                 alt="{name}">
        </div>'''
    else:
        image_html = f'''<div style="flex-shrink:0;margin-right:20px;">
            <div style="width:180px;height:180px;background:linear-gradient(135deg,#dbeafe,#e0e7ff);border-radius:12px;display:flex;align-items:center;justify-content:center;color:#3b82f6;font-size:4em;">🐦</div>
        </div>'''
    
    # Header section (always visible)
    header_html = f'''
    <div style="display:flex;align-items:flex-start;">
        {image_html}
        <div style="flex:1;min-width:0;">
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                <span style="font-size:1.3em;font-weight:700;color:#1e293b;">#{index} {name}</span>
                <span style="background:{conf_bg};color:{conf_color};padding:4px 12px;border-radius:20px;font-weight:600;font-size:0.85em;">{confidence}%</span>
                <span style="background:#e2e8f0;padding:3px 10px;border-radius:4px;font-size:0.8em;color:#475569;">📊 {source}</span>
            </div>
            <div style="color:#64748b;font-style:italic;margin:6px 0;font-size:0.95em;">{scientific}</div>
            <div style="color:#64748b;font-size:0.85em;margin-top:8px;"><b>🔍</b> {reason[:150]}{"..." if len(reason) > 150 else ""}</div>
        </div>
    </div>'''
    
    # Enrichment summary
    enrichment_html = ""
    if enriched.get("summary"):
        summary = enriched["summary"][:300] + "..." if len(enriched.get("summary", "")) > 300 else enriched.get("summary", "")
        enrichment_html = f'<div style="color:#475569;font-size:0.9em;line-height:1.5;margin:12px 0;padding:10px;background:#f8fafc;border-radius:8px;border-left:3px solid #3b82f6;">{summary}</div>'
    
    # Details - habitat, diet, conservation as separate full-width blocks
    details_html = ""
    if enriched.get("habitat"):
        habitat = enriched["habitat"]
        details_html += f'<div style="background:#ecfdf5;color:#065f46;padding:8px 12px;border-radius:6px;font-size:0.9em;margin:8px 0;white-space:normal;word-wrap:break-word;">🏠 {habitat}</div>'
    if enriched.get("diet"):
        diet = enriched["diet"]
        details_html += f'<div style="background:#fef3c7;color:#92400e;padding:8px 12px;border-radius:6px;font-size:0.9em;margin:8px 0;white-space:normal;word-wrap:break-word;">🍽️ {diet}</div>'
    if enriched.get("conservation"):
        cons = enriched["conservation"]
        cons_labels = {"LC": "Least Concern", "NT": "Near Threatened", "VU": "Vulnerable", "EN": "Endangered", "CR": "Critically Endangered"}
        cons_colors = {"LC": "#22c55e", "NT": "#84cc16", "VU": "#f59e0b", "EN": "#f97316", "CR": "#ef4444"}
        cons_key = cons.upper()[:2] if cons else "LC"
        cons_color = cons_colors.get(cons_key, "#64748b")
        cons_label = cons_labels.get(cons_key, cons)
        details_html += f'<div style="background:{cons_color};color:white;padding:6px 12px;border-radius:6px;font-size:0.9em;display:inline-block;margin:8px 0;">🛡️ {cons_label}</div>'
    
    # Fun facts
    fun_facts_html = ""
    if enriched.get("fun_facts") and isinstance(enriched["fun_facts"], list):
        facts = [f for f in enriched["fun_facts"][:2] if f]
        if facts:
            facts_list = "".join([f'<li style="margin:4px 0;color:#475569;">{fact}</li>' for fact in facts])
            fun_facts_html = f'<div style="margin:10px 0;padding:10px;background:#fefce8;border-radius:8px;"><b style="color:#854d0e;">💡 Fun Facts:</b><ul style="margin:6px 0 0 16px;padding:0;">{facts_list}</ul></div>'
    
    # India-specific info section (ALWAYS show if bird is found in India)
    india_html = ""
    india_info = enriched.get("india_info")
    if india_info and isinstance(india_info, dict):
        found_in_india = india_info.get("found_in_india", False)
        if found_in_india:
            india_parts = []
            
            # Local names
            local_names = india_info.get("local_names", {})
            if local_names and isinstance(local_names, dict):
                names_str = []
                for lang, lname in [("hindi", "Hindi"), ("marathi", "Marathi"), ("tamil", "Tamil"), ("bengali", "Bengali"), ("kannada", "Kannada")]:
                    if local_names.get(lang):
                        names_str.append(f"<b>{lname}:</b> {local_names[lang]}")
                if names_str:
                    india_parts.append(f'<div style="margin:4px 0;">🗣️ {" | ".join(names_str[:3])}</div>')
            
            if india_info.get("regions"):
                india_parts.append(f'<div style="margin:6px 0;white-space:normal;word-wrap:break-word;">📍 <b>Found in:</b> {india_info["regions"]}</div>')
            if india_info.get("best_season"):
                india_parts.append(f'<div style="margin:6px 0;white-space:normal;word-wrap:break-word;">📅 <b>Best season:</b> {india_info["best_season"]}</div>')
            if india_info.get("notable_locations"):
                india_parts.append(f'<div style="margin:6px 0;white-space:normal;word-wrap:break-word;">🔭 <b>Birding spots:</b> {india_info["notable_locations"]}</div>')
            
            if india_parts:
                india_html = f'''<div style="margin:10px 0;padding:12px;background:linear-gradient(135deg,#fff7ed,#ffedd5);border-radius:8px;border-left:3px solid #f97316;overflow:visible;">
                    <div style="font-weight:600;color:#c2410c;margin-bottom:8px;">🇮🇳 India</div>
                    <div style="color:#7c2d12;font-size:0.9em;line-height:1.5;">{"".join(india_parts)}</div>
                </div>'''
        else:
            # Bird not found in India
            india_html = f'<div style="margin:10px 0;padding:8px;background:#f1f5f9;border-radius:6px;font-size:0.85em;color:#64748b;">🌍 This species is not commonly found in India</div>'
    
    # Combine details content
    details_content = f"{enrichment_html}{details_html}{fun_facts_html}{india_html}"
    
    # Use accordion only if multiple birds
    if total_birds > 1:
        # Collapsible accordion format
        is_open = "open" if index == 1 else ""  # First one open by default
        return f'''
        <details {is_open} style="margin:10px 0;border:1px solid #e2e8f0;border-radius:12px;background:white;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
            <summary style="padding:16px;cursor:pointer;list-style:none;display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.2em;">{"▼" if is_open else "▶"}</span>
                <img src="{img_url if img_url else ''}" style="width:50px;height:50px;object-fit:cover;border-radius:8px;{'display:none' if not img_url else ''}" onerror="this.style.display='none'">
                <span style="font-weight:600;font-size:1.1em;color:#1e293b;">#{index} {name}</span>
                <span style="color:#64748b;font-style:italic;font-size:0.9em;">{scientific}</span>
                <span style="background:{conf_bg};color:{conf_color};padding:2px 10px;border-radius:12px;font-size:0.8em;margin-left:auto;">{confidence}%</span>
            </summary>
            <div style="padding:0 16px 16px 16px;border-top:1px solid #f1f5f9;">
                {header_html}
                {details_content}
            </div>
        </details>'''
    else:
        # Single bird - full expanded view
        return f'''
        <div style="padding:20px;background:white;border-radius:16px;margin:12px 0;border:1px solid #e2e8f0;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
            {header_html}
            {details_content}
        </div>'''


# ============ HYBRID LLM VALIDATION ============
def hybrid_llm_validation(birdnet_candidates: List[Dict], audio_features: Dict, 
                          location: str = "", month: str = "") -> List[Dict]:
    """
    LLM validation layer - enhances BirdNET results with reasoning.
    BirdNET is the gold standard for audio. LLM ENHANCES, not overrides.
    """
    if not birdnet_candidates:
        return []
    
    validated = []
    needs_validation = []
    
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
            # High confidence - trust BirdNET
            validated.append(bird_entry)
        else:
            needs_validation.append(candidate)
    
    # For high confidence, optionally add LLM context
    if validated and not needs_validation:
        top_bird = validated[0]
        try:
            prompt = f"""The bird "{top_bird['name']}" was identified by BirdNET with {top_bird['confidence']}% confidence.
Audio: {audio_features['min_freq']}-{audio_features['max_freq']}Hz, {audio_features['pattern']} pattern.
In 1-2 sentences, explain why this makes sense. Just the explanation."""
            
            reason = provider_factory.call_text(prompt)
            if reason and len(reason) < 300:
                top_bird['reason'] = f"BirdNET ({top_bird['confidence']}%): {reason.strip()}"
        except:
            pass
        return validated
    
    # For lower confidence, ask LLM to validate
    if needs_validation:
        candidates_text = "\n".join([
            f"- {c['name']} ({c.get('scientific', '')}): {c.get('confidence', 0)}%"
            for c in needs_validation
        ])
        
        prompt = f"""BirdNET detected these candidates (lower confidence):
{candidates_text}

Audio: {audio_features['min_freq']}-{audio_features['max_freq']}Hz, {audio_features['pattern']} pattern
Location: {location or 'Unknown'}, Season: {month or 'Unknown'}

Which is most likely? Respond with JSON: {{"birds": [{{"name": "...", "scientific_name": "...", "confidence": 60, "reason": "..."}}]}}"""
        
        response = provider_factory.call_text(prompt)
        llm_validated = parse_birds(response)
        
        if llm_validated:
            for bird in llm_validated:
                bird['source'] = 'BirdNET+LLM'
                validated.append(bird)
        else:
            # Fallback to BirdNET as-is
            for candidate in needs_validation:
                validated.append({
                    "name": candidate['name'],
                    "scientific_name": candidate.get('scientific', ''),
                    "confidence": candidate.get('confidence', 50),
                    "reason": f"BirdNET detection ({candidate.get('confidence', 50)}%)",
                    "source": "BirdNET"
                })
    
    return validated


# ============ MULTI-SOURCE AUDIO MERGE ============
def _merge_audio_candidates(candidates: List[Dict]) -> List[Dict]:
    """
    Merge audio candidates from multiple sources with weighted scoring.
    
    Weights:
    - BirdNET: 45% (spectrogram pattern matching)
    - Spectrogram+Vision: 30% (visual pattern analysis)
    - LLM-Enhanced: 25% (contextual reasoning)
    """
    if not candidates:
        return []
    
    # Source weights
    SOURCE_WEIGHTS = {
        "BirdNET": 0.45,
        "Spectrogram+Vision": 0.30,
        "LLM-Enhanced": 0.25,
        "BirdNET+LLM": 0.40,
    }
    
    # Group by bird name (case-insensitive)
    bird_scores = {}
    
    for c in candidates:
        name = c.get("name", "").lower().strip()
        if not name:
            continue
        
        source = c.get("source", "Unknown")
        # Extract base source (e.g., "BirdNET (high band)" -> "BirdNET")
        base_source = source.split("(")[0].strip() if "(" in source else source
        weight = SOURCE_WEIGHTS.get(base_source, 0.20)
        
        confidence = c.get("confidence", 50)
        weighted_score = weight * confidence
        
        if name not in bird_scores:
            bird_scores[name] = {
                "name": c.get("name"),
                "scientific_name": c.get("scientific_name", c.get("scientific", "")),
                "score": 0,
                "sources": [],
                "reasons": [],
                "count": 0
            }
        
        bird_scores[name]["score"] += weighted_score
        bird_scores[name]["sources"].append(source)
        bird_scores[name]["count"] += 1
        if c.get("reason"):
            bird_scores[name]["reasons"].append(c["reason"])
    
    # Sort by score (higher is better)
    sorted_birds = sorted(bird_scores.values(), key=lambda x: x["score"], reverse=True)
    
    # Normalize to confidence percentages
    if not sorted_birds:
        return []
    
    max_score = sorted_birds[0]["score"]
    
    results = []
    for bird in sorted_birds[:5]:  # Top 5
        # Boost if multiple sources agree
        multi_source_boost = min(1.2, 1 + (bird["count"] - 1) * 0.1)
        
        confidence = min(95, int((bird["score"] / max_score) * 100 * multi_source_boost))
        
        unique_sources = list(set(bird["sources"]))
        source_str = " + ".join(unique_sources[:3])
        
        results.append({
            "name": bird["name"],
            "scientific_name": bird["scientific_name"],
            "confidence": confidence,
            "reason": bird["reasons"][0] if bird["reasons"] else f"Identified by: {source_str}",
            "source": source_str
        })
    
    return results


# ============ STREAMING IDENTIFICATION FUNCTIONS ============

def identify_audio_streaming(audio_input, location: str = "", month: str = "") -> Generator[str, None, None]:
    """
    BirdSense Hybrid Audio Identification - ENHANCED VERSION
    Pipeline: META SAM-Audio → BirdNET → Spectrogram+Vision → LLM Validation
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
    
    # Convert to mono and normalize
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    audio_data = audio_data.astype(np.float64)
    if np.max(np.abs(audio_data)) > 0:
        audio_data = audio_data / np.max(np.abs(audio_data))
    
    # Get model info
    model_info = provider_factory.get_model_info("text")
    vision_info = provider_factory.get_model_info("vision")
    trail = []
    all_candidates = []  # Collect from all methods
    
    def update_trail(step: str, status: str = "⏳") -> str:
        trail_html = "".join([f"<div style='padding:4px 0;color:#64748b'>{t}</div>" for t in trail])
        model_badge = f"<div style='font-size:0.8em;color:#3b82f6;margin-bottom:8px'>🤖 {model_info['name']} | 🖼️ {vision_info['name']}</div>"
        return f"""<div style='padding:16px;background:#dbeafe;border-radius:8px'>
            <h3>🧠 BirdSense Enhanced Audio Analysis</h3>
            {model_badge}
            {trail_html}
            <div style='padding:4px 0;font-weight:bold'>{status} {step}</div>
        </div>"""
    
    # Stage 1: SAM-Audio Enhancement (CRITICAL - must run before BirdNET!)
    trail.append("✅ Audio loaded")
    yield update_trail("Stage 1/5: META SAM-Audio enhancement...")
    
    sam = SAMAudio()
    
    # 🔊 ENHANCE AUDIO FIRST - This is critical for accuracy!
    enhanced_audio = sam.enhance_audio(audio_data, sr)
    trail.append("✅ SAM-Audio: Noise reduction + Bird freq amplification")
    
    # Detect bird segments in enhanced audio
    segments = sam.detect_bird_segments(enhanced_audio, sr)
    
    # Separate into frequency bands from enhanced audio
    separated_bands = sam.separate_multiple_birds(enhanced_audio, sr)
    trail.append(f"✅ SAM-Audio: {len(segments)} segment(s), {len(separated_bands)} frequency band(s)")
    
    # Stage 2: BirdNET - Run on ENHANCED audio AND each frequency band
    yield update_trail("Stage 2/5: BirdNET multi-bird analysis...")
    
    birdnet_results = []
    if BIRDNET_AVAILABLE:
        # First, analyze the ENHANCED audio (not original!)
        full_results = identify_with_birdnet(enhanced_audio, sr, location, month)
        if full_results:
            for r in full_results:
                r["source"] = "BirdNET (enhanced)"
            birdnet_results.extend(full_results)
            trail.append(f"✅ BirdNET (enhanced): {len(full_results)} species")
        
        # Then analyze each separated frequency band for additional birds
        for band in separated_bands[:3]:  # Top 3 energy bands
            band_audio = band.get("audio")
            if band_audio is not None and len(band_audio) > 0:
                band_results = identify_with_birdnet(band_audio, sr, location, month)
                # Only add NEW species not already found
                for br in band_results:
                    br_name = br.get("name", "").lower()
                    existing_names = [r.get("name", "").lower() for r in birdnet_results]
                    if br_name and br_name not in existing_names:
                        br["source"] = f"BirdNET ({band['band']})"
                        birdnet_results.append(br)
        
        if birdnet_results:
            all_candidates.extend(birdnet_results)
            trail.append(f"✅ BirdNET total: {len(birdnet_results)} candidate(s)")
        else:
            trail.append("⚠️ BirdNET: No matches")
    else:
        trail.append("⚠️ BirdNET: Not available")
    
    # Stage 3: Spectrogram + Vision Model
    # Skip on cloud if BirdNET found enough candidates (optimization for speed)
    import os
    skip_spectrogram = os.environ.get("SKIP_SPECTROGRAM", "false").lower() == "true"
    has_enough_birdnet = len(all_candidates) >= 3  # BirdNET found multiple candidates
    
    spectrogram_results = []
    if skip_spectrogram or has_enough_birdnet:
        trail.append(f"⏩ Spectrogram: Skipped (BirdNET found {len(all_candidates)} candidates)")
    else:
        yield update_trail("Stage 3/5: Spectrogram vision analysis...")
        try:
            from audio_vision import SpectrogramAnalyzer
            import concurrent.futures
            
            spec_analyzer = SpectrogramAnalyzer()
            # Use ENHANCED audio for spectrogram (cleaner visualization)
            spec_image = spec_analyzer.generate_spectrogram(enhanced_audio, sr)
            
            # Use vision model to analyze spectrogram with timeout
            spec_prompt = """Analyze this bird call spectrogram. Identify the bird species based on:
- Frequency range (Y-axis)
- Temporal pattern (X-axis) 
- Harmonics and call shape

Common India patterns: Rising whistle=Koel, Two-note=Cuckoo, Rapid trill=Bee-eater, Complex song=Magpie-Robin

Respond in JSON: {{"birds": [{{"name": "...", "scientific_name": "...", "confidence": 75, "reason": "..."}}]}}"""
            
            # Run with 15 second timeout
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(provider_factory.call_vision, spec_image, spec_prompt)
                try:
                    spec_response = future.result(timeout=15)
                    spectrogram_results = parse_birds(spec_response)
                except concurrent.futures.TimeoutError:
                    trail.append("⚠️ Spectrogram: Timeout (>15s)")
                    spectrogram_results = []
            
            if spectrogram_results:
                for r in spectrogram_results:
                    r["source"] = "Spectrogram+Vision"
                    # Only add if not already found
                    if r["name"].lower() not in [c.get("name", "").lower() for c in all_candidates]:
                        all_candidates.append(r)
                trail.append(f"✅ Spectrogram: {len(spectrogram_results)} candidate(s)")
            elif not any("Timeout" in t for t in trail):
                trail.append("⚠️ Spectrogram: No visual match")
        except Exception as e:
            trail.append(f"⚠️ Spectrogram: Skipped ({str(e)[:30]})")
    
    # Stage 4: Features (from ENHANCED audio)
    yield update_trail("Stage 4/5: Acoustic feature extraction...")
    features = extract_audio_features(enhanced_audio, sr)
    trail.append(f"✅ Features (enhanced): {features['min_freq']}-{features['max_freq']}Hz, Peak: {features['peak_freq']}Hz")
    
    features_html = f"""<div style='padding:12px;background:#f1f5f9;border-radius:8px;margin:8px 0'>
        <b>🎵 Acoustic Features:</b><br>
        • Frequency: {features['min_freq']}-{features['max_freq']} Hz (Peak: {features['peak_freq']} Hz)<br>
        • Pattern: {features['pattern']} | Complexity: {features['complexity']}<br>
        • Syllables: {features['syllables']} | Rhythm: {features['rhythm']}
    </div>"""
    
    # Stage 5: LLM Validation + Enhanced Prompt
    yield update_trail("Stage 5/5: LLM validation with enhanced reasoning...")
    
    # Use enhanced audio prompt with all candidates as hints
    candidate_names = [c.get("name", "") for c in all_candidates[:5]]
    
    prompt_template = get_audio_prompt(provider_factory.active_provider or "ollama", enhanced=True)
    prompt = prompt_template.format(
        min_freq=features['min_freq'], max_freq=features['max_freq'],
        peak_freq=features['peak_freq'], freq_range=features['freq_range'],
        pattern=features['pattern'], complexity=features['complexity'],
        syllables=features['syllables'], rhythm=features['rhythm'],
        duration=features['duration'], quality=features.get('quality', 'Good'),
        location_info=f"- Location: {location}" if location else "- Location: India",
        season_info=f"- Season: {month}" if month else ""
    )
    
    # Add candidate hints if available
    if candidate_names:
        hint_text = ", ".join([n for n in candidate_names if n])
        prompt += f"\n\n## 🎯 DETECTION HINTS (from BirdNET/Spectrogram):\nPossible species: {hint_text}\nValidate or correct based on acoustic features."
    
    response = provider_factory.call_text(prompt)
    llm_birds = parse_birds(response)
    
    if llm_birds:
        for r in llm_birds:
            r["source"] = "LLM-Enhanced"
            # Add if new OR if higher confidence
            existing = [c for c in all_candidates if c.get("name", "").lower() == r["name"].lower()]
            if not existing:
                all_candidates.append(r)
            elif r.get("confidence", 0) > existing[0].get("confidence", 0):
                all_candidates.remove(existing[0])
                all_candidates.append(r)
        trail.append(f"✅ LLM validated: {len(llm_birds)} species")
    
    # Also validate BirdNET results if they exist
    if BIRDNET_AVAILABLE and birdnet_results and not llm_birds:
        trail.append("✅ Using BirdNET as primary source")
    
    # Merge all candidates with weighted scoring
    all_birds = _merge_audio_candidates(all_candidates)
    
    # Apply acoustic-based corrections (e.g., Magpie vs Magpie-Robin)
    if ENHANCED_CORRECTIONS_AVAILABLE and features:
        trail.append("🔄 Applying acoustic corrections...")
        all_birds = apply_acoustic_correction(all_birds, features)
        
    # Filter out non-Indian species if location is India
    if ENHANCED_CORRECTIONS_AVAILABLE and location and "india" in location.lower():
        trail.append("🌏 Filtering for Indian region...")
        all_birds = filter_non_indian_birds(all_birds, location)
    
    # Final results
    all_birds = deduplicate_birds(all_birds)
    
    if all_birds:
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
        
        total = len(all_birds)
        for i, bird in enumerate(all_birds, 1):
            result_html += format_bird_result(bird, i, include_enrichment=True, location=location, total_birds=total)
            yield result_html
            time.sleep(0.3)
    else:
        yield f"""<div style='padding:16px;background:#fef2f2;border-radius:8px'>
            <h3>❌ No Birds Identified</h3>
            {features_html}
            <p style='color:#64748b'>Try a clearer recording.</p>
        </div>"""


def identify_image_streaming(image, location: str = "") -> Generator[str, None, None]:
    """
    BirdSense Image Identification - ENHANCED VERSION
    Pipeline: Field Marks Analysis → Initial ID → Verification Pass → Regional Filter
    """
    if image is None:
        yield "<p style='color:#dc2626'>⚠️ Please upload an image</p>"
        return
    
    if not isinstance(image, Image.Image):
        image = Image.fromarray(np.array(image))
    image = image.convert("RGB")
    
    model_info = provider_factory.get_model_info("vision")
    trail = ["✅ Image loaded"]
    if location:
        trail.append(f"📍 Location: {location}")
    
    def update_trail(step: str, stage: int = 1, total: int = 3) -> str:
        trail_html = "".join([f"<div style='padding:2px 0;color:#64748b;font-size:0.9em'>{t}</div>" for t in trail])
        model_badge = f"<div style='font-size:0.8em;color:#3b82f6;margin-bottom:8px'>🤖 {model_info['name']} ({model_info['provider']})</div>"
        progress = int((stage / total) * 100)
        return f"""<div style='padding:16px;background:#dbeafe;border-radius:8px'>
            <h3>🔍 BirdSense Enhanced Image Analysis</h3>
            {model_badge}
            <div style='height:6px;background:#e2e8f0;border-radius:3px;margin:8px 0;overflow:hidden'>
                <div style='height:100%;width:{progress}%;background:linear-gradient(to right,#3b82f6,#8b5cf6);transition:width 0.3s'></div>
            </div>
            {trail_html}
            <div style='padding:4px 0;font-weight:bold'>⏳ {step}</div>
        </div>"""
    
    # Stage 1: Primary identification with enhanced prompt
    yield update_trail(f"Stage 1/3: Field marks analysis...", 1, 3)
    
    prompt = get_image_prompt(provider_factory.active_provider or "ollama", enhanced=True)
    response = provider_factory.call_vision(image, prompt)
    
    if not response:
        yield f"<p style='color:#dc2626'>❌ Vision model not responding. Check provider connection.</p>"
        return
    
    trail.append(f"✅ {model_info['name']} complete")
    
    primary_birds = parse_birds(response)
    
    if not primary_birds:
        yield f"""<div style='padding:16px;background:#fef2f2;border-radius:8px'>
            <h3>❌ Could not identify birds</h3>
            <details><summary>Raw response</summary>
            <pre style='background:#f1f5f9;padding:8px;border-radius:4px;font-size:0.8em'>{response[:500]}</pre>
            </details>
        </div>"""
        return
    
    trail.append(f"✅ Pass 1: {len(primary_birds)} candidate(s)")
    
    # Stage 2: Verification pass - Check for similar species
    yield update_trail("Stage 2/3: Similar species verification...", 2, 3)
    
    # Check if any candidates might be confused with similar species
    verified_birds = primary_birds.copy()
    
    # Import confusion prompts for similar species check
    try:
        from enhanced_prompts import get_confusion_prompt, CONFUSION_SPECIES_MATRIX
        
        candidate_names = [b.get("name", "") for b in primary_birds[:3]]
        confusion_prompt = get_confusion_prompt(candidate_names)
        
        if confusion_prompt:
            # There's a potential confusion - verify
            verify_prompt = f"""Look at the image again carefully.

{confusion_prompt}

Based on the EXACT features visible in this image, confirm or correct the identification.

Respond in JSON: {{"birds": [{{"name": "...", "scientific_name": "...", "confidence": 85, "reason": "VISIBLE features that confirm this ID: [list specific features]"}}]}}"""
            
            verify_response = provider_factory.call_vision(image, verify_prompt)
            verified = parse_birds(verify_response)
            
            if verified and verified[0].get("confidence", 0) > 70:
                # Use verified result if confident
                trail.append(f"✅ Similar species verified: {verified[0].get('name')}")
                verified_birds = verified
            else:
                trail.append("✅ Primary ID confirmed")
        else:
            trail.append("✅ No similar species confusion")
    except Exception as e:
        trail.append(f"⚠️ Verification skipped")
    
    # Stage 3: Regional context (if location provided)
    yield update_trail("Stage 3/3: Finalizing results...", 3, 3)
    
    if location:
        try:
            from ebird_integration import get_fallback_expected_species
            expected = get_fallback_expected_species(location, 1)
            
            # Boost confidence if bird is expected in region
            for bird in verified_birds:
                bird_name = bird.get("name", "").lower()
                if any(exp.lower() in bird_name or bird_name in exp.lower() for exp in expected):
                    bird["confidence"] = min(95, bird.get("confidence", 70) + 10)
                    bird["reason"] = f"{bird.get('reason', '')} [Common in {location}]"
                    
            trail.append(f"✅ Regional context applied")
        except:
            pass
    
    birds = deduplicate_birds(verified_birds)
    trail.append(f"✅ Final: {len(birds)} species identified")
    
    trail_html = "".join([f"<div style='padding:2px 0;color:#64748b;font-size:0.9em'>{t}</div>" for t in trail])
    result = f"""<div style='padding:16px;background:#dcfce7;border-radius:8px;margin-bottom:16px'>
        <h3>✅ BirdSense Results</h3>
        <p>Identified <b>{len(birds)}</b> species</p>
        <details><summary style='cursor:pointer;color:#059669'>View analysis trail</summary>
        <div style='padding:8px;background:#f0fdf4;border-radius:4px;margin-top:8px'>{trail_html}</div>
        </details>
    </div>"""
    
    total = len(birds)
    for i, bird in enumerate(birds, 1):
        result += format_bird_result(bird, i, include_enrichment=True, location=location, total_birds=total)
        yield result
        time.sleep(0.3)


def identify_description(description: str, location: str = "") -> Generator[str, None, None]:
    """BirdSense Description Identification."""
    if not description or len(description) < 5:
        yield "<p style='color:#dc2626'>⚠️ Please enter a description</p>"
        return
    
    model_info = provider_factory.get_model_info("text")
    trail = ["✅ Description received"]
    
    def update_trail(step: str) -> str:
        trail_html = "".join([f"<div style='padding:2px 0;color:#64748b;font-size:0.9em'>{t}</div>" for t in trail])
        model_badge = f"<div style='font-size:0.8em;color:#3b82f6;margin-bottom:8px'>🤖 {model_info['name']} ({model_info['provider']})</div>"
        return f"""<div style='padding:16px;background:#dbeafe;border-radius:8px'>
            <h3>📝 BirdSense Description Analysis</h3>
            {model_badge}
            {trail_html}
            <div style='padding:4px 0;font-weight:bold'>⏳ {step}</div>
        </div>"""
    
    yield update_trail(f"Analyzing with {model_info['name']}...")
    
    prompt_template = get_description_prompt(provider_factory.active_provider or "ollama")
    prompt = prompt_template.format(description=description)
    
    response = provider_factory.call_text(prompt)
    trail.append(f"✅ {model_info['name']} complete")
    
    birds = parse_birds(response)
    
    if not birds:
        yield f"""<div style='padding:16px;background:#fef2f2;border-radius:8px'>
            <h3>❌ Could not identify bird</h3>
            <p>Try more details about colors, size, behavior.</p>
        </div>"""
        return
    
    birds = deduplicate_birds(birds)
    trail.append(f"✅ Matched {len(birds)} species")
    
    trail_html = "".join([f"<div style='padding:2px 0;color:#64748b;font-size:0.9em'>{t}</div>" for t in trail])
    result = f"""<div style='padding:16px;background:#dcfce7;border-radius:8px;margin-bottom:16px'>
        <h3>✅ BirdSense Results</h3>
        <p>Matched <b>{len(birds)}</b> species</p>
        <details><summary style='cursor:pointer;color:#059669'>View trail</summary>
        <div style='padding:8px;background:#f0fdf4;border-radius:4px;margin-top:8px'>{trail_html}</div>
        </details>
    </div>"""
    
    total = len(birds)
    for i, bird in enumerate(birds, 1):
        result += format_bird_result(bird, i, include_enrichment=True, location=location, total_birds=total)
        yield result
        time.sleep(0.3)

