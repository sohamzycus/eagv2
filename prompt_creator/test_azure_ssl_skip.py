#!/usr/bin/env python3
"""
Test Azure OpenAI with SSL verification disabled.
For testing corporate APIM endpoints with custom certificates.
"""

import os
import sys
import httpx
import ssl

# Configuration
AZURE_ENDPOINT = "https://zycus-ptu.azure-api.net/ptu-intakemanagement"
DEPLOYMENT_NAME = "gpt4o-130524"
API_VERSION = "2024-02-15-preview"


def test_no_ssl_verify(api_key: str):
    """Test with SSL verification disabled."""
    print("=" * 60)
    print("Azure OpenAI Test (SSL Verify Disabled)")
    print("=" * 60)
    print(f"Endpoint: {AZURE_ENDPOINT}")
    print(f"Deployment: {DEPLOYMENT_NAME}")
    print()
    
    url = f"{AZURE_ENDPOINT}/openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={API_VERSION}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Connection successful!' in exactly those words."}
        ],
        "max_tokens": 20,
        "temperature": 0.0,
    }
    
    print(f"🔄 Testing with api-key header...")
    
    try:
        # Disable SSL verification
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0, verify=False)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            print(f"✅ Response: {content}")
            print()
            print("=" * 60)
            print("CONNECTION SUCCESSFUL!")
            print("=" * 60)
            return True, "api-key"
        else:
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Try with APIM subscription key
    print(f"\n🔄 Testing with Ocp-Apim-Subscription-Key header...")
    
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": api_key,
    }
    
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0, verify=False)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            print(f"✅ Response: {content}")
            print()
            print("=" * 60)
            print("CONNECTION SUCCESSFUL (using APIM subscription key)!")
            print("=" * 60)
            return True, "subscription-key"
        else:
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False, None


def test_openai_sdk_no_verify(api_key: str):
    """Test OpenAI SDK with SSL verification disabled."""
    print("\n🔄 Testing OpenAI SDK with SSL disabled...")
    
    try:
        from openai import AzureOpenAI
        import httpx
        
        # Create custom http client without SSL verification
        http_client = httpx.Client(verify=False)
        
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
                {"role": "user", "content": "Say 'SDK test passed!' in exactly those words."}
            ],
            max_tokens=20,
            temperature=0.0,
        )
        
        content = response.choices[0].message.content
        print(f"✅ SDK Response: {content}")
        return True
        
    except Exception as e:
        print(f"❌ SDK Error: {e}")
        return False


if __name__ == "__main__":
    # Suppress SSL warnings for testing
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("AZURE_OPENAI_API_KEY")
    
    if not api_key:
        print("Usage: python test_azure_ssl_skip.py YOUR_API_KEY")
        sys.exit(1)
    
    success, method = test_no_ssl_verify(api_key)
    
    if success:
        test_openai_sdk_no_verify(api_key)
        print(f"\n✅ Working authentication method: {method}")
    else:
        print("\n❌ All methods failed. Check API key and endpoint.")
        sys.exit(1)



