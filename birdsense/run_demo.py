#!/usr/bin/env python3
"""
BirdSense MVP Demo - Bird Audio Recognition

This demo showcases the audio recognition pipeline with:
- Real-time audio recording or file input
- Multiple test scenarios (clear, feeble, noisy, multi-bird)
- LLM-enhanced reasoning (via Ollama)
- Species identification for Indian birds

Usage:
    # Test with audio file
    python run_demo.py --audio path/to/bird_call.wav
    
    # Record from microphone
    python run_demo.py --record --duration 10
    
    # Run all test scenarios with synthetic audio
    python run_demo.py --test-all
    
    # Interactive mode
    python run_demo.py --interactive
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

# Rich console for beautiful output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Install 'rich' for better output: pip install rich")

# Import BirdSense modules
from audio.preprocessor import AudioPreprocessor, AudioConfig
from audio.augmentation import AudioAugmenter
from audio.encoder import AudioEncoder
from models.audio_classifier import BirdAudioClassifier
from models.novelty_detector import NoveltyDetector
from data.species_db import IndiaSpeciesDatabase
from llm.ollama_client import OllamaConfig
from llm.reasoning import BirdReasoningEngine, ReasoningContext


console = Console() if RICH_AVAILABLE else None


def print_header():
    """Print welcome header."""
    header = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🐦 BirdSense MVP - Intelligent Bird Recognition           ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                ║
║   Audio-based bird species identification for India          ║
║   Powered by lightweight models + Ollama LLM                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    if console:
        console.print(Panel(header, style="bold green"))
    else:
        print(header)


def generate_synthetic_bird_call(
    duration: float = 3.0,
    sample_rate: int = 32000,
    base_freq: float = 2000.0
) -> np.ndarray:
    """Generate synthetic bird-like call for testing."""
    t = np.linspace(0, duration, int(duration * sample_rate))
    
    # Frequency modulation
    freq_mod = base_freq + 300 * np.sin(2 * np.pi * 8 * t)
    
    # Generate signal with harmonics
    signal = np.zeros_like(t)
    for i in range(1, 4):
        amplitude = 1.0 / i
        phase = 2 * np.pi * freq_mod * i * np.cumsum(np.ones_like(t)) / sample_rate
        signal += amplitude * np.sin(phase)
    
    # Amplitude envelope
    envelope = np.ones_like(t)
    attack = int(0.1 * sample_rate)
    decay = int(0.2 * sample_rate)
    envelope[:attack] = np.linspace(0, 1, attack)
    envelope[-decay:] = np.linspace(1, 0, decay)
    
    signal = signal * envelope
    signal = signal / (np.max(np.abs(signal)) + 1e-8) * 0.8
    
    return signal.astype(np.float32)


class BirdSenseDemo:
    """Main demo class for BirdSense."""
    
    def __init__(self):
        self.preprocessor = AudioPreprocessor()
        self.augmenter = AudioAugmenter(seed=42)
        self.encoder = AudioEncoder(architecture='cnn', n_mels=128, embedding_dim=384)
        self.classifier = BirdAudioClassifier(num_classes=25, embedding_dim=384)
        self.species_db = IndiaSpeciesDatabase()
        
        # Initialize LLM reasoning (optional)
        self.reasoning_engine = None
        self._init_reasoning()
    
    def _init_reasoning(self):
        """Initialize LLM reasoning engine if Ollama is available."""
        try:
            config = OllamaConfig()
            self.reasoning_engine = BirdReasoningEngine(
                ollama_config=config,
                species_db=self.species_db
            )
            status = self.reasoning_engine.check_ollama_status()
            if status["status"] == "ready":
                if console:
                    console.print("✓ Ollama LLM ready for enhanced reasoning", style="green")
            else:
                if console:
                    console.print(f"⚠ Ollama not ready: {status}", style="yellow")
                self.reasoning_engine = None
        except Exception as e:
            if console:
                console.print(f"⚠ LLM reasoning disabled: {e}", style="yellow")
            self.reasoning_engine = None
    
    def process_audio(
        self,
        audio: np.ndarray,
        audio_label: str = "Input Audio",
        use_llm: bool = True,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process audio and identify bird species.
        
        Args:
            audio: Audio waveform
            audio_label: Label for display
            use_llm: Whether to use LLM reasoning
            location: Optional location context
            
        Returns:
            Dictionary with identification results
        """
        import torch
        
        # Step 1: Assess audio quality
        sr = self.preprocessor.config.sample_rate
        quality = self.preprocessor.get_audio_quality_assessment(audio, sr)
        
        # Step 2: Preprocess audio
        processed = self.preprocessor.process(audio, return_waveform=True)
        mel_specs = processed["mel_specs"]
        
        # Step 3: Run classifier on each chunk
        self.classifier.eval()
        all_predictions = []
        
        with torch.no_grad():
            for mel_spec in mel_specs:
                x = torch.tensor(mel_spec).unsqueeze(0)
                preds = self.classifier.predict(x, top_k=5)
                all_predictions.append(preds)
        
        # Aggregate predictions across chunks
        aggregated = self._aggregate_predictions(all_predictions)
        
        # Step 4: Get species information
        species_results = []
        for idx, prob in zip(aggregated["top_indices"], aggregated["top_probs"]):
            species = self.species_db.get_species(idx)
            if species:
                species_results.append({
                    "id": idx,
                    "name": species.common_name,
                    "scientific_name": species.scientific_name,
                    "confidence": float(prob),
                    "call_description": species.call_description
                })
        
        result = {
            "audio_label": audio_label,
            "quality": quality,
            "duration": processed["duration"],
            "num_chunks": processed["num_chunks"],
            "predictions": species_results,
            "uncertainty": float(aggregated["uncertainty"]),
            "embedding": aggregated.get("embedding")
        }
        
        # Step 5: LLM reasoning (if available)
        if use_llm and self.reasoning_engine and species_results:
            context = ReasoningContext(
                audio_predictions=[(s["id"], s["confidence"]) for s in species_results],
                audio_quality=quality["quality_label"],
                location_name=location
            )
            try:
                reasoning_result = self.reasoning_engine.reason(context)
                result["llm_reasoning"] = {
                    "species": reasoning_result.species_name,
                    "confidence": reasoning_result.confidence,
                    "reasoning": reasoning_result.reasoning,
                    "novelty_flag": reasoning_result.novelty_flag,
                    "novelty_explanation": reasoning_result.novelty_explanation
                }
            except Exception as e:
                result["llm_reasoning"] = {"error": str(e)}
        
        return result
    
    def _aggregate_predictions(self, all_predictions) -> Dict:
        """Aggregate predictions from multiple audio chunks."""
        import torch
        
        if len(all_predictions) == 1:
            return {
                "top_indices": all_predictions[0]["top_indices"][0].tolist(),
                "top_probs": all_predictions[0]["top_probabilities"][0].tolist(),
                "uncertainty": all_predictions[0]["uncertainty"][0].item(),
                "embedding": all_predictions[0]["embeddings"][0]
            }
        
        # Average probabilities across chunks
        all_probs = torch.stack([p["top_probabilities"][0] for p in all_predictions])
        avg_probs = all_probs.mean(dim=0)
        
        # Get top predictions from averaged
        top_probs, reorder = torch.sort(avg_probs, descending=True)
        top_indices = all_predictions[0]["top_indices"][0][reorder]
        
        # Average uncertainty
        avg_uncertainty = np.mean([p["uncertainty"][0].item() for p in all_predictions])
        
        # Average embeddings
        avg_embedding = torch.stack([p["embeddings"][0] for p in all_predictions]).mean(dim=0)
        
        return {
            "top_indices": top_indices.tolist(),
            "top_probs": top_probs.tolist(),
            "uncertainty": avg_uncertainty,
            "embedding": avg_embedding
        }
    
    def display_results(self, result: Dict[str, Any]):
        """Display identification results."""
        if console:
            self._display_rich(result)
        else:
            self._display_plain(result)
    
    def _display_rich(self, result: Dict[str, Any]):
        """Display results with rich formatting."""
        # Audio info panel
        quality = result["quality"]
        info_text = f"""
**Audio:** {result['audio_label']}
**Duration:** {result['duration']:.2f}s ({result['num_chunks']} chunks)
**Quality:** {quality['quality_label'].upper()} (score: {quality['quality_score']:.2f})
**SNR:** ~{quality['estimated_snr_db']:.1f} dB
"""
        console.print(Panel(Markdown(info_text), title="📊 Audio Analysis"))
        
        # Predictions table
        table = Table(title="🐦 Species Predictions", show_header=True, header_style="bold cyan")
        table.add_column("Rank", style="dim", width=6)
        table.add_column("Species", style="bold")
        table.add_column("Scientific Name", style="italic")
        table.add_column("Confidence", justify="right")
        table.add_column("Call Description")
        
        for i, pred in enumerate(result["predictions"][:5], 1):
            conf_style = "green" if pred["confidence"] > 0.7 else "yellow" if pred["confidence"] > 0.4 else "red"
            table.add_row(
                f"#{i}",
                pred["name"],
                pred["scientific_name"],
                f"[{conf_style}]{pred['confidence']:.1%}[/{conf_style}]",
                pred["call_description"][:50] + "..." if len(pred["call_description"]) > 50 else pred["call_description"]
            )
        
        console.print(table)
        console.print(f"\n🎯 Uncertainty: {result['uncertainty']:.2%}")
        
        # LLM reasoning
        if "llm_reasoning" in result and "error" not in result["llm_reasoning"]:
            llm = result["llm_reasoning"]
            reasoning_text = f"""
**LLM Assessment:** {llm['species']}
**Confidence:** {llm['confidence']:.0%}

{llm['reasoning']}
"""
            if llm.get("novelty_flag"):
                reasoning_text += f"\n\n⚠️ **NOVELTY ALERT:** {llm.get('novelty_explanation', 'Unusual sighting detected')}"
            
            console.print(Panel(Markdown(reasoning_text), title="🤖 AI Reasoning", border_style="blue"))
    
    def _display_plain(self, result: Dict[str, Any]):
        """Display results in plain text."""
        print(f"\n{'='*60}")
        print(f"Audio: {result['audio_label']}")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"Quality: {result['quality']['quality_label']} ({result['quality']['quality_score']:.2f})")
        print(f"\nTop Predictions:")
        for i, pred in enumerate(result["predictions"][:5], 1):
            print(f"  {i}. {pred['name']} ({pred['scientific_name']}): {pred['confidence']:.1%}")
        print(f"\nUncertainty: {result['uncertainty']:.2%}")
        print(f"{'='*60}")
    
    def run_test_scenario(
        self,
        scenario: str,
        duration: float = 3.0
    ) -> Dict[str, Any]:
        """
        Run a specific test scenario.
        
        Args:
            scenario: One of 'clear', 'feeble', 'noisy', 'multi_bird', 'brief'
            duration: Audio duration in seconds
            
        Returns:
            Test results
        """
        sr = 32000
        base_audio = generate_synthetic_bird_call(duration=duration, sample_rate=sr)
        
        if scenario == "clear":
            audio = base_audio
            label = "Clear Recording (High SNR)"
        elif scenario == "feeble":
            audio, _ = self.augmenter.create_challenging_sample(base_audio, sr, 'feeble')
            label = "Feeble/Distant Recording"
        elif scenario == "noisy":
            audio, _ = self.augmenter.create_challenging_sample(base_audio, sr, 'noisy')
            label = "Noisy Environment"
        elif scenario == "multi_bird":
            # Generate overlapping calls
            audio = base_audio.copy()
            for i in range(2):
                other = generate_synthetic_bird_call(
                    duration=duration * 0.7,
                    base_freq=1500 + i * 1000
                )
                start = int(np.random.uniform(0, len(audio) - len(other)))
                audio[start:start+len(other)] += other * 0.5
            audio = self.augmenter.add_noise(audio, sr, snr_db=15)
            label = "Multi-Bird Chorus"
        elif scenario == "brief":
            audio, _ = self.augmenter.create_challenging_sample(base_audio, sr, 'brief')
            label = "Brief Call (<1s)"
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        return self.process_audio(audio, audio_label=label, use_llm=True)
    
    def run_all_tests(self):
        """Run all test scenarios."""
        scenarios = ["clear", "feeble", "noisy", "multi_bird", "brief"]
        
        print_header()
        
        if console:
            console.print("\n[bold]Running all test scenarios...[/bold]\n")
        else:
            print("\nRunning all test scenarios...\n")
        
        for scenario in scenarios:
            if console:
                console.print(f"\n[bold cyan]━━━ Scenario: {scenario.upper()} ━━━[/bold cyan]")
            else:
                print(f"\n--- Scenario: {scenario.upper()} ---")
            
            result = self.run_test_scenario(scenario)
            self.display_results(result)
    
    def process_file(self, audio_path: str, use_llm: bool = True) -> Dict[str, Any]:
        """Process audio file."""
        import librosa
        
        audio, sr = librosa.load(audio_path, sr=self.preprocessor.config.sample_rate, mono=True)
        label = Path(audio_path).name
        
        return self.process_audio(audio, audio_label=label, use_llm=use_llm)
    
    def record_and_process(self, duration: float = 10.0) -> Dict[str, Any]:
        """Record audio and process."""
        try:
            import sounddevice as sd
        except ImportError:
            print("Install sounddevice for recording: pip install sounddevice")
            return {}
        
        sr = self.preprocessor.config.sample_rate
        
        if console:
            console.print(f"\n🎤 Recording for {duration}s... (make bird sounds!)", style="bold yellow")
        else:
            print(f"\nRecording for {duration}s...")
        
        audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype=np.float32)
        sd.wait()
        audio = audio.flatten()
        
        if console:
            console.print("✓ Recording complete!", style="green")
        else:
            print("Recording complete!")
        
        return self.process_audio(audio, audio_label="Live Recording", use_llm=True)
    
    def interactive_mode(self):
        """Run interactive demo mode."""
        print_header()
        
        while True:
            if console:
                console.print("\n[bold]Options:[/bold]")
                console.print("  1. Test with clear audio")
                console.print("  2. Test with feeble audio")
                console.print("  3. Test with noisy audio")
                console.print("  4. Test with multi-bird audio")
                console.print("  5. Test with brief call")
                console.print("  6. Record from microphone")
                console.print("  7. Run all tests")
                console.print("  8. List species database")
                console.print("  q. Quit")
                
                choice = console.input("\n[bold cyan]Enter choice: [/bold cyan]")
            else:
                print("\nOptions:")
                print("  1-5: Run test scenarios")
                print("  6: Record from mic")
                print("  7: Run all tests")
                print("  8: List species")
                print("  q: Quit")
                choice = input("Enter choice: ")
            
            if choice.lower() == 'q':
                break
            elif choice == '1':
                result = self.run_test_scenario("clear")
                self.display_results(result)
            elif choice == '2':
                result = self.run_test_scenario("feeble")
                self.display_results(result)
            elif choice == '3':
                result = self.run_test_scenario("noisy")
                self.display_results(result)
            elif choice == '4':
                result = self.run_test_scenario("multi_bird")
                self.display_results(result)
            elif choice == '5':
                result = self.run_test_scenario("brief")
                self.display_results(result)
            elif choice == '6':
                result = self.record_and_process(duration=10)
                if result:
                    self.display_results(result)
            elif choice == '7':
                self.run_all_tests()
            elif choice == '8':
                self._list_species()
    
    def _list_species(self):
        """List species in database."""
        species_list = self.species_db.get_all_species()
        
        if console:
            table = Table(title="🐦 India Bird Species Database", show_header=True)
            table.add_column("ID", style="dim")
            table.add_column("Common Name", style="bold")
            table.add_column("Scientific Name", style="italic")
            table.add_column("Hindi", style="cyan")
            table.add_column("Status")
            
            for species in species_list[:25]:
                table.add_row(
                    str(species.id),
                    species.common_name,
                    species.scientific_name,
                    species.hindi_name or "-",
                    species.conservation_status
                )
            
            console.print(table)
            console.print(f"\nTotal species: {len(species_list)}")
        else:
            for species in species_list[:25]:
                print(f"{species.id}: {species.common_name} ({species.scientific_name})")


