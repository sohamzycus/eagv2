"""
BirdSense Gradio App for HuggingFace Spaces
Zero-Shot LLM Bird Identification - 10,000+ Species

Deploy to HuggingFace Spaces:
1. Create Space at https://huggingface.co/spaces
2. Select Gradio SDK
3. Upload these files: app.py, requirements.txt, audio/, llm/, data/
4. Launch!
"""

import gradio as gr
import numpy as np
import torch
from pathlib import Path
import sys
import json

# Add current directory
sys.path.insert(0, str(Path(__file__).parent))

from audio.preprocessor import AudioPreprocessor
from data.species_db import IndiaSpeciesDatabase

# Import zero-shot identifier
try:
    from llm.zero_shot_identifier import ZeroShotBirdIdentifier, AudioFeatures
    HAS_ZERO_SHOT = True
except ImportError:
    HAS_ZERO_SHOT = False
    print("⚠️ Zero-shot identifier not available")

print("🐦 Loading BirdSense Zero-Shot Edition...")

# Initialize components
preprocessor = AudioPreprocessor()
species_db = IndiaSpeciesDatabase()

# Initialize zero-shot identifier
identifier = None
if HAS_ZERO_SHOT:
    try:
        identifier = ZeroShotBirdIdentifier()
        if identifier.initialize():
            print("✅ Zero-shot LLM identifier ready!")
        else:
            print("⚠️ LLM not available - using feature-based identification")
    except Exception as e:
        print(f"⚠️ Zero-shot setup failed: {e}")

print(f"✅ Ready! Can identify 10,000+ species")


def identify_bird(audio, location=None, month=None, description=None):
    """
    Identify bird from audio using zero-shot LLM.
    
    Args:
        audio: Tuple (sample_rate, audio_data) from Gradio
        location: Optional location string
        month: Optional month string
        description: Optional user description
    
    Returns:
        Formatted results for Gradio display
    """
    if audio is None:
        return (
            "Please upload or record audio",
            "N/A",
            "No audio provided",
            "",
            gr.update(visible=False)
        )
    
    sr, audio_data = audio
    
    # Convert to float32 and normalize
    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0
    elif audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float32) / 2147483648.0
    
    # Convert stereo to mono
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # Get audio quality
    quality = preprocessor.get_audio_quality_assessment(audio_data, sr)
    
    # Parse month
    month_num = None
    if month:
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        if month in months:
            month_num = months.index(month) + 1
    
    # Run identification
    if identifier:
        # Resample if needed
        import scipy.signal
        if sr != 32000:
            num_samples = int(len(audio_data) * 32000 / sr)
            audio_data = scipy.signal.resample(audio_data, num_samples)
            sr = 32000
        
        # Extract features
        features = identifier.extract_features(audio_data, sr)
        
        # Zero-shot identification
        result = identifier.identify(
            features=features,
            location=location,
            month=month_num,
            user_description=description
        )
        
        species_name = result.species_name
        scientific = result.scientific_name
        confidence = result.confidence * 100
        confidence_label = result.confidence_label
        reasoning = result.reasoning
        key_features = result.key_features_matched
        alternatives = result.alternative_species
        is_indian = result.is_indian_bird
        is_unusual = result.is_unusual_sighting
        unusual_reason = result.unusual_reason
    else:
        # Fallback
        species_name = "Unknown (LLM not available)"
        scientific = ""
        confidence = 0
        confidence_label = "low"
        reasoning = "Zero-shot LLM not available. Please install and run Ollama with qwen2.5:3b."
        key_features = []
        alternatives = []
        is_indian = True
        is_unusual = False
        unusual_reason = None
    
    # Format main result
    main_result = f"""
## 🎯 {species_name}
**Scientific Name:** _{scientific}_

**Confidence:** {confidence:.1f}% ({confidence_label.upper()})

**Audio Quality:** {quality['quality_label'].upper()} (score: {quality['quality_score']:.2f})
"""
    
    # Format confidence display
    if confidence >= 80:
        conf_color = "🟢"
    elif confidence >= 60:
        conf_color = "🟡"
    else:
        conf_color = "🔴"
    
    confidence_display = f"{conf_color} **{confidence:.1f}%** ({confidence_label.upper()})"
    
    # Format predictions
    predictions = f"### Top Match\n1. **{species_name}** ({confidence:.1f}%)\n"
    for i, alt in enumerate(alternatives[:3], 2):
        alt_conf = alt.get('confidence', 0.1) * 100
        predictions += f"{i}. {alt.get('name', 'Unknown')} ({alt_conf:.1f}%)\n"
    
    # Format reasoning
    reasoning_text = f"""
### 🤖 AI Analysis
{reasoning}

**Key Features Matched:**
{', '.join(key_features) if key_features else 'N/A'}

**Audio Features:**
- Duration: {features.duration:.1f}s
- Dominant Frequency: {features.dominant_frequency_hz:.0f} Hz
- Pattern: {'Melodic' if features.is_melodic else 'Simple'}, {'Repetitive' if features.is_repetitive else 'Varied'}
- Syllables: {features.num_syllables} at {features.syllable_rate:.1f}/sec
"""
    
    # Novelty alert
    novelty_visible = is_unusual or not is_indian
    novelty_text = ""
    if is_unusual:
        novelty_text = f"⚠️ **Unusual Sighting!** {unusual_reason or 'This is a rare observation!'}"
    elif not is_indian:
        novelty_text = f"🌍 **{species_name} is not typically found in India** - This is an exciting observation!"
    
    return (
        main_result,
        confidence_display,
        predictions,
        reasoning_text,
        gr.update(visible=novelty_visible, value=novelty_text)
    )


