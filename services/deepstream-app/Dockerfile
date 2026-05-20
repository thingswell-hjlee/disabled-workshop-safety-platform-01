# DeepStream 8-Channel Safety Pipeline
# Platform 1.0 - Edge AI Inference Server
#
# Build: docker build -t safety-deepstream-app .
# Run (GPU): docker run --gpus all -e DEEPSTREAM_MOCK_MODE=false safety-deepstream-app
# Run (Mock): docker run -e DEEPSTREAM_MOCK_MODE=true safety-deepstream-app

# --- GPU Mode: Use NVIDIA DeepStream base image ---
FROM nvcr.io/nvidia/deepstream:7.0-triton-multiarch AS gpu-base

# --- Mock Mode: Use lightweight Python image ---
FROM python:3.11-slim AS mock-base

# --- Final image (use build arg to select) ---
ARG MODE=mock
FROM ${MODE}-base

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ /app/src/
COPY configs/ /app/configs/

# Create directories
RUN mkdir -p /models/active/pgie /models/staged /models/rollback /data/clips

# Default environment variables
ENV SITE_ID=SITE-001 \
    DEEPSTREAM_MOCK_MODE=true \
    MOCK_EVENT_INTERVAL_SEC=5.0 \
    HEALTHCHECK_PORT=8010 \
    REDIS_HOST=redis \
    REDIS_PORT=6379 \
    REDIS_STREAM_NAME=stream:ds-events \
    MODEL_VERSION=v1.0.0-tao-ds \
    MODEL_ENGINE_PATH=/models/active/pgie/model.engine \
    MODEL_LABELS_PATH=/models/active/pgie/labels.txt \
    MAX_CHANNELS=8 \
    BATCH_SIZE=8 \
    GPU_ID=0 \
    LOG_LEVEL=INFO \
    CAMERAS_CONFIG_PATH=/app/config/cameras.json

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

EXPOSE 8010

# Run the application
CMD ["python", "-m", "src"]
