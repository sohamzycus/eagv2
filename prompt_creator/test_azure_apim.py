#!/usr/bin/env python3
"""
Test Azure OpenAI via API Management (APIM)

Zycus endpoint appears to be an Azure API Management proxy.
This tests different authentication methods.
"""

import os
import sys
import httpx
import json

# Configuration
AZURE_ENDPOINT = "https://zycus-ptu.azure-api.net/ptu-intakemanagement"
DEPLOYMENT_NAME = "gpt4o-130524"
API_VERSION = "2024-02-15-preview"


def test_with_openai_sdk(api_key: str):
    """Test using OpenAI SDK with custom headers."""
    print("\n--- Test 1: OpenAI SDK with api-key header ---")
    try:
        from openai import AzureOpenAI
        import httpx
        
        # Create custom http client with subscription key
        custom_headers = {
            "Ocp-Apim-Subscription-Key": api_key,
        }
        http_client = httpx.Client(headers=custom_headers)
        
        client = AzureOpenAI(
            api_key=api_key,
            api_version=API_VERSION,
            azure_endpoint=AZURE_ENDPOINT,
            http_client=http_client,
        )
        
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello' only."}
            ],
            max_tokens=10,
            temperature=0.0,
        )
        
        print(f"✅ Success: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_direct_http(api_key: str):
    """Test direct HTTP request to understand API structure."""
    print("\n--- Test 2: Direct HTTP Request ---")
    
    url = f"{AZURE_ENDPOINT}/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={API_VERSION}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello' only."}
        ],
        "max_tokens": 10,
        "temperature": 0.0,
    }
    
    print(f"URL: {url}")
    
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['choices'][0]['message']['content']}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_with_subscription_key(api_key: str):
    """Test with Ocp-Apim-Subscription-Key header."""
    print("\n--- Test 3: With APIM Subscription Key Header ---")
    
    url = f"{AZURE_ENDPOINT}/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={API_VERSION}"
    
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": api_key,
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello' only."}
        ],
        "max_tokens": 10,
        "temperature": 0.0,
    }
    
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['choices'][0]['message']['content']}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_base_endpoint(api_key: str):
    """Test with base endpoint (without path)."""
    print("\n--- Test 4: Base Endpoint without path ---")
    
    base_url = "https://zycus-ptu.azure-api.net"
    url = f"{base_url}/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={API_VERSION}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello' only."}
        ],
        "max_tokens": 10,
        "temperature": 0.0,
    }
    
    print(f"URL: {url}")
    
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data['choices'][0]['message']['content']}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("AZURE_OPENAI_API_KEY")
    
    if not api_key:
        print("Usage: python test_azure_apim.py YOUR_API_KEY")
        sys.exit(1)
    
    print("=" * 60)
    print("Azure OpenAI APIM Connection Tests")
    print("=" * 60)
    print(f"API Key: {'*' * 28}{api_key[-4:]}")
    
    # Run tests
    test_direct_http(api_key)
    test_with_subscription_key(api_key)
    test_base_endpoint(api_key)
    test_with_openai_sdk(api_key)

