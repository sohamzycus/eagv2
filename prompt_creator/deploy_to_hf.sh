#!/bin/bash
# Deploy to Hugging Face Spaces
# Usage: ./deploy_to_hf.sh <username> <space_name>

set -e

USERNAME=${1:-"your-username"}
SPACE_NAME=${2:-"workflow-agent-creator"}
SPACE_URL="https://huggingface.co/spaces/${USERNAME}/${SPACE_NAME}"

echo "🚀 Deploying to Hugging Face Spaces"
echo "   Space: ${SPACE_URL}"
echo ""

# Check if git-lfs is installed
if ! command -v git-lfs &> /dev/null; then
    echo "Installing git-lfs..."
    git lfs install
fi

# Create temp directory
TEMP_DIR=$(mktemp -d)
echo "📁 Working in: ${TEMP_DIR}"

# Clone or create the space
if git clone "https://huggingface.co/spaces/${USERNAME}/${SPACE_NAME}" "${TEMP_DIR}/space" 2>/dev/null; then
    echo "✅ Cloned existing space"
else
    echo "📝 Creating new space directory"
    mkdir -p "${TEMP_DIR}/space"
    cd "${TEMP_DIR}/space"
    git init
    git remote add origin "https://huggingface.co/spaces/${USERNAME}/${SPACE_NAME}"
fi

cd "${TEMP_DIR}/space"

# Get source directory
SOURCE_DIR="$(dirname "$0")"
if [ "$SOURCE_DIR" = "." ]; then
    SOURCE_DIR="$(pwd)"
fi

# Copy files
echo "📋 Copying files..."

# Core application files
cp -r "${SOURCE_DIR}/core" .
cp -r "${SOURCE_DIR}/domain" .
cp -r "${SOURCE_DIR}/ui" .
cp "${SOURCE_DIR}/app.py" .
cp "${SOURCE_DIR}/__init__.py" . 2>/dev/null || touch __init__.py
cp "${SOURCE_DIR}/requirements.txt" .

# Use HF-specific README
cp "${SOURCE_DIR}/README_HF.md" README.md

# Create .gitattributes for LFS
cat > .gitattributes << 'EOF'
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.gif filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
EOF

# Commit and push
echo "📤 Pushing to Hugging Face..."
git add .
git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"

echo ""
echo "Ready to push. Run the following commands:"
echo ""
echo "  cd ${TEMP_DIR}/space"
echo "  git push origin main"
echo ""
echo "Or push with credentials:"
echo "  git push https://USER:TOKEN@huggingface.co/spaces/${USERNAME}/${SPACE_NAME} main"
echo ""
echo "🌐 Your space will be available at: ${SPACE_URL}"
