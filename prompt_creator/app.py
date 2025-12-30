"""
Procurement Workflow Agent Creator - Entry Point

LLM is CORE to this system - not optional.
The LLM is used to:
1. Understand business intent
2. Design workflows intelligently
3. Identify required tools
4. Generate production-ready prompts
"""

import os
import sys

# Ensure proper imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def get_llm_client():
    """Initialize LLM client - REQUIRED."""
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if not api_key:
        print("\n" + "="*60)
        print("❌ ERROR: LLM Configuration Required")
        print("="*60)
        print("\nThe Workflow Creator REQUIRES an LLM to function.")
        print("\nSet these environment variables:")
        print("  export AZURE_OPENAI_API_KEY='your-key'")
        print("  export AZURE_OPENAI_ENDPOINT='your-endpoint'")
        print("  export AZURE_OPENAI_DEPLOYMENT='your-deployment'")
        print("\nOr create a .env file with these values.")
        print("="*60 + "\n")
        return None
    
    try:
        from core.llm.llm_factory import LLMFactory
        client = LLMFactory.create_zycus_gpt4o(api_key=api_key)
        print("✅ Connected to Azure OpenAI GPT-4o")
        return client
    except Exception as e:
        print(f"\n❌ Failed to connect to LLM: {e}")
        print("Please check your configuration.")
        return None


def main():
    """Main entry point."""
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Initialize LLM client (REQUIRED)
    llm_client = get_llm_client()
    
    # Import and create the app
    from ui.workflow_creator_app import create_workflow_creator_app
    app = create_workflow_creator_app(llm_client=llm_client)
    
    # Get port
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    
    if llm_client:
        print(f"\n🚀 Procurement Workflow Agent Creator")
        print(f"   Powered by: Azure OpenAI GPT-4o")
        print(f"   URL: http://localhost:{port}")
    else:
        print(f"\n⚠️  Starting in configuration mode...")
        print(f"   URL: http://localhost:{port}")
        print("   Configure LLM to enable full functionality.\n")
    
    # Launch
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )


if __name__ == "__main__":
    main()
