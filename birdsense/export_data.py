#!/usr/bin/env python3
"""
🐦 BirdSense - Export Collected Data
Developed by Soham

Exports feedback and samples for model improvement.

Usage:
    python export_data.py                    # Show summary
    python export_data.py --export feedback  # Export feedback JSON
    python export_data.py --export samples   # Package samples as ZIP
    python export_data.py --export all       # Export everything
"""

import argparse
import json
import zipfile
import os
from datetime import datetime
from pathlib import Path

from feedback import FEEDBACK_DIR, SAMPLES_DIR, LOGS_DIR, get_analytics


def show_summary():
    """Show summary of collected data."""
    stats = get_analytics()
    
    print("\n" + "=" * 60)
    print("🐦 BirdSense Data Summary")
    print("=" * 60)
    
    print(f"\n📊 Predictions: {stats['total_predictions']}")
    print(f"   🎵 Audio: {stats['by_type'].get('audio', 0)}")
    print(f"   📷 Image: {stats['by_type'].get('image', 0)}")
    print(f"   📝 Description: {stats['by_type'].get('description', 0)}")
    
    print(f"\n📝 Feedback Received: {stats['feedback_received']}")
    print(f"   Reported Accuracy: {stats['accuracy_reported']}%")
    
    print(f"\n📦 Samples Collected: {stats['samples_collected']}")
    
    if stats['top_species']:
        print("\n🐦 Top Species:")
        for species, count in list(stats['top_species'].items())[:5]:
            print(f"   {species}: {count}")
    
    print("\n" + "=" * 60)


def export_feedback():
    """Export all feedback data to JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"birdsense_feedback_{timestamp}.json"
    
    all_data = {
        "predictions": [],
        "feedback": [],
        "export_timestamp": datetime.now().isoformat()
    }
    
    # Collect predictions
    for log_file in LOGS_DIR.glob("predictions_*.jsonl"):
        with open(log_file) as f:
            for line in f:
                try:
                    all_data["predictions"].append(json.loads(line))
                except:
                    pass
    
    # Collect feedback
    feedback_file = FEEDBACK_DIR / "feedback.jsonl"
    if feedback_file.exists():
        with open(feedback_file) as f:
            for line in f:
                try:
                    all_data["feedback"].append(json.loads(line))
                except:
                    pass
    
    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)
    
    print(f"✅ Exported feedback to: {output_file}")
    print(f"   Predictions: {len(all_data['predictions'])}")
    print(f"   Feedback: {len(all_data['feedback'])}")
    
    return output_file


def export_samples():
    """Package all samples as ZIP for training."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"birdsense_samples_{timestamp}.zip"
    
    if not SAMPLES_DIR.exists():
        print("❌ No samples directory found")
        return None
    
    sample_count = 0
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add all sample files
        for root, dirs, files in os.walk(SAMPLES_DIR):
            for file in files:
                filepath = Path(root) / file
                arcname = filepath.relative_to(SAMPLES_DIR)
                zf.write(filepath, arcname)
                sample_count += 1
    
    if sample_count > 0:
        print(f"✅ Exported samples to: {output_file}")
        print(f"   Files: {sample_count}")
        return output_file
    else:
        os.remove(output_file)
        print("❌ No samples to export")
        return None


def export_all():
    """Export everything."""
    print("📦 Exporting all data...")
    
    feedback_file = export_feedback()
    samples_file = export_samples()
    
    print("\n" + "=" * 60)
    print("📤 Export Complete!")
    print("=" * 60)
    
    if feedback_file:
        print(f"📝 Feedback: {feedback_file}")
    if samples_file:
        print(f"📦 Samples: {samples_file}")
    
    print("\nThese files can be used to:")
    print("  • Analyze misclassification patterns")
    print("  • Fine-tune models with corrected labels")
    print("  • Improve prompts based on feedback")


def main():
    parser = argparse.ArgumentParser(description="Export BirdSense data")
    parser.add_argument("--export", choices=["feedback", "samples", "all"], 
                        help="What to export")
    args = parser.parse_args()
    
    if args.export == "feedback":
        export_feedback()
    elif args.export == "samples":
        export_samples()
    elif args.export == "all":
        export_all()
    else:
        show_summary()


if __name__ == "__main__":
    main()

