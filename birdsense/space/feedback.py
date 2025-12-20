"""
🐦 BirdSense Feedback & Sample Collection
Developed by Soham

Collects:
1. User feedback on predictions (correct/incorrect)
2. Audio/Image samples with corrections
3. Usage analytics for model improvement
"""

import json
import os
import uuid
import hashlib
from datetime import datetime
from pathlib import Path

# ============ CONFIG ============
FEEDBACK_DIR = Path("feedback_data")
SAMPLES_DIR = FEEDBACK_DIR / "samples"
LOGS_DIR = FEEDBACK_DIR / "logs"

# Create directories
FEEDBACK_DIR.mkdir(exist_ok=True)
SAMPLES_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ============ FEEDBACK STORAGE ============

def generate_session_id():
    """Generate unique session ID."""
    return str(uuid.uuid4())[:8]


def log_prediction(
    input_type: str,  # "audio", "image", "description"
    prediction: dict,
    features: dict = None,
    session_id: str = None
) -> str:
    """
    Log a prediction for audit trail.
    Returns prediction_id for feedback reference.
    """
    prediction_id = str(uuid.uuid4())[:12]
    
    log_entry = {
        "prediction_id": prediction_id,
        "session_id": session_id or generate_session_id(),
        "timestamp": datetime.now().isoformat(),
        "input_type": input_type,
        "prediction": prediction,
        "features": features,
        "feedback": None,  # Will be updated when user provides feedback
        "correct_species": None
    }
    
    # Save to daily log file
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS_DIR / f"predictions_{date_str}.jsonl"
    
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    return prediction_id


def save_feedback(
    prediction_id: str,
    is_correct: bool,
    correct_species: str = None,
    user_notes: str = None
):
    """
    Save user feedback on a prediction.
    """
    feedback_entry = {
        "prediction_id": prediction_id,
        "timestamp": datetime.now().isoformat(),
        "is_correct": is_correct,
        "correct_species": correct_species,
        "user_notes": user_notes
    }
    
    # Save to feedback file
    feedback_file = FEEDBACK_DIR / "feedback.jsonl"
    with open(feedback_file, "a") as f:
        f.write(json.dumps(feedback_entry) + "\n")
    
    return True


def save_sample(
    input_type: str,
    data: bytes,
    species: str,
    source: str = "user_correction",
    metadata: dict = None
) -> str:
    """
    Save a sample (audio/image) for training data.
    """
    # Generate unique filename
    file_hash = hashlib.md5(data).hexdigest()[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    ext = ".wav" if input_type == "audio" else ".jpg"
    filename = f"{species.replace(' ', '_')}_{timestamp}_{file_hash}{ext}"
    
    # Save file
    sample_path = SAMPLES_DIR / input_type
    sample_path.mkdir(exist_ok=True)
    
    filepath = sample_path / filename
    with open(filepath, "wb") as f:
        f.write(data)
    
    # Save metadata
    meta = {
        "filename": filename,
        "species": species,
        "input_type": input_type,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    
    meta_file = SAMPLES_DIR / "samples_index.jsonl"
    with open(meta_file, "a") as f:
        f.write(json.dumps(meta) + "\n")
    
    return str(filepath)


# ============ ANALYTICS ============

def get_analytics():
    """Get usage analytics for dashboard."""
    stats = {
        "total_predictions": 0,
        "by_type": {"audio": 0, "image": 0, "description": 0},
        "feedback_received": 0,
        "accuracy_reported": 0,
        "samples_collected": 0,
        "top_species": {},
        "recent_feedback": []
    }
    
    # Count predictions
    for log_file in LOGS_DIR.glob("predictions_*.jsonl"):
        with open(log_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    stats["total_predictions"] += 1
                    stats["by_type"][entry.get("input_type", "unknown")] = \
                        stats["by_type"].get(entry.get("input_type", "unknown"), 0) + 1
                    
                    # Track species
                    pred = entry.get("prediction", {})
                    if isinstance(pred, list) and pred:
                        species = pred[0].get("name", "Unknown")
                    elif isinstance(pred, dict):
                        species = pred.get("name", "Unknown")
                    else:
                        species = "Unknown"
                    
                    stats["top_species"][species] = stats["top_species"].get(species, 0) + 1
                except:
                    pass
    
    # Count feedback
    feedback_file = FEEDBACK_DIR / "feedback.jsonl"
    if feedback_file.exists():
        correct_count = 0
        with open(feedback_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    stats["feedback_received"] += 1
                    if entry.get("is_correct"):
                        correct_count += 1
                    stats["recent_feedback"].append(entry)
                except:
                    pass
        
        if stats["feedback_received"] > 0:
            stats["accuracy_reported"] = round(correct_count / stats["feedback_received"] * 100, 1)
    
    # Keep only recent feedback
    stats["recent_feedback"] = stats["recent_feedback"][-10:]
    
    # Count samples
    samples_index = SAMPLES_DIR / "samples_index.jsonl"
    if samples_index.exists():
        with open(samples_index) as f:
            stats["samples_collected"] = sum(1 for _ in f)
    
    # Sort top species
    stats["top_species"] = dict(
        sorted(stats["top_species"].items(), key=lambda x: -x[1])[:10]
    )
    
    return stats


def format_analytics_html():
    """Format analytics as HTML for Gradio."""
    stats = get_analytics()
    
    top_species_html = "".join([
        f"<tr><td>{s}</td><td>{c}</td></tr>" 
        for s, c in list(stats["top_species"].items())[:5]
    ])
    
    return f"""
    <div style="padding: 20px; background: #f8fafc; border-radius: 12px;">
        <h2>📊 BirdSense Analytics Dashboard</h2>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0;">
            <div style="background: white; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 2em; font-weight: bold; color: #3b82f6;">{stats['total_predictions']}</div>
                <div style="color: #64748b;">Total Predictions</div>
            </div>
            <div style="background: white; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 2em; font-weight: bold; color: #22c55e;">{stats['feedback_received']}</div>
                <div style="color: #64748b;">Feedback Received</div>
            </div>
            <div style="background: white; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 2em; font-weight: bold; color: #f59e0b;">{stats['accuracy_reported']}%</div>
                <div style="color: #64748b;">Reported Accuracy</div>
            </div>
            <div style="background: white; padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 2em; font-weight: bold; color: #8b5cf6;">{stats['samples_collected']}</div>
                <div style="color: #64748b;">Samples Collected</div>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div style="background: white; padding: 16px; border-radius: 8px;">
                <h3>🐦 Top Identified Species</h3>
                <table style="width: 100%;">
                    <tr><th>Species</th><th>Count</th></tr>
                    {top_species_html}
                </table>
            </div>
            <div style="background: white; padding: 16px; border-radius: 8px;">
                <h3>📈 Usage by Type</h3>
                <div>🎵 Audio: {stats['by_type'].get('audio', 0)}</div>
                <div>📷 Image: {stats['by_type'].get('image', 0)}</div>
                <div>📝 Description: {stats['by_type'].get('description', 0)}</div>
            </div>
        </div>
    </div>
    """

