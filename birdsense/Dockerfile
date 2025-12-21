# 🐦 BirdSense - Production Container
# Developed by Soham
#
# Uses LiteLLM API for LLM (GPT-4o Vision + GPT-5.2 Text)
# BirdNET included for audio analysis
#
# Build: docker build -t birdsense .
# Run:   docker run -p 7860:7860 birdsense

FROM python:3.12-slim

LABEL maintainer="Soham"
LABEL description="BirdSense - AI Bird Identification (Production)"

# Install system dependencies
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

# Copy application code
COPY app.py prompts.py confusion_rules.py feedback.py ./

# Create directories
RUN mkdir -p /app/feedback_data/logs /app/feedback_data/samples

# Expose port
EXPOSE 7860

# Environment variables
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"
ENV PYTHONUNBUFFERED=1
ENV TF_CPP_MIN_LOG_LEVEL=2

# LiteLLM config (can be overridden at runtime)
ENV LITELLM_API_BASE="https://litellm-rm.zycus.net"
ENV LITELLM_VISION_MODEL="gpt-4o-201124-payg-eastus"
ENV LITELLM_TEXT_MODEL="gpt-5.2-payg-global"

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Run
CMD ["python", "app.py"]
