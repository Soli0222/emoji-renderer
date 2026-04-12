"""Unit tests for text rendering."""

import math
from unittest.mock import patch

import pytest
from PIL import Image, ImageFont

from src.core.fonts import font_manager
from src.core.text import (
    DEFAULT_HEIGHT,
    MAX_FONT_SIZE,
    MAX_VERTICAL_SCALE,
    MIN_FONT_SIZE,
    MIN_VERTICAL_SCALE,
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

    TEST_FONT_ID = "notosansjp_bold"

    @pytest.fixture
    def renderer(self):
        """Create TextRenderer instance."""
        return TextRenderer()

    @pytest.fixture
    def real_font_manager(self):
        """Initialize the bundled fonts for regression-style rendering tests."""
        font_manager.initialize("assets/fonts")
        return font_manager

    def _get_alpha_bbox(self, image):
        """Return the alpha-channel bbox for visible pixels."""
        return image.getchannel("A").getbbox()

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

    def test_calculate_font_size_for_square_limits_vertical_scale_for_tall_text(
        self, renderer, real_font_manager
    ):
        """Test square-mode sizing keeps tall multiline text within scale bounds."""
        font_size = renderer.calculate_font_size_for_square(
            "あ\nい\nう\nえ\nお", self.TEST_FONT_ID, SQUARE_SIZE, 0
        )
        font = real_font_manager.get_font(self.TEST_FONT_ID, font_size)
        _, text_height = renderer._get_text_dimensions("あ\nい\nう\nえ\nお", font, 0)
        available_size = SQUARE_SIZE - (PADDING * 2)
        vertical_scale = available_size / text_height

        assert MIN_FONT_SIZE <= font_size <= MAX_FONT_SIZE
        assert vertical_scale >= MIN_VERTICAL_SCALE

    def test_square_vertical_scale_guard_can_raise_height_when_room_remains(self, renderer):
        """Test the upper vertical-scale guard can increase font size when width headroom exists."""

        class DummyFont:
            def __init__(self, size):
                self.size = size

        with patch("src.core.text.MAX_FONT_SIZE", 400), patch("src.core.text.font_manager") as mock_fm:
            mock_fm.get_font.side_effect = lambda _font_id, size: DummyFont(size)

            def fake_dimensions(_text, font, outline_width=0):
                width = min(font.size // 2, 180 - (outline_width * 2))
                height = max(1, math.ceil(font.size / 3))
                return width + (outline_width * 2), height + (outline_width * 2)

            renderer._get_text_dimensions = fake_dimensions

            font_size = renderer._apply_square_vertical_scale_guard("narrow", "test_font", 200, 236, 0)
            available_size = SQUARE_SIZE - (PADDING * 2)
            _, text_height = renderer._get_text_dimensions("narrow", DummyFont(font_size), 0)
            vertical_scale = available_size / text_height

            assert font_size > 200
            assert vertical_scale <= MAX_VERTICAL_SCALE

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

    def test_render_text_square_mode_stretches_single_character(self, renderer, real_font_manager):
        """Test square mode stretches a short single-line string to fill the drawable square."""
        style = TextStyle(font_id=self.TEST_FONT_ID, text_color="#FF0000")
        layout = LayoutConfig(mode="square", alignment="center")

        image = renderer.render_text("あ", style, layout)
        bbox = self._get_alpha_bbox(image)
        available_size = SQUARE_SIZE - (PADDING * 2) - (style.outline_width * 2)

        assert bbox is not None
        assert (bbox[2] - bbox[0]) >= available_size - 2
        assert (bbox[3] - bbox[1]) >= available_size - 2

    def test_render_text_square_mode_multiline_fits_drawable_square(
        self, renderer, real_font_manager
    ):
        """Test square mode keeps multiline text within the drawable square."""
        style = TextStyle(font_id=self.TEST_FONT_ID, text_color="#FF0000")
        layout = LayoutConfig(mode="square", alignment="center")

        image = renderer.render_text("あ\nい\nう\nえ\nお", style, layout)
        bbox = self._get_alpha_bbox(image)
        available_size = SQUARE_SIZE - (PADDING * 2) - (style.outline_width * 2)

        assert bbox is not None
        assert (bbox[2] - bbox[0]) <= available_size
        assert (bbox[3] - bbox[1]) <= available_size
        assert (bbox[3] - bbox[1]) >= available_size - 2

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

    @pytest.mark.parametrize("text", ["", " ", "\n"])
    def test_render_text_square_mode_returns_transparent_canvas_for_empty_inputs(
        self, renderer, real_font_manager, text
    ):
        """Test square mode returns a transparent canvas when no ink is produced."""
        style = TextStyle(font_id=self.TEST_FONT_ID, text_color="#FF0000")
        layout = LayoutConfig(mode="square", alignment="center")

        image = renderer.render_text(text, style, layout)

        assert image.size == (SQUARE_SIZE, SQUARE_SIZE)
        assert self._get_alpha_bbox(image) is None

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

    def test_vertical_scale_range(self):
        """Test vertical scale constants."""
        assert MIN_VERTICAL_SCALE < MAX_VERTICAL_SCALE
