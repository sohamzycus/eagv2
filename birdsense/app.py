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

# Import provider factory (handles all LLM connectivity)
from providers import provider_factory

# Import analysis functions (all identification logic)
from analysis import (
    identify_audio_streaming,
    identify_image_streaming,
    identify_description,
    BIRDNET_AVAILABLE
)

# Import feedback system
from feedback import (
    save_feedback,
    get_analytics,
    format_analytics_html
)


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
