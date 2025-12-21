# 🐦 BirdSense - Production Cloud Container
# Developed by Soham
#
# Uses LiteLLM API for LLM (GPT-4o Vision + GPT-5.2 Text)
# BirdNET included for audio analysis (gold standard)
#
# Build: docker build -t birdsense .
# Run:   docker run -p 7860:7860 -e LITELLM_API_KEY=your-key birdsense

FROM python:3.12-slim

LABEL maintainer="Soham"
LABEL description="BirdSense - Hybrid AI Bird Identification"

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (refactored architecture)
COPY app.py providers.py analysis.py ./
COPY prompts.py confusion_rules.py feedback.py ./
COPY env-template.txt ./

# Create directories for feedback data
RUN mkdir -p /app/feedback_data/logs /app/feedback_data/samples

# Expose port
EXPOSE 7860

# Environment variables
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"
ENV PYTHONUNBUFFERED=1
ENV TF_CPP_MIN_LOG_LEVEL=2

# Azure OpenAI config - set API key at runtime via -e or Cloud Run env vars
# DO NOT hardcode API keys here!
ENV IS_AZURE="true"
ENV LITELLM_API_BASE="https://zycus-ptu.azure-api.net/ptu-intakemanagement"
ENV AZURE_DEPLOYMENT="gpt4o-130524"
ENV AZURE_API_VERSION="2024-02-15-preview"
ENV LITELLM_VISION_MODEL="gpt-4o"
ENV LITELLM_TEXT_MODEL="gpt-4o"
# LITELLM_API_KEY must be provided at runtime

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Run
CMD ["python", "app.py"]
