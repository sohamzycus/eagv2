# Dockerfile for Procurement Workflow Agent Creator
# Optimized for Hugging Face Spaces (free tier)

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860
ENV PYTHONPATH=/app

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY core/ /app/core/
COPY domain/ /app/domain/
COPY ui/ /app/ui/
COPY __init__.py /app/

# Copy entry point
COPY app.py /app/

# Create non-root user for security (required by HF Spaces)
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

# Expose port (HF Spaces uses 7860)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Run the application
CMD ["python", "app.py"]
