"""Unit tests for text rendering."""

from unittest.mock import patch

import pytest
from PIL import Image, ImageFont

from src.core.text import (
    DEFAULT_HEIGHT,
    MAX_FONT_SIZE,
    MIN_FONT_SIZE,
    PADDING,
    SQUARE_SIZE,
    LayoutConfig,
    TextRenderer,
    TextStyle,
)


class TestTextStyle:
    """Tests for TextStyle dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        style = TextStyle(font_id="test_font", text_color="#FF0000")
        assert style.font_id == "test_font"
        assert style.text_color == "#FF0000"
        assert style.outline_color == "#FFFFFF"
        assert style.outline_width == 0
        assert style.shadow is False

    def test_custom_values(self):
        """Test custom values are applied."""
        style = TextStyle(
            font_id="custom_font",
            text_color="#00FF00",
            outline_color="#0000FF",
            outline_width=5,
            shadow=True,
        )
        assert style.outline_color == "#0000FF"
        assert style.outline_width == 5
        assert style.shadow is True


class TestLayoutConfig:
    """Tests for LayoutConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        layout = LayoutConfig()
        assert layout.mode == "square"
        assert layout.alignment == "center"

    def test_custom_values(self):
        """Test custom values."""
        layout = LayoutConfig(mode="banner", alignment="left")
        assert layout.mode == "banner"
        assert layout.alignment == "left"


