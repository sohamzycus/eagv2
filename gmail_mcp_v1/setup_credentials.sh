#!/bin/bash
# Gmail MCP Credential Setup
# This script creates symbolic links to credential files stored securely outside the repository

SECURE_DIR="../gmail_credentials_secure"
REPO_DIR="."

echo "🔐 Setting up Gmail MCP credentials from secure location..."

# Check if secure directory exists
if [ ! -d "$SECURE_DIR" ]; then
    echo "❌ Secure credential directory not found: $SECURE_DIR"
    echo "💡 Please run the authentication setup first"
    exit 1
fi

# Create symbolic links for credential files
echo "🔗 Creating symbolic links to secure credential files..."

files=("credentials.json" "token.json" "gmail_session.json" "llm_gmail_session.json")

for file in "${files[@]}"; do
    if [ -f "$SECURE_DIR/$file" ]; then
        if [ -L "$REPO_DIR/$file" ] || [ -f "$REPO_DIR/$file" ]; then
            rm -f "$REPO_DIR/$file"
        fi
        ln -s "$SECURE_DIR/$file" "$REPO_DIR/$file"
        echo "  ✅ Linked $file"
    else
        echo "  ⚠️  $file not found in secure directory"
    fi
done

echo ""
echo "🎉 Credential setup complete!"
echo "📁 Secure files location: $(realpath $SECURE_DIR)"
echo "🔗 Symbolic links created in repository"
echo ""
echo "✅ You can now run:"
echo "   python multi_step_research_gmail.py"
echo "   python test_gmail_direct.py"
