# Base image - Python Alpine
FROM python:3.13.11-alpine3.23

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies for Pillow and fonts
RUN apk add --no-cache \
    # Pillow dependencies
    jpeg-dev \
    zlib-dev \
    libwebp-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    harfbuzz-dev \
    fribidi-dev \
    # Build tools for NumPy/Pillow
    build-base \
    python3-dev \
    # Fonts
    font-noto-cjk

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Copy fonts (SIL Open Font License)
COPY assets/fonts/ ./assets/fonts/

# Create non-root user
RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -s /bin/sh -D appuser && \
    chown -R appuser:appgroup /app

USER appuser

# Expose ports (app: 8109, metrics: 9109)
EXPOSE 8109 9109

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8109/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8109"]
