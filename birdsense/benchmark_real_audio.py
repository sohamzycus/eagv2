"""
🐦 BirdSense Real Audio Benchmark
Developed by Soham

Benchmarks BirdSense accuracy against real field recordings.
Audio files named: Scientific_name_Common Name.mp3
"""

import os
import re
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

# Audio loading
import soundfile as sf
from pydub import AudioSegment
import io

# BirdSense modules
from analysis import (
    identify_with_birdnet,
    extract_audio_features,
    hybrid_llm_validation,
    parse_birds,
    deduplicate_birds,
    SAMAudio,
    BIRDNET_AVAILABLE
)
from providers import provider_factory
from prompts import get_audio_prompt


# ============ CONFIG ============

AUDIO_FOLDER = "/Users/soham.niyogi/Downloads/Bird_audio"
OUTPUT_DIR = "/Users/soham.niyogi/Soham/codebase/eagv2/birdsense/benchmark_results"
LOCATION = "India"  # Default location context


# ============ AUDIO LOADING ============

def load_audio(filepath: str) -> Tuple[Optional[np.ndarray], int]:
    """Load audio file with multiple fallback methods."""
    sr = 44100
    audio_data = None
    
    ext = filepath.lower().split('.')[-1]
    
    # Method 1: pydub for m4a/mp3
    if ext in ['m4a', 'mp3', 'aac', 'mp4']:
        try:
            audio_segment = AudioSegment.from_file(filepath)
            sr = audio_segment.frame_rate
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)
            samples = np.array(audio_segment.get_array_of_samples())
            audio_data = samples.astype(np.float64) / 32768.0
        except Exception as e:
            print(f"  pydub failed: {e}")
    
    # Method 2: soundfile for wav/flac
    if audio_data is None:
        try:
            audio_data, sr = sf.read(filepath)
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
        except Exception as e:
            print(f"  soundfile failed: {e}")
    
    # Normalize
    if audio_data is not None:
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
    
    return audio_data, sr


def parse_filename(filename: str) -> Tuple[str, str, List[str]]:
    """
    Parse filename to extract expected bird(s).
    Returns: (scientific_name, common_name, [all_expected_names])
    
    Filename patterns:
    - Scientific_name_Common Name.mp3
    - Scientific_name_Common Name_2.m4a
    - bird1, bird2.m4a (multiple)
    """
    # Remove extension
    name = Path(filename).stem
    
    # Remove trailing _2, _3 etc
    name = re.sub(r'_\d+$', '', name)
    
    # Remove location coordinates
    name = re.sub(r'_\d+-\d+-[\d.]+-[NS]_\d+-\d+-[\d.]+-[EW]', '', name)
    
    expected_names = []
    
    # Check for multiple birds (comma separated)
    if ',' in name:
        parts = [p.strip() for p in name.split(',')]
        for p in parts:
            expected_names.append(p.lower())
        return "", "", expected_names
    
    # Standard format: Scientific_name_Common Name
    parts = name.split('_')
    if len(parts) >= 2:
        # Try to find scientific name (two words with capital letters)
        scientific = ""
        common = ""
        
        # First two parts usually scientific name
        if len(parts) >= 2:
            scientific = f"{parts[0]} {parts[1]}"
            common = ' '.join(parts[2:]) if len(parts) > 2 else parts[1]
        
        expected_names = [
            common.lower(),
            scientific.lower(),
            parts[-1].lower() if parts else ""  # Just last word
        ]
        
        return scientific, common, [n for n in expected_names if n]
    
    return "", name, [name.lower()]


