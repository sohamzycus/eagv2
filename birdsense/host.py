#!/usr/bin/env python3
"""
🐦 BirdSense - Public Hosting Script
Developed by Soham

Exposes your local BirdSense instance to the internet for testing.
Uses Gradio's built-in sharing feature for quick sharing.

Usage:
    python host.py              # Start with public URL
    python host.py --local      # Local only (no sharing)
"""

import argparse
import os
import sys

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description="Host BirdSense for public testing")
    parser.add_argument("--local", action="store_true", help="Local only (no public URL)")
    parser.add_argument("--port", type=int, default=7860, help="Port number (default: 7860)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🐦 BirdSense - AI Bird Identification")
    print("   Developed by Soham")
    print("=" * 60)
    
    # Import app
    from app import create_app, check_ollama
    
    # Check Ollama
    status = check_ollama()
    if not status['ok']:
        print("\n⚠️  Ollama not running!")
        print("   Start with: ollama serve")
        print("   Pull models: ollama pull llava:7b && ollama pull phi4:latest")
        sys.exit(1)
    
    print(f"\n✅ Ollama ready")
    print(f"   Vision (LLaVA): {'✅' if status['vision'] else '❌'}")
    print(f"   Text (phi4): {'✅' if status['text'] else '❌'}")
    
    # Create app
    app = create_app()
    
    # Launch
    share = not args.local
    
    if share:
        print("\n🌐 Creating public URL...")
        print("   (This may take a moment)")
    else:
        print("\n🏠 Running locally only")
    
    print("\n" + "=" * 60)
    
    app.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=share,
        show_error=True,
        favicon_path=None
    )


if __name__ == "__main__":
    main()

