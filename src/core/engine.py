"""Rendering engine - orchestrates the entire rendering pipeline."""

import io
import logging
import time
from dataclasses import dataclass

from PIL import Image

from src.config import settings
from src.core.animation import (
    FRAME_DURATION_MS,
    MotionConfig,
    MotionType,
    animation_generator,
)
from src.core.fonts import font_manager
from src.core.text import LayoutConfig, TextStyle, text_renderer

logger = logging.getLogger(__name__)


@dataclass
class RenderResult:
    """Result of a render operation."""

    data: bytes
    format: str  # "webp" or "apng"
    size_bytes: int
    render_time_ms: float


class RenderingEngine:
    """Main rendering engine that orchestrates text rendering and animation."""

    def __init__(self):
        """Initialize the rendering engine."""
        self.text_renderer = text_renderer
        self.animation_generator = animation_generator

    def render(
        self, text: str, style: TextStyle, layout: LayoutConfig, motion: MotionConfig
    ) -> RenderResult:
        """
        Render an emoji image or animation.

        Args:
            text: Text to render
            style: Text styling options
            layout: Layout configuration
            motion: Motion/animation configuration

        Returns:
            RenderResult with image data and metadata

        Raises:
            ValueError: If font_id is not found or validation fails
        """
        start_time = time.time()

        # Validate font exists
        if not font_manager.font_exists(style.font_id):
            raise ValueError(f"Font not found: {style.font_id}")

        # Render base text
        base_image = self.text_renderer.render_text(text, style, layout)

        # Generate frames (single frame for static, multiple for animated)
        if motion.type == MotionType.NONE:
            frames = [base_image]
            output_format = "webp"
        elif motion.type == MotionType.GAMING:
            # Gaming mode needs to re-render text with different colors
            frames = self._generate_gaming_frames(text, style, layout, motion)
            output_format = "apng"
        else:
            # Other animations transform the base image
            frames = self.animation_generator.generate_frames(base_image, motion, style.text_color)
            output_format = "apng"

        # Encode output
        if output_format == "webp":
            data = self._encode_webp(frames[0])
        else:
            data = self._encode_apng(frames)

        render_time = (time.time() - start_time) * 1000

        return RenderResult(
            data=data, format=output_format, size_bytes=len(data), render_time_ms=render_time
        )

    def _generate_gaming_frames(
        self, text: str, style: TextStyle, layout: LayoutConfig, motion: MotionConfig
    ) -> list[Image.Image]:
        """
        Generate gaming (rainbow) frames by re-rendering with rotated hue.

        Args:
            text: Text to render
            style: Base text style
            layout: Layout configuration
            motion: Motion configuration

        Returns:
            List of frames
        """
        from src.utils.color import hex_to_rgb, rotate_hue

        frame_count = self.animation_generator.get_frame_count(motion.speed)
        base_rgb = hex_to_rgb(style.text_color)
        frames = []

        for i in range(frame_count):
            hue_shift = (360 / frame_count) * i
            new_color = rotate_hue(*base_rgb, hue_shift)

            # Re-render with new color
            frame = self.text_renderer.render_text(text, style, layout, custom_text_color=new_color)
            frames.append(frame)

        return frames

    def _encode_webp(self, image: Image.Image) -> bytes:
        """
        Encode image as WebP.

        Args:
            image: PIL Image

        Returns:
            WebP bytes
        """
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=90, lossless=False)
        return buffer.getvalue()

    def _encode_apng(self, frames: list[Image.Image]) -> bytes:
        """
        Encode frames as APNG.

        Args:
            frames: List of PIL Images

        Returns:
            APNG bytes
        """
        buffer = io.BytesIO()

        if len(frames) == 0:
            raise ValueError("No frames to encode")

        if len(frames) == 1:
            # Single frame - just save as PNG
            frames[0].save(buffer, format="PNG", optimize=True)
        else:
            # Multiple frames - save as APNG
            frames[0].save(
                buffer,
                format="PNG",
                save_all=True,
                append_images=frames[1:],
                duration=FRAME_DURATION_MS,
                loop=0,  # Infinite loop
                optimize=True,
            )

        return buffer.getvalue()

    def check_size_limit(self, data: bytes) -> bool:
        """
        Check if output size is within limits.

        Args:
            data: Output bytes

        Returns:
            True if within limit, False otherwise
        """
        size_kb = len(data) / 1024
        return size_kb <= settings.max_image_size_kb


# Global rendering engine instance
rendering_engine = RenderingEngine()
