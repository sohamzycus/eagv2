"""
Deploy BirdSense to HuggingFace Spaces.

Usage:
    python deploy_to_hf.py --token YOUR_HF_TOKEN
"""

from huggingface_hub import HfApi, create_repo, upload_folder
import argparse
import os
from pathlib import Path


def deploy_to_huggingface(token: str, space_name: str = "birdsense"):
    """Deploy BirdSense Space to HuggingFace."""
    
    api = HfApi(token=token)
    
    # Get username
    user = api.whoami()
    username = user["name"]
    print(f"✅ Logged in as: {username}")
    
    repo_id = f"{username}/{space_name}"
    
    # Create the Space repository
    try:
        create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="gradio",
            token=token,
            exist_ok=True
        )
        print(f"✅ Space created/exists: {repo_id}")
    except Exception as e:
        print(f"⚠️ Space creation note: {e}")
    
    # Upload the birdsense-space folder
    space_dir = Path(__file__).parent / "birdsense-space"
    
    print(f"📤 Uploading from: {space_dir}")
    
    # Upload all files
    upload_folder(
        folder_path=str(space_dir),
        repo_id=repo_id,
        repo_type="space",
        token=token,
        ignore_patterns=["__pycache__", "*.pyc", ".git", "venv"]
    )
    
    print(f"\n{'='*60}")
    print(f"🎉 DEPLOYMENT SUCCESSFUL!")
    print(f"{'='*60}")
    print(f"\n🌐 Your app is live at:")
    print(f"   https://huggingface.co/spaces/{repo_id}")
    print(f"\n📱 Share this link with your researchers!")
    print(f"{'='*60}\n")
    
    return f"https://huggingface.co/spaces/{repo_id}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy BirdSense to HuggingFace")
    parser.add_argument("--token", required=True, help="HuggingFace API token")
    parser.add_argument("--name", default="birdsense", help="Space name")
    
    args = parser.parse_args()
    
    deploy_to_huggingface(args.token, args.name)

