#!/usr/bin/env python3
"""
Test Azure OpenAI Connection

This script tests the connection to Azure OpenAI GPT-4o.
Run with your API key to verify connectivity.

Usage:
    python test_azure_connection.py YOUR_API_KEY
    
    # Or with environment variable:
    export AZURE_OPENAI_API_KEY=YOUR_API_KEY
    python test_azure_connection.py
"""

import os
import sys

# Configuration
AZURE_ENDPOINT = "https://zycus-ptu.azure-api.net/ptu-intakemanagement"
DEPLOYMENT_NAME = "gpt4o-130524"
API_VERSION = "2024-02-15-preview"


def test_connection(api_key: str):
    """Test Azure OpenAI connection with a simple request."""
    try:
        from openai import AzureOpenAI
        
        print("=" * 60)
        print("Azure OpenAI Connection Test")
        print("=" * 60)
        print(f"Endpoint: {AZURE_ENDPOINT}")
        print(f"Deployment: {DEPLOYMENT_NAME}")
        print(f"API Version: {API_VERSION}")
        print(f"API Key: {'*' * 8}{api_key[-4:]}")
        print()
        
        client = AzureOpenAI(
            api_key=api_key,
            api_version=API_VERSION,
            azure_endpoint=AZURE_ENDPOINT,
        )
        
        print("🔄 Sending test request...")
        
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Connection successful!' in exactly those words."}
            ],
            max_tokens=20,
            temperature=0.0,
        )
        
        content = response.choices[0].message.content
        print(f"✅ Response: {content}")
        print()
        print("=" * 60)
        print("CONNECTION TEST PASSED!")
        print("=" * 60)
        return True
        
    except ImportError:
        print("❌ ERROR: openai package not installed")
        print("   Run: pip install openai")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check if API key is correct")
        print("2. Verify endpoint URL")
        print("3. Ensure deployment name matches")
        print("4. Check API version compatibility")
        return False


if __name__ == "__main__":
    # Get API key from command line or environment
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if not api_key:
        print("Usage: python test_azure_connection.py YOUR_API_KEY")
        print("   Or: export AZURE_OPENAI_API_KEY=YOUR_API_KEY && python test_azure_connection.py")
        sys.exit(1)
    
    success = test_connection(api_key)
    sys.exit(0 if success else 1)



