# MSPaint MCP Production v2 - PowerShell Runner
# Sets up environment and runs the demo

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MSPaint MCP Production v2 - Quick Start" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan

# Set the Google Gemini API key
$env:GOOGLE_API_KEY = "AIzaSyBomWfEWE4Usj9FVbWQs5NvNV2dMjuIiDs"
$env:GEMINI_API_KEY = "AIzaSyBomWfEWE4Usj9FVbWQs5NvNV2dMjuIiDs"

$apiKeyPreview = $env:GOOGLE_API_KEY.Substring(0, [Math]::Min(20, $env:GOOGLE_API_KEY.Length))
Write-Host "✅ API Key configured: $apiKeyPreview..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python is available: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install requirements if needed
Write-Host "📦 Installing/checking requirements..." -ForegroundColor Yellow
try {
    pip install -r requirements.txt
    Write-Host "✅ Requirements installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install requirements" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Run the setup and demo
Write-Host "🚀 Starting MSPaint MCP Demo..." -ForegroundColor Cyan
try {
    python setup_and_run.py
} catch {
    Write-Host "❌ Error running demo: $_" -ForegroundColor Red
}

Read-Host "Press Enter to exit"
