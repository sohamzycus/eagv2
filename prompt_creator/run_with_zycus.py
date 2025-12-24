#!/usr/bin/env python3
"""
Quick Start Script for Zycus Azure OpenAI.

This script pre-configures the Prompt Creator with Zycus Azure OpenAI settings.

Usage:
    python run_with_zycus.py [--demo] [--cli] [--port PORT]

The API key can be provided via:
1. Command line: python run_with_zycus.py --api-key YOUR_KEY
2. Environment: export AZURE_OPENAI_API_KEY=YOUR_KEY
3. Interactive prompt (if not set)
"""

import argparse
import os
import sys
from getpass import getpass

# Pre-configure Zycus Azure OpenAI settings
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://zycus-ptu.azure-api.net/ptu-intakemanagement")
os.environ.setdefault("AZURE_OPENAI_DEPLOYMENT", "gpt4o-130524")
os.environ.setdefault("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
os.environ.setdefault("AZURE_OPENAI_VERIFY_SSL", "false")  # Corporate APIM
os.environ.setdefault("LLM_PROVIDER", "azure_openai")
os.environ.setdefault("LLM_MODEL", "gpt-4o")


def main():
    parser = argparse.ArgumentParser(
        description="Run Prompt Creator with Zycus Azure OpenAI GPT-4o",
    )
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument("--cli", action="store_true", help="Run CLI mode")
    parser.add_argument("--port", type=int, default=7860, help="UI port")
    parser.add_argument("--api-key", type=str, help="Azure OpenAI API key")

    args = parser.parse_args()

    # Set API key
    if args.api_key:
        os.environ["AZURE_OPENAI_API_KEY"] = args.api_key
    elif not os.getenv("AZURE_OPENAI_API_KEY"):
        print("=" * 60)
        print("Zycus Azure OpenAI GPT-4o Configuration")
        print("=" * 60)
        print(f"Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
        print(f"API Version: {os.getenv('AZURE_OPENAI_API_VERSION')}")
        print()
        api_key = getpass("Enter Azure OpenAI API Key: ")
        os.environ["AZURE_OPENAI_API_KEY"] = api_key

    # Import and run main
    from main import run_demo, run_cli, run_ui, create_llm_client

    # Create LLM client
    llm_client = create_llm_client()

    print()
    print(f"✅ Connected to: {llm_client.provider_name} / {llm_client.model_name}")
    print()

    if args.demo:
        run_demo(llm_client)
    elif args.cli:
        run_cli(llm_client)
    else:
        run_ui(args.port, llm_client)


if __name__ == "__main__":
    main()

