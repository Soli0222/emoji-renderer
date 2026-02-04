"""Text rendering module - handles text drawing, sizing, and effects."""

import logging
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.core.fonts import font_manager
from src.utils.color import hex_to_rgb

logger = logging.getLogger(__name__)


# Default canvas settings
DEFAULT_HEIGHT = 256
SQUARE_SIZE = 256
MIN_FONT_SIZE = 10
MAX_FONT_SIZE = 200
PADDING = 10


@dataclass
class TextStyle:
    """Text styling options."""
    font_id: str
    text_color: str
    outline_color: str = "#FFFFFF"
    outline_width: int = 0
    shadow: bool = False


@dataclass
class LayoutConfig:
    """Layout configuration."""
    mode: str = "square"  # "square" or "banner"
    alignment: str = "center"  # "left", "center", "right"


class TextRenderer:
    """Handles text rendering with various styles and effects."""

    def __init__(self):
        """Initialize the text renderer."""
        pass

    def calculate_font_size_for_square(
        self,
        text: str,
        font_id: str,
        canvas_size: int = SQUARE_SIZE,
        outline_width: int = 0
    ) -> int:
        """
        Calculate the maximum font size that fits text within a square canvas.
        Uses binary search for efficiency.

        Args:
            text: Text to render
            font_id: Font identifier
            canvas_size: Size of the square canvas
            outline_width: Width of outline (reduces available space)

        Returns:
            Maximum font size that fits
        """
        available_size = canvas_size - (PADDING * 2) - (outline_width * 2)

        low = MIN_FONT_SIZE
        high = MAX_FONT_SIZE
        best_size = MIN_FONT_SIZE

        while low <= high:
            mid = (low + high) // 2
            font = font_manager.get_font(font_id, mid)

            # Calculate text bounding box
            bbox = self._get_multiline_bbox(text, font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            if text_width <= available_size and text_height <= available_size:
                best_size = mid
                low = mid + 1
            else:
                high = mid - 1

        return best_size

    def calculate_banner_dimensions(
        self,
        text: str,
        font_id: str,
        font_size: int = 64,
        outline_width: int = 0
    ) -> tuple[int, int]:
        """
        Calculate canvas dimensions for banner mode.

        Args:
            text: Text to render
            font_id: Font identifier
            font_size: Fixed font size
            outline_width: Width of outline

        Returns:
            Tuple of (width, height)
        """
        font = font_manager.get_font(font_id, font_size)
        bbox = self._get_multiline_bbox(text, font)

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        width = text_width + (PADDING * 2) + (outline_width * 2)
        height = text_height + (PADDING * 2) + (outline_width * 2)

        return (width, height)

    def _get_multiline_bbox(
        self,
        text: str,
        font: ImageFont.FreeTypeFont
    ) -> tuple[int, int, int, int]:
        """
        Get bounding box for multiline text.

        Args:
            text: Text (may contain newlines)
            font: PIL ImageFont

        Returns:
            Bounding box as (left, top, right, bottom)
        """
        # Create a temporary image for measurement
        temp_img = Image.new('RGBA', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)

        bbox = temp_draw.multiline_textbbox((0, 0), text, font=font)
        return (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))

    def render_text(
        self,
        text: str,
        style: TextStyle,
        layout: LayoutConfig,
        custom_text_color: tuple[int, int, int] | None = None
    ) -> Image.Image:
        """
        Render text to an image with the specified style and layout.

        Args:
            text: Text to render
            style: TextStyle configuration
            layout: LayoutConfig configuration
            custom_text_color: Override text color (for gaming mode animation)

        Returns:
            PIL Image with rendered text
        """
        # Determine canvas size and font size based on mode
        if layout.mode == "square":
            font_size = self.calculate_font_size_for_square(
                text, style.font_id, SQUARE_SIZE, style.outline_width
            )
            canvas_width = SQUARE_SIZE
            canvas_height = SQUARE_SIZE
        else:  # banner mode
            font_size = 64  # Fixed font size for banner
            canvas_width, canvas_height = self.calculate_banner_dimensions(
                text, style.font_id, font_size, style.outline_width
            )

        # Create transparent canvas
        canvas = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))

        # Get font
        font = font_manager.get_font(style.font_id, font_size)

        # Calculate text position
        bbox = self._get_multiline_bbox(text, font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Horizontal alignment
        if layout.alignment == "left":
            x = PADDING + style.outline_width
        elif layout.alignment == "right":
            x = canvas_width - text_width - PADDING - style.outline_width
        else:  # center
            x = (canvas_width - text_width) // 2

        # Vertical center
        y = (canvas_height - text_height) // 2 - bbox[1]

        # Render shadow layer if enabled
        if style.shadow:
            canvas = self._add_shadow(canvas, text, font, x, y, style.outline_width)

        # Render text with outline
        draw = ImageDraw.Draw(canvas)

        # Parse colors
        text_color = custom_text_color or hex_to_rgb(style.text_color)
        outline_color = hex_to_rgb(style.outline_color) if style.outline_width > 0 else None

        # Draw text with stroke (outline)
        if style.outline_width > 0 and outline_color:
            draw.multiline_text(
                (x, y),
                text,
                font=font,
                fill=(*text_color, 255),
                stroke_width=style.outline_width,
                stroke_fill=(*outline_color, 255),
                align=layout.alignment
            )
        else:
            draw.multiline_text(
                (x, y),
                text,
                font=font,
                fill=(*text_color, 255),
                align=layout.alignment
            )

        return canvas

    def _add_shadow(
        self,
        canvas: Image.Image,
        text: str,
        font: ImageFont.FreeTypeFont,
        x: int,
        y: int,
        outline_width: int
    ) -> Image.Image:
        """
        Add a drop shadow behind the text.

        Args:
            canvas: Canvas image
            text: Text to render
            font: PIL ImageFont
            x: X position
            y: Y position
            outline_width: Outline width (affects shadow offset)

        Returns:
            Canvas with shadow added
        """
        shadow_offset = 4
        shadow_blur = 5

        # Create shadow layer
        shadow = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)

        # Draw shadow text (black, semi-transparent)
        shadow_draw.multiline_text(
            (x + shadow_offset, y + shadow_offset),
            text,
            font=font,
            fill=(0, 0, 0, 128),
            stroke_width=outline_width,
            stroke_fill=(0, 0, 0, 128)
        )

        # Apply Gaussian blur
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))

        # Composite shadow under canvas
        result = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        result = Image.alpha_composite(result, shadow)
        result = Image.alpha_composite(result, canvas)

        return result


# Global text renderer instance
text_renderer = TextRenderer()