def check_match(predicted: str, expected_names: List[str]) -> bool:
    """Check if prediction matches any expected name, with special handling for confusing names."""
    predicted_lower = predicted.lower().strip()
    
    for expected in expected_names:
        expected_lower = expected.lower().strip()
        
        # Remove numbers from expected (e.g., "magpie1" → "magpie")
        import re
        expected_clean = re.sub(r'[0-9]+$', '', expected_lower).strip()
        
        # SPECIAL CASE: "magpie" (without "robin") should NOT match "Oriental Magpie-Robin"
        # because they are completely different species!
        if expected_clean == "magpie":
            # Only accept actual Magpie species (Eurasian, Common, Black-billed)
            valid_magpie_matches = [
                "eurasian magpie", "common magpie", "black-billed magpie",
                "pica pica", "magpie"
            ]
            # REJECT Oriental Magpie-Robin (it's NOT a Magpie)
            if "robin" in predicted_lower or "oriental" in predicted_lower:
                continue  # Not a match
            for valid in valid_magpie_matches:
                if valid in predicted_lower or predicted_lower in valid:
                    return True
            continue  # Check next expected name
        
        # SPECIAL CASE: "bee eater" should match Green/Blue-tailed/etc Bee-eater
        if "bee" in expected_clean and "eater" in expected_clean:
            if "bee-eater" in predicted_lower or "bee eater" in predicted_lower:
                return True
        
        # Exact match
        if predicted_lower == expected_lower or predicted_lower == expected_clean:
            return True
        
        # Partial match (one contains the other)
        if expected_clean in predicted_lower or predicted_lower in expected_clean:
            return True
        
        # Word overlap (at least 1 significant word matches)
        pred_words = set(predicted_lower.replace("-", " ").split())
        exp_words = set(expected_clean.replace("-", " ").split())
        # Remove common words
        common_words = {"the", "a", "an", "bird", "sp", "sp.", "phone"}
        pred_words -= common_words
        exp_words -= common_words
        if len(pred_words & exp_words) >= 1:
            return True
    
    return False


# ============ BENCHMARK ============

