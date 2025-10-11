#!/usr/bin/env python3
"""
Fix credentials.json redirect URIs
"""
import json
import shutil

def fix_credentials():
    """Fix redirect_uris in credentials.json"""
    print("🔧 Fixing credentials.json redirect URIs...")
    
    # Backup original
    shutil.copy('credentials.json', 'credentials_backup.json')
    print("✅ Backed up original to credentials_backup.json")
    
    # Load current credentials
    with open('credentials.json', 'r') as f:
        creds = json.load(f)
    
    # Fix redirect URIs with proper ports
    creds['installed']['redirect_uris'] = [
        'http://localhost:8080/',
        'http://localhost:8081/', 
        'http://localhost:8082/',
        'http://localhost:9090/',
        'urn:ietf:wg:oauth:2.0:oob'  # Console fallback
    ]
    
    # Save fixed credentials
    with open('credentials.json', 'w') as f:
        json.dump(creds, f, indent=2)
    
    print("✅ Fixed redirect URIs in credentials.json")
    print("📋 Added redirect URIs:")
    for uri in creds['installed']['redirect_uris']:
        print(f"   - {uri}")
    
    return True

if __name__ == "__main__":
    fix_credentials()
    print("\n🚀 Now try authentication again!")
    print("▶️  Run: python fresh_auth.py")
