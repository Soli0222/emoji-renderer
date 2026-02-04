"""Unit tests for API schemas."""

import pytest
from pydantic import ValidationError

from src.api.schemas import (
    HEX_COLOR_PATTERN,
    ErrorResponse,
    FontSchema,
    HealthResponse,
    LayoutSchema,
    MotionSchema,
    RenderRequest,
    StyleSchema,
)


class TestLayoutSchema:
    """Tests for LayoutSchema."""

    def test_default_values(self):
        """Test default layout values."""
        layout = LayoutSchema()
        assert layout.mode == "square"
        assert layout.alignment == "center"

    def test_valid_modes(self):
        """Test valid layout modes."""
        for mode in ["square", "banner"]:
            layout = LayoutSchema(mode=mode)  # type: ignore[arg-type]
            assert layout.mode == mode

    def test_invalid_mode(self):
        """Test invalid layout mode raises error."""
        with pytest.raises(ValidationError):
            LayoutSchema(mode="invalid")  # type: ignore[arg-type]

    def test_valid_alignments(self):
        """Test valid alignment values."""
        for alignment in ["left", "center", "right"]:
            layout = LayoutSchema(alignment=alignment)  # type: ignore[arg-type]
            assert layout.alignment == alignment

    def test_invalid_alignment(self):
        """Test invalid alignment raises error."""
        with pytest.raises(ValidationError):
            LayoutSchema(alignment="invalid")  # type: ignore[arg-type]


class TestStyleSchema:
    """Tests for StyleSchema."""

    def test_required_fields(self):
        """Test required fields must be provided."""
        with pytest.raises(ValidationError):
            StyleSchema()  # type: ignore[call-arg]

    def test_minimal_valid_style(self):
        """Test minimal valid style."""
        style = StyleSchema(fontId="test_font", textColor="#FF0000")
        assert style.fontId == "test_font"
        assert style.textColor == "#FF0000"

    def test_default_values(self):
        """Test default values are set."""
        style = StyleSchema(fontId="test_font", textColor="#FF0000")
        assert style.outlineColor == "#FFFFFF"
        assert style.outlineWidth == 0
        assert style.shadow is False

    def test_valid_hex_colors(self):
        """Test valid hex color formats."""
        valid_colors = ["#FF0000", "#ff0000", "#F00", "#abc", "#ABCDEF"]
        for color in valid_colors:
            style = StyleSchema(fontId="font", textColor=color)
            assert style.textColor == color

    def test_invalid_hex_colors(self):
        """Test invalid hex colors raise error."""
        invalid_colors = ["FF0000", "#GGGGGG", "#12345", "red", "#1234567"]
        for color in invalid_colors:
            with pytest.raises(ValidationError):
                StyleSchema(fontId="font", textColor=color)

    def test_outline_width_range(self):
        """Test outline width validation."""
        # Valid range
        for width in [0, 10, 20]:
            style = StyleSchema(fontId="font", textColor="#FFF", outlineWidth=width)
            assert style.outlineWidth == width

        # Invalid: below minimum
        with pytest.raises(ValidationError):
            StyleSchema(fontId="font", textColor="#FFF", outlineWidth=-1)

        # Invalid: above maximum
        with pytest.raises(ValidationError):
            StyleSchema(fontId="font", textColor="#FFF", outlineWidth=21)

    def test_outline_color_validation(self):
        """Test outline color is validated."""
        with pytest.raises(ValidationError):
            StyleSchema(fontId="font", textColor="#FFF", outlineColor="invalid")


class TestMotionSchema:
    """Tests for MotionSchema."""

    def test_default_values(self):
        """Test default motion values."""
        motion = MotionSchema()
        assert motion.type == "none"
        assert motion.intensity == "medium"
        assert motion.speed == 1.0

    def test_valid_motion_types(self):
        """Test valid motion types."""
        for motion_type in ["none", "shake", "spin", "bounce", "gaming"]:
            motion = MotionSchema(type=motion_type)  # type: ignore[arg-type]
            assert motion.type == motion_type

    def test_invalid_motion_type(self):
        """Test invalid motion type raises error."""
        with pytest.raises(ValidationError):
            MotionSchema(type="invalid")  # type: ignore[arg-type]

    def test_valid_intensity_levels(self):
        """Test valid intensity levels."""
        for intensity in ["low", "medium", "high"]:
            motion = MotionSchema(intensity=intensity)  # type: ignore[arg-type]
            assert motion.intensity == intensity

    def test_invalid_intensity(self):
        """Test invalid intensity raises error."""
        with pytest.raises(ValidationError):
            MotionSchema(intensity="invalid")  # type: ignore[arg-type]

    def test_speed_range(self):
        """Test speed validation range."""
        # Valid range
        for speed in [0.1, 1.0, 2.5, 5.0]:
            motion = MotionSchema(speed=speed)
            assert motion.speed == speed

        # Invalid: below minimum
        with pytest.raises(ValidationError):
            MotionSchema(speed=0.05)

        # Invalid: above maximum
        with pytest.raises(ValidationError):
            MotionSchema(speed=5.5)


