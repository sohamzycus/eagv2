#!/bin/bash
# ============================================
# Deploy to Hugging Face Spaces
# ============================================

set -e

# Configuration
HF_SPACE_NAME="${HF_SPACE_NAME:-prompt-creator}"
HF_USERNAME="${HF_USERNAME:-your-username}"

echo "============================================"
echo "Deploying Prompt Creator to HuggingFace Spaces"
echo "============================================"
echo ""

# Check if huggingface-cli is installed
if ! command -v huggingface-cli &> /dev/null; then
    echo "Installing huggingface_hub..."
    pip install huggingface_hub
fi

# Check if logged in
if ! huggingface-cli whoami &> /dev/null; then
    echo "Please login to HuggingFace:"
    huggingface-cli login
fi

# Get username
HF_USERNAME=$(huggingface-cli whoami | head -1)
echo "Logged in as: $HF_USERNAME"

# Create Space if it doesn't exist
SPACE_REPO="$HF_USERNAME/$HF_SPACE_NAME"
echo ""
echo "Creating/updating Space: $SPACE_REPO"

# Clone or create the space
if [ -d "hf_space" ]; then
    rm -rf hf_space
fi

# Try to clone existing space, or create new one
if huggingface-cli repo info "$SPACE_REPO" --repo-type space &> /dev/null; then
    echo "Space exists, cloning..."
    git clone "https://huggingface.co/spaces/$SPACE_REPO" hf_space
else
    echo "Creating new Space..."
    huggingface-cli repo create "$HF_SPACE_NAME" --type space --space-sdk gradio
    git clone "https://huggingface.co/spaces/$SPACE_REPO" hf_space
fi

# Copy files to space
echo "Copying files..."
cp -r prompt_creator hf_space/
cp app.py hf_space/
cp requirements.txt hf_space/
cp README_HF.md hf_space/README.md

# Create .gitattributes for LFS
cat > hf_space/.gitattributes << 'EOF'
*.bin filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
EOF

# Push to HuggingFace
cd hf_space
git add .
git commit -m "Deploy Prompt Creator" || true
git push

echo ""
echo "============================================"
echo "✅ Deployment Complete!"
echo "============================================"
echo ""
echo "Your Space is available at:"
echo "https://huggingface.co/spaces/$SPACE_REPO"
echo ""
echo "To add your Azure OpenAI credentials:"
echo "1. Go to: https://huggingface.co/spaces/$SPACE_REPO/settings"
echo "2. Add these secrets:"
echo "   - AZURE_OPENAI_API_KEY"
echo "   - AZURE_OPENAI_ENDPOINT"
echo "   - AZURE_OPENAI_DEPLOYMENT"
echo ""

