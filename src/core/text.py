"""Text rendering module - handles text drawing, sizing, and effects."""

import logging
import math
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
MAX_VERTICAL_SCALE = 2.0
MIN_VERTICAL_SCALE = 0.5
SHADOW_OFFSET = 4
SHADOW_BLUR = 5


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
        self, text: str, font_id: str, canvas_size: int = SQUARE_SIZE, outline_width: int = 0
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
        available_size = max(1, canvas_size - (PADDING * 2) - (outline_width * 2))

        low = MIN_FONT_SIZE
        high = MAX_FONT_SIZE
        best_size = MIN_FONT_SIZE

        while low <= high:
            mid = (low + high) // 2
            font = font_manager.get_font(font_id, mid)

            text_width, _ = self._get_text_dimensions(text, font, outline_width)

            if text_width <= available_size:
                best_size = mid
                low = mid + 1
            else:
                high = mid - 1

        best_size = self._apply_square_vertical_scale_guard(
            text, font_id, best_size, available_size, outline_width
        )

        return best_size

    def calculate_banner_dimensions(
        self, text: str, font_id: str, font_size: int = 64, outline_width: int = 0
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
        self, text: str, font: ImageFont.FreeTypeFont
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
        temp_img = Image.new("RGBA", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)

        bbox = temp_draw.multiline_textbbox((0, 0), text, font=font)
        return (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3]))

    def _get_text_dimensions(
        self, text: str, font: ImageFont.FreeTypeFont, outline_width: int = 0
    ) -> tuple[int, int]:
        """Measure text dimensions using the ink bbox plus outline width."""
        bbox = self._get_multiline_bbox(text, font)
        text_width = max(0, (bbox[2] - bbox[0]) + (outline_width * 2))
        text_height = max(0, (bbox[3] - bbox[1]) + (outline_width * 2))
        return text_width, text_height

    def _apply_square_vertical_scale_guard(
        self,
        text: str,
        font_id: str,
        font_size: int,
        available_size: int,
        outline_width: int,
    ) -> int:
        """Adjust the font size so the square-mode vertical scale stays bounded."""
        font = font_manager.get_font(font_id, font_size)
        _, text_height = self._get_text_dimensions(text, font, outline_width)

        if text_height == 0:
            return font_size

        vertical_scale = available_size / text_height
        min_height = math.ceil(available_size / MAX_VERTICAL_SCALE)
        max_height = math.floor(available_size / MIN_VERTICAL_SCALE)

        if vertical_scale >= MAX_VERTICAL_SCALE:
            # Try to increase height without exceeding the width constraint.
            low = font_size
            high = MAX_FONT_SIZE
            adjusted_size = font_size

            while low <= high:
                mid = (low + high) // 2
                font = font_manager.get_font(font_id, mid)
                text_width, text_height = self._get_text_dimensions(text, font, outline_width)

                if text_width <= available_size and text_height >= min_height:
                    adjusted_size = mid
                    low = mid + 1
                elif text_width > available_size:
                    high = mid - 1
                else:
                    low = mid + 1

            return adjusted_size

        if vertical_scale <= MIN_VERTICAL_SCALE:
            low = MIN_FONT_SIZE
            high = font_size
            adjusted_size = font_size

            while low <= high:
                mid = (low + high) // 2
                font = font_manager.get_font(font_id, mid)
                _, text_height = self._get_text_dimensions(text, font, outline_width)

                if text_height <= max_height:
                    adjusted_size = mid
                    low = mid + 1
                else:
                    high = mid - 1

            return adjusted_size

        return font_size

    def _draw_text(
        self,
        canvas: Image.Image,
        text: str,
        font: ImageFont.FreeTypeFont,
        x: int,
        y: int,
        style: TextStyle,
        layout: LayoutConfig,
        custom_text_color: tuple[int, int, int] | None = None,
    ) -> None:
        """Draw text onto the provided canvas."""
        draw = ImageDraw.Draw(canvas)

        text_color = custom_text_color or hex_to_rgb(style.text_color)
        outline_color = hex_to_rgb(style.outline_color) if style.outline_width > 0 else None

        if style.outline_width > 0 and outline_color:
            draw.multiline_text(
                (x, y),
                text,
                font=font,
                fill=(*text_color, 255),
                stroke_width=style.outline_width,
                stroke_fill=(*outline_color, 255),
                align=layout.alignment,
            )
        else:
            draw.multiline_text(
                (x, y), text, font=font, fill=(*text_color, 255), align=layout.alignment
            )

    def _render_tight_text_image(
        self,
        text: str,
        style: TextStyle,
        layout: LayoutConfig,
        font: ImageFont.FreeTypeFont,
        custom_text_color: tuple[int, int, int] | None = None,
    ) -> Image.Image | None:
        """Render text to a tightly-cropped image based on visible pixels."""
        bbox = self._get_multiline_bbox(text, font)
        text_width, text_height = self._get_text_dimensions(text, font, style.outline_width)
        shadow_margin = SHADOW_OFFSET + (SHADOW_BLUR * 2) if style.shadow else 0

        temp_width = max(1, text_width + (shadow_margin * 2))
        temp_height = max(1, text_height + (shadow_margin * 2))
        temp_canvas = Image.new("RGBA", (temp_width, temp_height), (0, 0, 0, 0))

        x = shadow_margin - bbox[0] + style.outline_width
        y = shadow_margin - bbox[1] + style.outline_width

        if style.shadow:
            temp_canvas = self._add_shadow(temp_canvas, text, font, x, y, style.outline_width)

        self._draw_text(temp_canvas, text, font, x, y, style, layout, custom_text_color)

        alpha_bbox = temp_canvas.getchannel("A").getbbox()
        if alpha_bbox is None:
            return None

        cropped = temp_canvas.crop(alpha_bbox)
        if cropped.width == 0 or cropped.height == 0:
            return None

        return cropped

    def render_text(
        self,
        text: str,
        style: TextStyle,
        layout: LayoutConfig,
        custom_text_color: tuple[int, int, int] | None = None,
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
        if layout.mode == "square":
            font_size = self.calculate_font_size_for_square(
                text, style.font_id, SQUARE_SIZE, style.outline_width
            )
            font = font_manager.get_font(style.font_id, font_size)
            available_size = max(1, SQUARE_SIZE - (PADDING * 2) - (style.outline_width * 2))
            canvas = Image.new("RGBA", (SQUARE_SIZE, SQUARE_SIZE), (0, 0, 0, 0))
            text_image = self._render_tight_text_image(
                text, style, layout, font, custom_text_color=custom_text_color
            )

            if text_image is None:
                return canvas

            resized = text_image.resize(
                (available_size, available_size), resample=Image.Resampling.LANCZOS
            )
            offset = (
                (SQUARE_SIZE - available_size) // 2,
                (SQUARE_SIZE - available_size) // 2,
            )
            canvas.alpha_composite(resized, dest=offset)
            return canvas

        font_size = 64  # Fixed font size for banner
        canvas_width, canvas_height = self.calculate_banner_dimensions(
            text, style.font_id, font_size, style.outline_width
        )
        font = font_manager.get_font(style.font_id, font_size)
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

        bbox = self._get_multiline_bbox(text, font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        if layout.alignment == "left":
            x = PADDING + style.outline_width
        elif layout.alignment == "right":
            x = canvas_width - text_width - PADDING - style.outline_width
        else:  # center
            x = (canvas_width - text_width) // 2

        y = (canvas_height - text_height) // 2 - bbox[1]

        if style.shadow:
            canvas = self._add_shadow(canvas, text, font, x, y, style.outline_width)

        self._draw_text(canvas, text, font, x, y, style, layout, custom_text_color)

        return canvas

    def _add_shadow(
        self,
        canvas: Image.Image,
        text: str,
        font: ImageFont.FreeTypeFont,
        x: int,
        y: int,
        outline_width: int,
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
        # Create shadow layer
        shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)

        # Draw shadow text (black, semi-transparent)
        shadow_draw.multiline_text(
            (x + SHADOW_OFFSET, y + SHADOW_OFFSET),
            text,
            font=font,
            fill=(0, 0, 0, 128),
            stroke_width=outline_width,
            stroke_fill=(0, 0, 0, 128),
        )

        # Apply Gaussian blur
        shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))

        # Composite shadow under canvas
        result = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        result = Image.alpha_composite(result, shadow)
        result = Image.alpha_composite(result, canvas)

        return result


# Global text renderer instance
text_renderer = TextRenderer()
