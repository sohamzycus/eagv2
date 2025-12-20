"""
BirdSense Gradio App for HuggingFace Spaces Deployment

This creates a beautiful Gradio interface that can be deployed
to HuggingFace Spaces for free public access.

Deploy to HuggingFace:
1. Create a new Space at https://huggingface.co/new-space
2. Select "Gradio" as the SDK
3. Push this repository to the Space
"""

import gradio as gr
import numpy as np
import torch
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from audio.preprocessor import AudioPreprocessor
from audio.augmentation import AudioAugmenter
from models.audio_classifier import BirdAudioClassifier
from data.species_db import IndiaSpeciesDatabase

# Initialize components
print("🐦 Loading BirdSense...")
preprocessor = AudioPreprocessor()
species_db = IndiaSpeciesDatabase()
classifier = BirdAudioClassifier(num_classes=species_db.get_num_classes())
classifier.eval()

# Load trained weights if available
checkpoint_path = Path("checkpoints/best_calibrated.pt")
if checkpoint_path.exists():
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    classifier.load_state_dict(checkpoint['model_state_dict'])
    print("✅ Loaded trained model")
else:
    print("⚠️ Using untrained model (demo mode)")

print(f"✅ Loaded {species_db.get_num_classes()} species")


def identify_bird(audio, location=None, month=None):
    """
    Identify bird species from audio input.
    
    Args:
        audio: Tuple of (sample_rate, audio_data) from Gradio
        location: Optional location string
        month: Optional month number
        
    Returns:
        Dictionary with results for Gradio outputs
    """
    if audio is None:
        return {
            species_output: "Please upload or record audio",
            confidence_output: 0,
            all_predictions: "No audio provided",
            quality_output: "N/A",
            reasoning_output: ""
        }
    
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
    
    # Preprocess
    result = preprocessor.process(audio_data)
    mel_specs = result['mel_specs']
    
    # Run classifier
    with torch.no_grad():
        x = torch.tensor(mel_specs[0]).unsqueeze(0)
        predictions = classifier.predict(x, top_k=5)
    
    # Format results
    top_indices = predictions['top_indices'][0].tolist()
    top_probs = predictions['top_probabilities'][0].tolist()
    
    # Build predictions list
    pred_lines = []
    for i, (idx, prob) in enumerate(zip(top_indices, top_probs), 1):
        species = species_db.get_species(idx)
        if species:
            hindi = f" ({species.hindi_name})" if species.hindi_name else ""
            pred_lines.append(f"{i}. **{species.common_name}**{hindi} - {prob*100:.1f}%")
            pred_lines.append(f"   _{species.scientific_name}_ | {species.call_description}")
    
    # Top prediction
    top_species = species_db.get_species(top_indices[0])
    top_name = top_species.common_name if top_species else "Unknown"
    top_conf = top_probs[0] * 100
    
    # Generate reasoning
    reasoning = f"""
### Analysis

**Audio Quality:** {quality['quality_label'].upper()} (score: {quality['quality_score']:.2f})
**Duration:** {result['duration']:.1f} seconds
**Estimated SNR:** {quality['estimated_snr_db']:.1f} dB

### Top Match: {top_name}

The audio analysis suggests this is most likely a **{top_name}**.
"""
    
    if top_species:
        reasoning += f"""
**About this species:**
- Scientific name: _{top_species.scientific_name}_
- Family: {top_species.family}
- Call: {top_species.call_description}
- Habitats: {', '.join(top_species.habitats)}
- Conservation: {top_species.conservation_status}
"""
    
    if location:
        reasoning += f"\n📍 Location context: {location}"
    
    return {
        species_output: top_name,
        confidence_output: top_conf,
        all_predictions: "\n".join(pred_lines),
        quality_output: f"{quality['quality_label'].upper()} ({quality['quality_score']:.2f})",
        reasoning_output: reasoning
    }


def get_species_list():
    """Get formatted species list for display."""
    species = species_db.get_all_species()
    lines = []
    for s in species:
        hindi = f" / {s.hindi_name}" if s.hindi_name else ""
        lines.append(f"• **{s.common_name}**{hindi} (_{s.scientific_name}_)")
    return "\n".join(lines)


# Custom CSS for beautiful UI
css = """
.gradio-container {
    font-family: 'Outfit', sans-serif !important;
}

.main-header {
    text-align: center;
    background: linear-gradient(135deg, #1a2332, #243447);
    padding: 2rem;
    border-radius: 12px;
    margin-bottom: 1rem;
}

.species-card {
    background: linear-gradient(135deg, rgba(74, 222, 128, 0.1), rgba(34, 211, 238, 0.1));
    border: 1px solid rgba(74, 222, 128, 0.3);
    border-radius: 12px;
    padding: 1rem;
}

.confidence-high { color: #4ade80; }
.confidence-medium { color: #fbbf24; }
.confidence-low { color: #ef4444; }
"""

# Build Gradio interface
with gr.Blocks(css=css, title="🐦 BirdSense", theme=gr.themes.Soft(
    primary_hue="green",
    secondary_hue="cyan",
)) as demo:
    
    gr.HTML("""
    <div class="main-header">
        <h1>🐦 BirdSense</h1>
        <p style="color: #94a3b8;">Intelligent Bird Recognition for India | CSCR Initiative</p>
        <p style="color: #64748b; font-size: 0.9rem;">Powered by Meta SAM-Audio & Local ML</p>
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
                    label="📍 Location (optional)",
                    placeholder="e.g., Western Ghats, Kerala"
                )
                month_input = gr.Dropdown(
                    label="📅 Month (optional)",
                    choices=["", "January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"]
                )
            
            identify_btn = gr.Button("🔍 Identify Bird", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            gr.Markdown("### 🎯 Results")
            
            with gr.Group():
                species_output = gr.Textbox(label="Top Match", interactive=False)
                confidence_output = gr.Slider(
                    label="Confidence",
                    minimum=0,
                    maximum=100,
                    value=0,
                    interactive=False
                )
                quality_output = gr.Textbox(label="Audio Quality", interactive=False)
            
            all_predictions = gr.Markdown(label="All Predictions")
    
    with gr.Row():
        reasoning_output = gr.Markdown(label="AI Analysis")
    
    # Species database accordion
    with gr.Accordion("📚 Supported Species (25+)", open=False):
        gr.Markdown(get_species_list())
    
    # Footer
    gr.HTML("""
    <div style="text-align: center; color: #64748b; margin-top: 2rem; padding: 1rem;">
        <p>🇮🇳 CSCR Initiative | Open Source | 
        <a href="https://github.com" target="_blank">GitHub</a> | 
        <a href="https://ai.meta.com/samaudio/" target="_blank">Meta SAM-Audio</a></p>
    </div>
    """)
    
    # Event handlers
    identify_btn.click(
        fn=identify_bird,
        inputs=[audio_input, location_input, month_input],
        outputs=[species_output, confidence_output, all_predictions, quality_output, reasoning_output]
    )
    
    audio_input.change(
        fn=identify_bird,
        inputs=[audio_input, location_input, month_input],
        outputs=[species_output, confidence_output, all_predictions, quality_output, reasoning_output]
    )


# Launch configuration
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

