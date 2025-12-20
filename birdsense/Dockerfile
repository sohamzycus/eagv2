# 🐦 BirdSense - AI Bird Identification
# Developed by Soham
#
# Single codebase - auto-detects:
#   - Local: Uses Ollama (if available)
#   - Cloud: Uses Groq API (FREE, no credit card)
#
# Build: docker build -t birdsense .
# Run:   docker run -p 7860:7860 -e GROQ_API_KEY=xxx birdsense

FROM python:3.12-slim

LABEL maintainer="Soham"
LABEL description="BirdSense - Hybrid AI Bird Identification System"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first for Docker layer caching
COPY requirements_cloud.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Run the application
CMD ["python", "app.py"]