# Custom theme
theme = gr.themes.Soft(
    primary_hue="green",
    secondary_hue="cyan",
    neutral_hue="slate",
    font=["Outfit", "system-ui", "sans-serif"]
)

# Build Gradio interface
with gr.Blocks(theme=theme, title="🐦 BirdSense") as demo:
    
    gr.HTML("""
    <div style="text-align: center; background: linear-gradient(135deg, #1a2332, #243447); padding: 2rem; border-radius: 16px; margin-bottom: 1rem;">
        <h1 style="font-size: 2.5rem; margin: 0;">🐦 BirdSense</h1>
        <p style="color: #94a3b8; margin-top: 0.5rem;">Zero-Shot LLM Bird Identification</p>
        <p style="color: #64748b; font-size: 0.9rem;">10,000+ species • No training required • Works worldwide</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🎤 Audio Input")
            
            audio_input = gr.Audio(
                sources=["microphone", "upload"],
                type="numpy",
                label="Record or Upload Bird Audio",
            )
            
            with gr.Row():
                location_input = gr.Textbox(
                    label="📍 Location",
                    placeholder="e.g., Western Ghats, Kerala"
                )
                month_input = gr.Dropdown(
                    label="📅 Month",
                    choices=["", "January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"]
                )
            
            description_input = gr.Textbox(
                label="📝 Additional Notes",
                placeholder="Any observations about the bird...",
                lines=2
            )
            
            identify_btn = gr.Button("🔍 Identify Bird", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            gr.Markdown("### 🎯 Results")
            
            main_result = gr.Markdown(label="Identification")
            confidence_display = gr.Markdown(label="Confidence")
            predictions = gr.Markdown(label="Predictions")
            reasoning = gr.Markdown(label="Analysis")
            novelty_alert = gr.Markdown(visible=False)
    
    gr.HTML("""
    <div style="text-align: center; color: #64748b; margin-top: 2rem; padding: 1rem;">
        <p>🇮🇳 CSCR Initiative | Zero-Shot LLM (qwen2.5:3b) | Open Source</p>
    </div>
    """)
    
    # Event handlers
    identify_btn.click(
        fn=identify_bird,
        inputs=[audio_input, location_input, month_input, description_input],
        outputs=[main_result, confidence_display, predictions, reasoning, novelty_alert]
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

