#!/usr/bin/env python3
"""
Prompt Creator - Hugging Face Spaces Entry Point

This is the main entry point for Hugging Face Spaces deployment.
Credentials are loaded from HuggingFace Secrets.

Environment Variables (set as HuggingFace Secrets):
- AZURE_OPENAI_API_KEY: Your Azure OpenAI API key
- AZURE_OPENAI_ENDPOINT: Azure endpoint URL
- AZURE_OPENAI_DEPLOYMENT: Deployment name
- AZURE_OPENAI_API_VERSION: API version (optional)
- AZURE_OPENAI_VERIFY_SSL: Set to "false" for corporate endpoints
"""

import os
import sys
from pathlib import Path

# Setup Python path for package imports
# This ensures prompt_creator package can be found
APP_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(APP_DIR))

# Also add parent if running from within prompt_creator directory
if APP_DIR.name == "prompt_creator":
    sys.path.insert(0, str(APP_DIR.parent))

# Load environment from .env if exists (for local development)
try:
    from dotenv import load_dotenv
    env_file = APP_DIR / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        load_dotenv()
except ImportError:
    pass

# Set default values for Zycus endpoint if not provided
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://zycus-ptu.azure-api.net/ptu-intakemanagement")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT", "gpt4o-130524")
os.environ.setdefault("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
os.environ.setdefault("AZURE_OPENAI_VERIFY_SSL", "false")


def create_llm_client():
    """Create LLM client from environment."""
    # Import with fallback for different module structures
    try:
        from prompt_creator.core.llm.llm_factory import LLMFactory
        from prompt_creator.core.llm.azure_openai_client import MockLLMClient
    except ImportError:
        # Try relative import if prompt_creator is the current package
        from core.llm.llm_factory import LLMFactory
        from core.llm.azure_openai_client import MockLLMClient
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if api_key:
        try:
            client = LLMFactory.create_zycus_gpt4o(api_key=api_key)
            print(f"✅ Connected to Azure OpenAI GPT-4o")
            return client
        except Exception as e:
            print(f"⚠️ Could not create Azure client: {e}")
    
    print("⚠️ No API key found - using demo mode")
    print("   Set AZURE_OPENAI_API_KEY in HuggingFace Secrets for live LLM")
    return MockLLMClient()


def main():
    """Main entry point for HuggingFace Spaces."""
    # Import with fallback for different module structures
    try:
        from prompt_creator.ui.gradio_app import create_app
    except ImportError:
        from ui.gradio_app import create_app
    
    # Create LLM client
    llm_client = create_llm_client()
    
    # Create Gradio app
    app = create_app(llm_client=llm_client)
    
    # Get port from environment (HuggingFace uses 7860)
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    
    print(f"🚀 Starting Prompt Creator on port {port}")
    print(f"   LLM: {llm_client.provider_name} / {llm_client.model_name}")
    
    # Launch with HuggingFace-compatible settings
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()