def run_audio_benchmark(max_files: int = None, audio_folder: str = None) -> Dict:
    """
    Run benchmark on real audio files.
    
    Returns dict with:
    - results: list of individual test results
    - summary: accuracy metrics
    """
    folder = audio_folder or AUDIO_FOLDER
    
    print("🐦 BirdSense Real Audio Benchmark")
    print("=" * 60)
    print(f"Audio folder: {folder}")
    print(f"BirdNET available: {BIRDNET_AVAILABLE}")
    print(f"LLM backend: {provider_factory.active_provider}")
    print("=" * 60)
    
    # Get audio files
    audio_files = []
    for f in os.listdir(folder):
        if f.lower().endswith(('.mp3', '.m4a', '.wav', '.aac', '.flac')):
            audio_files.append(f)
    
    if max_files:
        audio_files = audio_files[:max_files]
    
    print(f"\n📁 Found {len(audio_files)} audio files\n")
    
    results = []
    correct = 0
    total = 0
    
    sam = SAMAudio()
    
    for i, filename in enumerate(audio_files):
        filepath = os.path.join(folder, filename)
        scientific, common, expected_names = parse_filename(filename)
        
        print(f"\n[{i+1}/{len(audio_files)}] {filename}")
        print(f"  Expected: {common or expected_names}")
        
        # Load audio
        audio_data, sr = load_audio(filepath)
        if audio_data is None:
            print(f"  ❌ Failed to load audio")
            results.append({
                "file": filename,
                "expected_scientific": scientific,
                "expected_common": common,
                "expected_names": expected_names,
                "status": "load_error",
                "predictions": [],
                "correct": False
            })
            continue
        
        print(f"  Audio: {len(audio_data)/sr:.1f}s @ {sr}Hz")
        
        # Run identification pipeline
        start_time = time.time()
        all_birds = []
        
        try:
            # 1. SAM-Audio enhancement
            enhanced_audio = sam.enhance_audio(audio_data, sr)
            
            # 2. BirdNET analysis
            if BIRDNET_AVAILABLE:
                birdnet_results = identify_with_birdnet(enhanced_audio, sr, LOCATION, "")
                if birdnet_results:
                    all_birds.extend(birdnet_results)
                    print(f"  BirdNET: {len(birdnet_results)} species")
            
            # 3. Multi-band analysis
            separated = sam.separate_multiple_birds(enhanced_audio, sr)
            for band in separated[:3]:
                band_audio = band.get("audio")
                if band_audio is not None and BIRDNET_AVAILABLE:
                    band_results = identify_with_birdnet(band_audio, sr, LOCATION, "")
                    for br in band_results:
                        if br.get("name", "").lower() not in [b.get("name", "").lower() for b in all_birds]:
                            br["source"] = f"BirdNET ({band['band']})"
                            all_birds.append(br)
            
            # 4. Feature extraction
            features = extract_audio_features(enhanced_audio, sr)
            
            # 5. LLM validation (if we have candidates)
            if all_birds:
                validated = hybrid_llm_validation(all_birds, features, LOCATION, "")
                if validated:
                    all_birds = validated
            else:
                # Fallback to LLM-only
                prompt = get_audio_prompt(provider_factory.active_provider or "ollama", enhanced=True).format(
                    min_freq=features['min_freq'], max_freq=features['max_freq'],
                    peak_freq=features['peak_freq'], freq_range=features['freq_range'],
                    pattern=features['pattern'], complexity=features['complexity'],
                    syllables=features['syllables'], rhythm=features['rhythm'],
                    duration=features['duration'], quality=features.get('quality', 'Good'),
                    location_info=f"- Location: {LOCATION}",
                    season_info=""
                )
                response = provider_factory.call_text(prompt)
                llm_birds = parse_birds(response)
                if llm_birds:
                    all_birds = llm_birds
            
            # Apply acoustic corrections (Magpie vs Magpie-Robin, etc.)
            try:
                from enhanced_prompts import apply_acoustic_correction, filter_non_indian_birds
                all_birds = apply_acoustic_correction(all_birds, features)
                all_birds = filter_non_indian_birds(all_birds, LOCATION)
            except ImportError:
                pass
            
            # Deduplicate
            all_birds = deduplicate_birds(all_birds)
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                "file": filename,
                "expected_scientific": scientific,
                "expected_common": common,
                "expected_names": expected_names,
                "status": "error",
                "error": str(e),
                "predictions": [],
                "correct": False
            })
            continue
        
        elapsed = time.time() - start_time
        
        # Check if correct
        predictions = [b.get("name", "") for b in all_birds[:3]]
        is_correct = any(check_match(p, expected_names) for p in predictions)
        
        if is_correct:
            correct += 1
            print(f"  ✅ Correct: {predictions[:2]}")
        else:
            print(f"  ❌ Wrong: {predictions[:2]} (expected {common or expected_names[0]})")
        
        total += 1
        
        results.append({
            "file": filename,
            "expected_scientific": scientific,
            "expected_common": common,
            "expected_names": expected_names,
            "status": "success",
            "predictions": [
                {
                    "name": b.get("name", ""),
                    "scientific_name": b.get("scientific_name", ""),
                    "confidence": b.get("confidence", 0),
                    "source": b.get("source", "")
                }
                for b in all_birds[:5]
            ],
            "correct": is_correct,
            "processing_time_ms": int(elapsed * 1000),
            "features": features
        })
        
        # Progress
        if total > 0:
            print(f"  Running accuracy: {correct}/{total} ({100*correct/total:.1f}%)")
    
    # Summary
    accuracy = 100 * correct / total if total > 0 else 0
    
    summary = {
        "total_files": len(audio_files),
        "tested": total,
        "correct": correct,
        "accuracy": round(accuracy, 2),
        "birdnet_available": BIRDNET_AVAILABLE,
        "llm_backend": provider_factory.active_provider,
        "timestamp": datetime.now().isoformat()
    }
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {correct}/{total} correct ({accuracy:.1f}% accuracy)")
    print("=" * 60)
    
    return {
        "summary": summary,
        "results": results
    }


