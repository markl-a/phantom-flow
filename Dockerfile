# Multi-stage build for AI Automation Framework
# Stage 1: Builder
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    # For OCR and image processing
    tesseract-ocr \
    tesseract-ocr-chi-tra \
    tesseract-ocr-chi-sim \
    # For browser automation
    chromium \
    chromium-driver \
    # For video processing
    ffmpeg \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY ai_automation_framework/ ./ai_automation_framework/
COPY examples/ ./examples/
COPY tests/ ./tests/
COPY setup.py .
COPY README.md .
COPY .env.example .env

# Install the package
RUN pip install --no-cache-dir -e .

# Create directories for data persistence
RUN mkdir -p /app/data /app/logs /app/cache

# Expose ports
# 8000: FastAPI/Web service
# 8501: Streamlit demos
# 8080: Alternative web port
EXPOSE 8000 8501 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import ai_automation_framework; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "ai_automation_framework"]
