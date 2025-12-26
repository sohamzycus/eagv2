# Dockerfile for Prompt Creator
# Optimized for Hugging Face Spaces

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7861
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

# Copy the prompt_creator package
COPY core/ /app/prompt_creator/core/
COPY domain/ /app/prompt_creator/domain/
COPY ui/ /app/prompt_creator/ui/
COPY __init__.py /app/prompt_creator/

# Copy entry points
COPY app.py /app/
COPY main.py /app/

# Create __init__.py files to ensure proper package structure
RUN touch /app/__init__.py

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose Gradio port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7861/ || exit 1

# Run the application
CMD ["python", "app.py"]