def save_results(data: Dict, output_dir: str = OUTPUT_DIR, prefix: str = "benchmark"):
    """Save results to JSON and generate HTML report."""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON
    json_path = os.path.join(output_dir, f"{prefix}_{timestamp}.json")
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"\n📄 JSON saved: {json_path}")
    
    # Generate HTML report
    html_path = os.path.join(output_dir, f"{prefix}_{timestamp}.html")
    generate_html_report(data, html_path)
    print(f"📊 HTML report: {html_path}")
    
    return json_path, html_path


def generate_html_report(data: Dict, output_path: str):
    """Generate interactive HTML report."""
    summary = data["summary"]
    results = data["results"]
    
    # Calculate stats
    correct = [r for r in results if r.get("correct")]
    incorrect = [r for r in results if r.get("status") == "success" and not r.get("correct")]
    errors = [r for r in results if r.get("status") in ["error", "load_error"]]
    
    # Top confusions
    confusions = {}
    for r in incorrect:
        expected = r.get("expected_common") or (r.get("expected_names", [""])[0] if r.get("expected_names") else "")
        predicted = r.get("predictions", [{}])[0].get("name", "Unknown") if r.get("predictions") else "None"
        key = f"{expected} → {predicted}"
        confusions[key] = confusions.get(key, 0) + 1
    
    top_confusions = sorted(confusions.items(), key=lambda x: -x[1])[:10]
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐦 BirdSense Benchmark Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ text-align: center; margin-bottom: 30px; font-size: 2.5em; }}
        h1 span {{ color: #22c55e; }}
        
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .stat-card {{ background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 25px; border-radius: 16px; text-align: center; }}
        .stat-card.success {{ border: 2px solid #22c55e; }}
        .stat-card.warning {{ border: 2px solid #f59e0b; }}
        .stat-card.error {{ border: 2px solid #ef4444; }}
        .stat-value {{ font-size: 3em; font-weight: bold; }}
        .stat-value.green {{ color: #22c55e; }}
        .stat-value.yellow {{ color: #f59e0b; }}
        .stat-value.red {{ color: #ef4444; }}
        .stat-label {{ color: #94a3b8; margin-top: 5px; }}
        
        .section {{ background: #1e293b; border-radius: 16px; padding: 25px; margin-bottom: 30px; }}
        .section h2 {{ color: #60a5fa; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }}
        
        .confusion-list {{ list-style: none; }}
        .confusion-list li {{ padding: 12px; background: rgba(239, 68, 68, 0.1); margin-bottom: 8px; border-radius: 8px; display: flex; justify-content: space-between; }}
        .confusion-list .count {{ background: #ef4444; color: white; padding: 4px 12px; border-radius: 20px; }}
        
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background: #334155; color: #60a5fa; }}
        tr:hover {{ background: rgba(59, 130, 246, 0.1); }}
        .correct {{ color: #22c55e; }}
        .incorrect {{ color: #ef4444; }}
        .confidence {{ background: #334155; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; }}
        
        .filter-bar {{ display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }}
        .filter-btn {{ padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.2s; }}
        .filter-btn.all {{ background: #3b82f6; color: white; }}
        .filter-btn.correct {{ background: #22c55e; color: white; }}
        .filter-btn.incorrect {{ background: #ef4444; color: white; }}
        .filter-btn:hover {{ transform: translateY(-2px); }}
        
        .meta {{ color: #64748b; font-size: 0.9em; margin-top: 30px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🐦 BirdSense <span>Benchmark Report</span></h1>
        
        <div class="summary">
            <div class="stat-card success">
                <div class="stat-value green">{summary['accuracy']}%</div>
                <div class="stat-label">Accuracy</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['correct']}/{summary['tested']}</div>
                <div class="stat-label">Correct / Total</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['total_files']}</div>
                <div class="stat-label">Audio Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value yellow">{len(errors)}</div>
                <div class="stat-label">Errors</div>
            </div>
        </div>
        
        <div class="section">
            <h2>⚙️ Configuration</h2>
            <p><strong>BirdNET:</strong> {"✅ Available" if summary['birdnet_available'] else "❌ Not Available"}</p>
            <p><strong>LLM Backend:</strong> {summary['llm_backend'] or 'None'}</p>
            <p><strong>Timestamp:</strong> {summary['timestamp']}</p>
        </div>
        
        <div class="section">
            <h2>🔄 Top Confusions</h2>
            <ul class="confusion-list">
                {''.join(f'<li><span>{conf}</span><span class="count">{count}</span></li>' for conf, count in top_confusions) or '<li>No confusions found</li>'}
            </ul>
        </div>
        
        <div class="section">
            <h2>📋 Detailed Results</h2>
            <div class="filter-bar">
                <button class="filter-btn all" onclick="filterResults('all')">All ({len(results)})</button>
                <button class="filter-btn correct" onclick="filterResults('correct')">Correct ({len(correct)})</button>
                <button class="filter-btn incorrect" onclick="filterResults('incorrect')">Incorrect ({len(incorrect)})</button>
            </div>
            <table id="results-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Expected</th>
                        <th>Prediction</th>
                        <th>Confidence</th>
                        <th>Source</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for i, r in enumerate(results):
        expected = r.get("expected_common") or (r.get("expected_names", [""])[0] if r.get("expected_names") else "Unknown")
        prediction = r.get("predictions", [{}])[0].get("name", "-") if r.get("predictions") else "-"
        confidence = r.get("predictions", [{}])[0].get("confidence", 0) if r.get("predictions") else 0
        source = r.get("predictions", [{}])[0].get("source", "-") if r.get("predictions") else "-"
        is_correct = r.get("correct", False)
        status = r.get("status", "unknown")
        
        result_class = "correct" if is_correct else "incorrect"
        result_text = "✅" if is_correct else "❌" if status == "success" else "⚠️"
        
        html += f"""
                    <tr class="result-row {result_class}" data-status="{result_class}">
                        <td>{i+1}</td>
                        <td>{expected}</td>
                        <td>{prediction}</td>
                        <td><span class="confidence">{confidence}%</span></td>
                        <td>{source}</td>
                        <td class="{result_class}">{result_text}</td>
                    </tr>
"""
    
    html += f"""
                </tbody>
            </table>
        </div>
        
        <div class="meta">
            Generated by BirdSense Benchmark | Developed by Soham | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
    
    <script>
        function filterResults(type) {{
            const rows = document.querySelectorAll('.result-row');
            rows.forEach(row => {{
                if (type === 'all') {{
                    row.style.display = '';
                }} else {{
                    row.style.display = row.dataset.status === type ? '' : 'none';
                }}
            }});
        }}
    </script>
</body>
</html>
"""
    
    with open(output_path, 'w') as f:
        f.write(html)


# ============ MAIN ============

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark BirdSense audio identification")
    parser.add_argument("--folder", type=str, default=None, help="Path to audio folder")
    parser.add_argument("--max-files", type=int, default=None, help="Maximum files to process")
    parser.add_argument("--output-prefix", type=str, default="benchmark", help="Output file prefix")
    args = parser.parse_args()
    
    # Ensure cloud backend is active
    if provider_factory.active_provider != "cloud":
        print("⚠️ Switching to cloud LLM backend...")
        provider_factory.set_active("cloud")
    
    # Run benchmark
    results = run_audio_benchmark(max_files=args.max_files, audio_folder=args.folder)
    
    # Save results
    json_path, html_path = save_results(results, prefix=args.output_prefix)
    
    print(f"\n🎉 Benchmark complete!")
    print(f"   View report: file://{html_path}")

