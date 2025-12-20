# BirdSense - AI Bird Identification
# Developed by Soham
#
# Build: docker build -t birdsense .
# Run: docker run -p 7860:7860 birdsense

FROM python:3.12-slim

LABEL maintainer="Soham"
LABEL description="BirdSense - Hybrid AI Bird Identification System"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY prompts.py .
COPY confusion_rules.py .
COPY README.md .

# Expose Gradio port
EXPOSE 7860

# Environment variables
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"
ENV OLLAMA_HOST="host.docker.internal:11434"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Run the application
CMD ["python", "app.py"]
