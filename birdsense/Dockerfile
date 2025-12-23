# 🐦 BirdSense - Production Cloud Container
# Developed by Soham
#
# Includes both Gradio UI and REST API
# Uses Azure OpenAI for LLM (GPT-4o Vision + Text)
# BirdNET included for audio analysis (gold standard)
#
# Build: docker build -t birdsense .
# 
# Run modes:
#   Gradio UI: docker run -p 7860:7860 -e LITELLM_API_KEY=xxx birdsense
#   REST API:  docker run -p 8000:8000 -e RUN_MODE=api -e LITELLM_API_KEY=xxx birdsense
#   Both:      docker run -p 7860:7860 -p 8000:8000 -e RUN_MODE=both -e LITELLM_API_KEY=xxx birdsense

FROM python:3.12-slim

LABEL maintainer="Soham"
LABEL description="BirdSense - Hybrid AI Bird Identification (UI + API)"

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libsndfile1 \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (refactored architecture)
COPY app.py providers.py analysis.py ./
COPY prompts.py confusion_rules.py feedback.py ./
COPY audio_vision.py enhanced_prompts.py ./
COPY bird_dataset.py research_tools.py ebird_integration.py ./
COPY enhanced_analysis.py ./
COPY env-template.txt ./

# Copy API module
COPY api/ ./api/

# Create directories for feedback data
RUN mkdir -p /app/feedback_data/logs /app/feedback_data/samples

# Create startup script
RUN echo '#!/bin/bash\n\
if [ "$RUN_MODE" = "api" ]; then\n\
    echo "🐦 Starting BirdSense REST API on port 8000..."\n\
    exec uvicorn api.main:app --host 0.0.0.0 --port 8000\n\
elif [ "$RUN_MODE" = "both" ]; then\n\
    echo "🐦 Starting BirdSense (Gradio + API)..."\n\
    uvicorn api.main:app --host 0.0.0.0 --port 8000 &\n\
    exec python app.py\n\
else\n\
    echo "🐦 Starting BirdSense Gradio UI on port 7860..."\n\
    exec python app.py\n\
fi' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 7860 8000

# Environment variables
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"
ENV PYTHONUNBUFFERED=1
ENV TF_CPP_MIN_LOG_LEVEL=2
ENV RUN_MODE="gradio"

# Azure OpenAI config - set API key at runtime via -e or Cloud Run env vars
# DO NOT hardcode API keys here!
ENV IS_AZURE="true"
ENV LITELLM_API_BASE="https://zycus-ptu.azure-api.net/ptu-intakemanagement"
ENV AZURE_DEPLOYMENT="gpt4o-130524"
ENV AZURE_API_VERSION="2024-02-15-preview"
ENV LITELLM_VISION_MODEL="gpt-4o"
ENV LITELLM_TEXT_MODEL="gpt-4o"
# LITELLM_API_KEY must be provided at runtime

# Health check (checks both ports if running both)
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || curl -f http://localhost:8000/health || exit 1

# Run
CMD ["/app/start.sh"]