def main():
    parser = argparse.ArgumentParser(
        description="BirdSense MVP Demo - Bird Audio Recognition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_demo.py --test-all              Run all test scenarios
  python run_demo.py --audio bird.wav        Process audio file
  python run_demo.py --record --duration 10  Record and process
  python run_demo.py --interactive           Interactive mode
        """
    )
    
    parser.add_argument("--audio", "-a", type=str, help="Path to audio file")
    parser.add_argument("--record", "-r", action="store_true", help="Record from microphone")
    parser.add_argument("--duration", "-d", type=float, default=10.0, help="Recording duration (seconds)")
    parser.add_argument("--test-all", action="store_true", help="Run all test scenarios")
    parser.add_argument("--test", "-t", type=str, 
                       choices=["clear", "feeble", "noisy", "multi_bird", "brief"],
                       help="Run specific test scenario")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM reasoning")
    
    args = parser.parse_args()
    
    # Initialize demo
    demo = BirdSenseDemo()
    
    if args.audio:
        print_header()
        result = demo.process_file(args.audio, use_llm=not args.no_llm)
        demo.display_results(result)
    elif args.record:
        print_header()
        result = demo.record_and_process(duration=args.duration)
        if result:
            demo.display_results(result)
    elif args.test_all:
        demo.run_all_tests()
    elif args.test:
        print_header()
        result = demo.run_test_scenario(args.test)
        demo.display_results(result)
    elif args.interactive:
        demo.interactive_mode()
    else:
        # Default: run all tests
        demo.run_all_tests()


if __name__ == "__main__":
    main()