class TestTextRenderer:
    """Tests for TextRenderer class."""

    @pytest.fixture
    def renderer(self):
        """Create TextRenderer instance."""
        return TextRenderer()

    def test_get_multiline_bbox_single_line(self, renderer):
        """Test bounding box calculation for single line text."""
        # Use a real default font for testing
        default_font = ImageFont.load_default()

        bbox = renderer._get_multiline_bbox("Test", default_font)
        assert isinstance(bbox, tuple)
        assert len(bbox) == 4
        # bbox should be (left, top, right, bottom)
        assert bbox[2] > bbox[0]  # width > 0
        assert bbox[3] >= bbox[1]  # height >= 0

    def test_calculate_font_size_for_square_basic(self, renderer):
        """Test font size calculation returns valid size."""
        with patch("src.core.text.font_manager") as mock_fm:
            from PIL import ImageFont

            mock_fm.get_font.return_value = ImageFont.load_default()

            size = renderer.calculate_font_size_for_square("Test", "test_font", SQUARE_SIZE, 0)
            assert MIN_FONT_SIZE <= size <= MAX_FONT_SIZE

    def test_calculate_font_size_accounts_for_outline(self, renderer):
        """Test font size calculation accounts for outline width."""
        with patch("src.core.text.font_manager") as mock_fm:
            from PIL import ImageFont

            mock_fm.get_font.return_value = ImageFont.load_default()

            size_no_outline = renderer.calculate_font_size_for_square(
                "Test", "test_font", SQUARE_SIZE, 0
            )

            size_with_outline = renderer.calculate_font_size_for_square(
                "Test", "test_font", SQUARE_SIZE, 10
            )

            # With outline, available space is less, so font should be same or smaller
            assert size_with_outline <= size_no_outline

    def test_calculate_banner_dimensions(self, renderer):
        """Test banner dimension calculation."""
        with patch("src.core.text.font_manager") as mock_fm:
            from PIL import ImageFont

            mock_fm.get_font.return_value = ImageFont.load_default()

            width, height = renderer.calculate_banner_dimensions("Test Text", "test_font", 64, 0)

            # Width should accommodate text plus padding
            assert width > (PADDING * 2)
            # Height should accommodate text plus padding (dynamic sizing)
            assert height > (PADDING * 2)

    def test_render_text_square_mode(self, renderer):
        """Test rendering in square mode produces correct size image."""
        style = TextStyle(font_id="test_font", text_color="#FF0000")
        layout = LayoutConfig(mode="square", alignment="center")

        with patch("src.core.text.font_manager") as mock_fm:
            from PIL import ImageFont

            mock_fm.get_font.return_value = ImageFont.load_default()

            image = renderer.render_text("Test", style, layout)

            assert isinstance(image, Image.Image)
            assert image.size == (SQUARE_SIZE, SQUARE_SIZE)
            assert image.mode == "RGBA"

    def test_render_text_banner_mode(self, renderer):
        """Test rendering in banner mode produces dynamic width."""
        style = TextStyle(font_id="test_font", text_color="#FF0000")
        layout = LayoutConfig(mode="banner", alignment="center")

        with patch("src.core.text.font_manager") as mock_fm:
            from PIL import ImageFont

            mock_fm.get_font.return_value = ImageFont.load_default()

            image = renderer.render_text("Test Text", style, layout)

            assert isinstance(image, Image.Image)
            assert image.mode == "RGBA"

    def test_render_text_alignment_left(self, renderer):
        """Test left alignment positioning."""
        style = TextStyle(font_id="test_font", text_color="#FF0000")
        layout = LayoutConfig(mode="square", alignment="left")

        with patch("src.core.text.font_manager") as mock_fm:
            from PIL import ImageFont

            mock_fm.get_font.return_value = ImageFont.load_default()

            image = renderer.render_text("Test", style, layout)
            assert image is not None

    def test_render_text_alignment_right(self, renderer):
        """Test right alignment positioning."""
        style = TextStyle(font_id="test_font", text_color="#FF0000")
        layout = LayoutConfig(mode="square", alignment="right")

        with patch("src.core.text.font_manager") as mock_fm:
            from PIL import ImageFont

            mock_fm.get_font.return_value = ImageFont.load_default()

            image = renderer.render_text("Test", style, layout)
            assert image is not None

    def test_render_text_with_outline(self, renderer):
        """Test rendering with outline."""
        style = TextStyle(
            font_id="test_font", text_color="#FF0000", outline_color="#000000", outline_width=3
        )
        layout = LayoutConfig()

        with patch("src.core.text.font_manager") as mock_fm:
            from PIL import ImageFont

            mock_fm.get_font.return_value = ImageFont.load_default()

            image = renderer.render_text("Test", style, layout)
            assert image is not None

    def test_render_text_with_shadow(self, renderer):
        """Test rendering with shadow effect."""
        style = TextStyle(font_id="test_font", text_color="#FF0000", shadow=True)
        layout = LayoutConfig()

        with patch("src.core.text.font_manager") as mock_fm:
            from PIL import ImageFont

            mock_fm.get_font.return_value = ImageFont.load_default()

            image = renderer.render_text("Test", style, layout)
            assert image is not None
            assert image.mode == "RGBA"

    def test_render_text_with_custom_color(self, renderer):
        """Test rendering with custom text color override."""
        style = TextStyle(font_id="test_font", text_color="#FF0000")
        layout = LayoutConfig()
        custom_color = (0, 255, 0)

        with patch("src.core.text.font_manager") as mock_fm:
            from PIL import ImageFont

            mock_fm.get_font.return_value = ImageFont.load_default()

            image = renderer.render_text("Test", style, layout, custom_text_color=custom_color)
            assert image is not None

    def test_render_text_multiline(self, renderer):
        """Test rendering multiline text."""
        style = TextStyle(font_id="test_font", text_color="#FF0000")
        layout = LayoutConfig()

        with patch("src.core.text.font_manager") as mock_fm:
            from PIL import ImageFont

            mock_fm.get_font.return_value = ImageFont.load_default()

            image = renderer.render_text("Line 1\nLine 2", style, layout)
            assert image is not None

    def test_add_shadow_creates_blurred_layer(self, renderer):
        """Test shadow creation."""
        canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        default_font = ImageFont.load_default()

        result = renderer._add_shadow(canvas, "Test", default_font, 100, 100, 0)

        assert isinstance(result, Image.Image)
        assert result.mode == "RGBA"
        assert result.size == canvas.size


class TestTextRendererConstants:
    """Test module constants."""

    def test_square_size(self):
        """Test square size constant."""
        assert SQUARE_SIZE == 256

    def test_default_height(self):
        """Test default height constant."""
        assert DEFAULT_HEIGHT == 256

    def test_padding(self):
        """Test padding constant."""
        assert PADDING == 10

    def test_font_size_range(self):
        """Test font size range constants."""
        assert MIN_FONT_SIZE < MAX_FONT_SIZE
        assert MIN_FONT_SIZE > 0
