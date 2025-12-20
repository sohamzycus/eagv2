# 🐦 BirdSense - Full AI Bird Identification
# Developed by Soham
#
# Includes: BirdNET + TensorFlow + Ollama LLM
#
# Build: docker build -t birdsense .
# Run:   docker run -p 7860:7860 birdsense

FROM python:3.12-slim

LABEL maintainer="Soham"
LABEL description="BirdSense - Hybrid AI Bird Identification with BirdNET"

# Install system dependencies for TensorFlow + audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    libasound2-dev \
    portaudio19-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first for Docker layer caching
COPY requirements.txt .

# Install Python dependencies (includes TensorFlow + BirdNET)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY prompts.py .
COPY confusion_rules.py .
COPY feedback.py .

# Create feedback data directory
RUN mkdir -p /app/feedback_data/logs /app/feedback_data/samples

# Expose Gradio port
EXPOSE 7860

# Environment variables
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"
ENV PYTHONUNBUFFERED=1
ENV TF_CPP_MIN_LOG_LEVEL=2

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Run the application
CMD ["python", "app.py"]