class TestRenderRequest:
    """Tests for RenderRequest schema."""

    @pytest.fixture
    def valid_style(self):
        """Create a valid style for testing."""
        return StyleSchema(fontId="test_font", textColor="#FF0000")

    def test_required_fields(self, valid_style):
        """Test required fields."""
        request = RenderRequest(text="Test", style=valid_style)
        assert request.text == "Test"
        assert request.style == valid_style

    def test_default_layout(self, valid_style):
        """Test default layout is applied."""
        request = RenderRequest(text="Test", style=valid_style)
        assert request.layout.mode == "square"
        assert request.layout.alignment == "center"

    def test_default_motion(self, valid_style):
        """Test default motion is applied."""
        request = RenderRequest(text="Test", style=valid_style)
        assert request.motion.type == "none"

    def test_empty_text_rejected(self, valid_style):
        """Test empty text is rejected."""
        with pytest.raises(ValidationError):
            RenderRequest(text="", style=valid_style)

    def test_whitespace_only_text_rejected(self, valid_style):
        """Test whitespace-only text is rejected."""
        with pytest.raises(ValidationError):
            RenderRequest(text="   ", style=valid_style)

    def test_text_length_limit(self, valid_style):
        """Test text length limit."""
        # Get the max length from settings
        from src.config import settings

        max_len = settings.max_text_length

        # Valid: at limit
        request = RenderRequest(text="a" * max_len, style=valid_style)
        assert len(request.text) == max_len

        # Invalid: exceeds limit
        with pytest.raises(ValidationError):
            RenderRequest(text="a" * (max_len + 1), style=valid_style)

    def test_multiline_text(self, valid_style):
        """Test multiline text is accepted."""
        request = RenderRequest(text="Line1\nLine2", style=valid_style)
        assert "\n" in request.text

    def test_full_request(self):
        """Test full request with all fields."""
        request = RenderRequest(
            text="Test",
            layout=LayoutSchema(mode="banner", alignment="left"),
            style=StyleSchema(
                fontId="font",
                textColor="#FF0000",
                outlineColor="#000000",
                outlineWidth=5,
                shadow=True,
            ),
            motion=MotionSchema(type="shake", intensity="high", speed=2.0),
        )
        assert request.layout.mode == "banner"
        assert request.style.outlineWidth == 5
        assert request.motion.type == "shake"


class TestFontSchema:
    """Tests for FontSchema."""

    def test_required_fields(self):
        """Test required fields."""
        font = FontSchema(id="test_font", name="Test Font")
        assert font.id == "test_font"
        assert font.name == "Test Font"

    def test_default_categories(self):
        """Test default categories is empty list."""
        font = FontSchema(id="test", name="Test")
        assert font.categories == []

    def test_valid_categories(self):
        """Test valid category values."""
        font = FontSchema(
            id="test", name="Test", categories=["serif", "sans-serif", "handwritten", "display"]
        )
        assert len(font.categories) == 4

    def test_custom_category(self):
        """Test custom category is accepted."""
        font = FontSchema(id="test", name="Test", categories=["custom"])
        assert font.categories == ["custom"]


class TestHealthResponse:
    """Tests for HealthResponse."""

    def test_default_status(self):
        """Test default status is ok."""
        response = HealthResponse()
        assert response.status == "ok"

    def test_custom_status(self):
        """Test custom status."""
        response = HealthResponse(status="healthy")
        assert response.status == "healthy"


class TestErrorResponse:
    """Tests for ErrorResponse."""

    def test_required_detail(self):
        """Test detail is required."""
        with pytest.raises(ValidationError):
            ErrorResponse()  # type: ignore[call-arg]

    def test_error_message(self):
        """Test error message is stored."""
        error = ErrorResponse(detail="Something went wrong")
        assert error.detail == "Something went wrong"


class TestHexColorPattern:
    """Tests for HEX color regex pattern."""

    def test_valid_six_char_uppercase(self):
        """Test valid 6-char uppercase hex."""
        assert HEX_COLOR_PATTERN.match("#FF0000") is not None
        assert HEX_COLOR_PATTERN.match("#ABCDEF") is not None

    def test_valid_six_char_lowercase(self):
        """Test valid 6-char lowercase hex."""
        assert HEX_COLOR_PATTERN.match("#ff0000") is not None
        assert HEX_COLOR_PATTERN.match("#abcdef") is not None

    def test_valid_three_char(self):
        """Test valid 3-char hex."""
        assert HEX_COLOR_PATTERN.match("#FFF") is not None
        assert HEX_COLOR_PATTERN.match("#abc") is not None

    def test_invalid_no_hash(self):
        """Test invalid hex without hash."""
        assert HEX_COLOR_PATTERN.match("FF0000") is None

    def test_invalid_length(self):
        """Test invalid length."""
        assert HEX_COLOR_PATTERN.match("#FF00") is None
        assert HEX_COLOR_PATTERN.match("#FF00001") is None

    def test_invalid_chars(self):
        """Test invalid characters."""
        assert HEX_COLOR_PATTERN.match("#GGGGGG") is None
