"""API routes - FastAPI endpoint definitions."""

import logging
import uuid

from fastapi import APIRouter, HTTPException, Response

from src.api.schemas import ErrorResponse, FontSchema, HealthResponse, RenderRequest
from src.config import settings
from src.core.animation import Intensity, MotionConfig, MotionType
from src.core.engine import rendering_engine
from src.core.fonts import font_manager
from src.core.text import LayoutConfig, TextStyle

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the health status of the service.",
)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok")


@router.get(
    "/fonts",
    response_model=list[FontSchema],
    summary="List available fonts",
    description="Returns a list of installed fonts available for rendering.",
)
async def list_fonts():
    """List all available fonts."""
    fonts = font_manager.list_fonts()
    return [FontSchema(id=font.id, name=font.name, categories=font.categories) for font in fonts]


@router.post(
    "/generate",
    summary="Generate Emoji Image",
    description="Renders a static WebP or animated APNG based on the request parameters.",
    responses={
        200: {
            "description": "Image generated successfully.",
            "content": {
                "image/webp": {"schema": {"type": "string", "format": "binary"}},
                "image/apng": {"schema": {"type": "string", "format": "binary"}},
            },
        },
        400: {
            "description": "Bad Request (e.g., output size exceeds limit)",
            "model": ErrorResponse,
        },
        422: {
            "description": "Validation Error (e.g., invalid hex code, unknown font ID)",
            "model": ErrorResponse,
        },
        500: {"description": "Rendering Engine Error", "model": ErrorResponse},
    },
)
async def generate_emoji(request: RenderRequest):
    """Generate an emoji image or animation."""
    request_id = str(uuid.uuid4())[:8]

    logger.info(
        "Generate request",
        extra={
            "requestId": request_id,
            "text_length": len(request.text),
            "font_id": request.style.fontId,
            "motion_type": request.motion.type,
        },
    )

    # Validate font exists
    if not font_manager.font_exists(request.style.fontId):
        logger.warning(f"Font not found: {request.style.fontId}", extra={"requestId": request_id})
        raise HTTPException(status_code=422, detail=f"Font not found: {request.style.fontId}")

    try:
        # Convert request to internal models
        style = TextStyle(
            font_id=request.style.fontId,
            text_color=request.style.textColor,
            outline_color=request.style.outlineColor,
            outline_width=request.style.outlineWidth,
            shadow=request.style.shadow,
        )

        layout = LayoutConfig(mode=request.layout.mode, alignment=request.layout.alignment)

        motion = MotionConfig(
            type=MotionType(request.motion.type),
            intensity=Intensity(request.motion.intensity),
            speed=request.motion.speed,
        )

        # Render the image
        result = rendering_engine.render(
            text=request.text, style=style, layout=layout, motion=motion
        )

        # Check size limit
        if not rendering_engine.check_size_limit(result.data):
            logger.warning(
                f"Output size exceeds limit: {result.size_bytes} bytes",
                extra={"requestId": request_id},
            )
            raise HTTPException(
                status_code=400,
                detail=f"Output size ({result.size_bytes / 1024:.1f}KB) exceeds limit ({settings.max_image_size_kb}KB)",
            )

        # Determine content type
        if result.format == "webp":
            media_type = "image/webp"
        else:
            media_type = "image/apng"

        logger.info(
            "Generate success",
            extra={
                "requestId": request_id,
                "latency_ms": result.render_time_ms,
                "output_format": result.format,
                "output_size_bytes": result.size_bytes,
            },
        )

        return Response(content=result.data, media_type=media_type)

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}", extra={"requestId": request_id})
        raise HTTPException(status_code=422, detail=str(e)) from None

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.exception(f"Rendering error: {str(e)}", extra={"requestId": request_id})
        raise HTTPException(status_code=500, detail="Internal rendering error") from e
