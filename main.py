"""Main application entry point."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import REGISTRY, Counter, Histogram, start_http_server
from pythonjsonlogger import jsonlogger

from src.api.routes import router
from src.config import settings
from src.core.fonts import font_manager


# Configure JSON logging
def setup_logging():
    """Configure JSON formatted logging."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Avoid adding duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


# Prometheus metrics - avoid duplicate registration on reload
_metrics = {}


def get_or_create_metric(metric_class, name, description, **kwargs):
    """Get existing metric or create new one."""
    if name in _metrics:
        return _metrics[name]

    # Check if already in registry
    if name in REGISTRY._names_to_collectors:
        collector = REGISTRY._names_to_collectors[name]
        _metrics[name] = collector
        return collector

    metric = metric_class(name, description, **kwargs)
    _metrics[name] = metric
    return metric


RENDER_DURATION = get_or_create_metric(
    Histogram,
    'render_duration_seconds',
    'Time spent rendering images',
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

RENDER_ERRORS = get_or_create_metric(
    Counter,
    'render_errors_total',
    'Total number of render errors',
    labelnames=['error_type']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Emoji Renderer Service")

    # Initialize font manager
    font_manager.initialize(settings.font_directory)
    logger.info(f"Loaded {len(font_manager.list_fonts())} fonts")

    # Start Prometheus metrics server on separate port
    start_http_server(settings.metrics_port)
    logger.info(f"Metrics server started on port {settings.metrics_port}")

    yield

    # Shutdown
    logger.info("Shutting down Emoji Renderer Service")


# Create FastAPI application
app = FastAPI(
    title="Emoji Renderer Service",
    description="Text-to-Image/Animation rendering service for Misskey Custom Emojis.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
