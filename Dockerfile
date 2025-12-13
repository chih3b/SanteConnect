# SanteConnect Backend - Medical AI Assistant
# Multi-stage build for optimized image size

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies (Tesseract OCR, OpenCV deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-ara \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY main.py .
COPY config.py .
COPY fast_query.py .
COPY cache_manager.py .
COPY agent_langgraph.py .
COPY services/ ./services/
COPY data/ ./data/

# Note: EasyOCR models (~200MB) will be downloaded on first use at runtime
# This avoids build failures due to network issues

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /root/.EasyOCR 2>/dev/null || true
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV ESPRIT_API_KEY=sk-e16d16a054744585bfb2ef09bb52315c

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
