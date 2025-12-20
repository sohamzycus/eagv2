#!/usr/bin/env python3
"""
BirdSense Setup Script

Handles:
- Virtual environment creation
- Dependency installation
- Ollama model download
- Initial model setup
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description, check=True):
    """Run a command with status output."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    if check and result.returncode != 0:
        print(f"❌ Failed: {description}")
        return False
    print(f"✅ {description}")
    return True


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🐦 BirdSense Setup                                         ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                ║
║   Setting up the bird recognition environment                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Step 1: Create virtual environment
    venv_path = project_dir / "venv"
    if not venv_path.exists():
        run_command(
            f"{sys.executable} -m venv venv",
            "Creating virtual environment"
        )
    else:
        print("✅ Virtual environment already exists")
    
    # Determine pip path
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip"
        python_path = venv_path / "Scripts" / "python"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    # Step 2: Upgrade pip
    run_command(
        f"{pip_path} install --upgrade pip",
        "Upgrading pip"
    )
    
    # Step 3: Install requirements
    run_command(
        f"{pip_path} install -r requirements.txt",
        "Installing Python dependencies"
    )
    
    # Step 4: Check Ollama
    print("\n" + "="*60)
    print("  Checking Ollama installation")
    print("="*60)
    
    ollama_check = subprocess.run("ollama --version", shell=True, capture_output=True)
    
    if ollama_check.returncode != 0:
        print("""
⚠️  Ollama not found!

To enable LLM-enhanced reasoning, install Ollama:

macOS/Linux:
  curl -fsSL https://ollama.com/install.sh | sh

Windows:
  Download from https://ollama.com/download

After installation, run:
  ollama pull phi3:mini
        """)
    else:
        print("✅ Ollama is installed")
        
        # Pull model
        print("\n  Pulling phi3:mini model (this may take a few minutes)...")
        run_command(
            "ollama pull phi3:mini",
            "Downloading Ollama model",
            check=False
        )
    
    # Step 5: Create samples directory
    samples_dir = project_dir / "samples"
    samples_dir.mkdir(exist_ok=True)
    print("✅ Created samples directory")
    
    # Step 6: Create checkpoints directory
    checkpoints_dir = project_dir / "checkpoints"
    checkpoints_dir.mkdir(exist_ok=True)
    print("✅ Created checkpoints directory")
    
    # Success message
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ✅ Setup Complete!                                         ║
║                                                              ║
║   To run the demo:                                           ║
║                                                              ║
║   1. Activate the virtual environment:                       ║
║      source venv/bin/activate  (Linux/macOS)                 ║
║      venv\\Scripts\\activate     (Windows)                    ║
║                                                              ║
║   2. Run the demo:                                           ║
║      python run_demo.py --test-all                           ║
║      python run_demo.py --interactive                        ║
║                                                              ║
║   3. Run tests:                                              ║
║      pytest tests/ -v                                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()

