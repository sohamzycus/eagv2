#!/bin/bash
# 🐦 BirdSense - Cloud Deployment Script
# Developed by Soham
#
# Deploys to HuggingFace Spaces with auto-refresh on GitHub push
#
# Usage:
#   ./deploy_cloud.sh setup     # First-time setup
#   ./deploy_cloud.sh deploy    # Deploy now
#   ./deploy_cloud.sh status    # Check deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SPACE_DIR="./space"
HF_REPO="sohiyiy/birdsense"

case "$1" in
    setup)
        echo -e "${GREEN}🐦 BirdSense Cloud Setup${NC}"
        echo "=========================="
        
        # Check for HuggingFace CLI
        if ! command -v huggingface-cli &> /dev/null; then
            echo "Installing huggingface_hub..."
            pip install huggingface_hub
        fi
        
        # Login
        echo ""
        echo -e "${YELLOW}Step 1: Login to HuggingFace${NC}"
        echo "Get your token at: https://huggingface.co/settings/tokens"
        huggingface-cli login
        
        # Create space directory with required files
        echo ""
        echo -e "${YELLOW}Step 2: Preparing Space files${NC}"
        mkdir -p "$SPACE_DIR"
        
        # Copy cloud version as main app
        cp app_cloud.py "$SPACE_DIR/app.py"
        cp prompts.py "$SPACE_DIR/"
        cp feedback.py "$SPACE_DIR/"
        cp requirements_cloud.txt "$SPACE_DIR/requirements.txt"
        
        echo "✅ Space files prepared in $SPACE_DIR/"
        
        # GitHub Actions setup reminder
        echo ""
        echo -e "${YELLOW}Step 3: Enable Auto-Deploy${NC}"
        echo "Add this secret to your GitHub repo:"
        echo "  Settings → Secrets → Actions → New secret"
        echo "  Name: HF_TOKEN"
        echo "  Value: (your HuggingFace token)"
        echo ""
        echo "Then push to main branch - it will auto-deploy!"
        ;;
        
    deploy)
        echo -e "${GREEN}🚀 Deploying to HuggingFace Spaces${NC}"
        
        # Prepare space files
        mkdir -p "$SPACE_DIR"
        cp app_cloud.py "$SPACE_DIR/app.py"
        cp prompts.py "$SPACE_DIR/"
        cp feedback.py "$SPACE_DIR/"
        cp requirements_cloud.txt "$SPACE_DIR/requirements.txt"
        
        # Deploy
        cd "$SPACE_DIR"
        python << 'EOF'
from huggingface_hub import HfApi, upload_folder
import os

api = HfApi()

# Create if needed
try:
    api.create_repo(
        repo_id="sohiyiy/birdsense",
        repo_type="space",
        space_sdk="gradio",
        private=False
    )
    print("Created new space")
except Exception as e:
    print(f"Space exists or error: {e}")

# Upload
upload_folder(
    folder_path=".",
    repo_id="sohiyiy/birdsense",
    repo_type="space",
    ignore_patterns=["__pycache__", "*.pyc", ".git*", "venv"]
)
print("✅ Deployed!")
EOF
        
        echo ""
        echo -e "${GREEN}✅ Deployed to:${NC}"
        echo "   https://huggingface.co/spaces/$HF_REPO"
        ;;
        
    status)
        echo -e "${GREEN}📊 Deployment Status${NC}"
        echo ""
        echo "HuggingFace Space: https://huggingface.co/spaces/$HF_REPO"
        echo ""
        echo "To set API keys in the Space:"
        echo "1. Go to Space Settings"
        echo "2. Add Repository secrets:"
        echo "   - TOGETHER_API_KEY (free at together.ai)"
        echo "   - Or REPLICATE_API_TOKEN (free at replicate.com)"
        ;;
        
    *)
        echo "🐦 BirdSense Cloud Deployment"
        echo ""
        echo "Usage:"
        echo "  $0 setup   - First-time setup (login, prepare files)"
        echo "  $0 deploy  - Deploy to HuggingFace Spaces now"
        echo "  $0 status  - Show deployment status"
        echo ""
        echo "For auto-deploy on GitHub push:"
        echo "  Add HF_TOKEN secret to your GitHub repo"
        echo "  Push to main branch"
        ;;
esac

