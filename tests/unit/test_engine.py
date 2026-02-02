"""Unit tests for rendering engine."""

from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from src.core.animation import MotionConfig, MotionType
from src.core.engine import RenderingEngine, RenderResult
from src.core.text import LayoutConfig, TextStyle


class TestRenderResult:
    """Tests for RenderResult dataclass."""

    def test_render_result_creation(self):
        """Test RenderResult dataclass creation."""
        result = RenderResult(
            data=b"test data",
            format="webp",
            size_bytes=9,
            render_time_ms=100.5
        )

        assert result.data == b"test data"
        assert result.format == "webp"
        assert result.size_bytes == 9
        assert result.render_time_ms == 100.5


class TestRenderingEngine:
    """Tests for RenderingEngine class."""

    @pytest.fixture
    def style(self):
        """Create a test style."""
        return TextStyle(
            font_id="test_font",
            text_color="#FF0000"
        )

    @pytest.fixture
    def layout(self):
        """Create a test layout."""
        return LayoutConfig(mode="square", alignment="center")

    @pytest.fixture
    def test_image(self):
        """Create a test image."""
        return Image.new('RGBA', (256, 256), (255, 0, 0, 255))

    def test_init(self):
        """Test engine initialization."""
        engine = RenderingEngine()
        assert engine.text_renderer is not None
        assert engine.animation_generator is not None

    def test_render_static_image(self, style, layout, test_image):
        """Test rendering a static (non-animated) image."""
        engine = RenderingEngine()
        motion = MotionConfig(type=MotionType.NONE)

        with patch('src.core.engine.font_manager') as mock_fm:
            mock_fm.font_exists.return_value = True
            engine.text_renderer = MagicMock()
            engine.text_renderer.render_text.return_value = test_image

            result = engine.render("Test", style, layout, motion)

        assert isinstance(result, RenderResult)
        assert result.format == "webp"
        assert result.size_bytes > 0
        assert result.render_time_ms >= 0

    def test_render_animated_shake(self, style, layout, test_image):
        """Test rendering shake animation."""
        engine = RenderingEngine()
        motion = MotionConfig(type=MotionType.SHAKE)

        with patch('src.core.engine.font_manager') as mock_fm:
            mock_fm.font_exists.return_value = True
            engine.text_renderer = MagicMock()
            engine.text_renderer.render_text.return_value = test_image
            engine.animation_generator = MagicMock()
            engine.animation_generator.generate_frames.return_value = [test_image] * 5

            result = engine.render("Test", style, layout, motion)

        assert result.format == "apng"

    def test_render_animated_spin(self, style, layout, test_image):
        """Test rendering spin animation."""
        engine = RenderingEngine()
        motion = MotionConfig(type=MotionType.SPIN)

        with patch('src.core.engine.font_manager') as mock_fm:
            mock_fm.font_exists.return_value = True
            engine.text_renderer = MagicMock()
            engine.text_renderer.render_text.return_value = test_image
            engine.animation_generator = MagicMock()
            engine.animation_generator.generate_frames.return_value = [test_image] * 5

            result = engine.render("Test", style, layout, motion)

        assert result.format == "apng"

    def test_render_animated_bounce(self, style, layout, test_image):
        """Test rendering bounce animation."""
        engine = RenderingEngine()
        motion = MotionConfig(type=MotionType.BOUNCE)

        with patch('src.core.engine.font_manager') as mock_fm:
            mock_fm.font_exists.return_value = True
            engine.text_renderer = MagicMock()
            engine.text_renderer.render_text.return_value = test_image
            engine.animation_generator = MagicMock()
            engine.animation_generator.generate_frames.return_value = [test_image] * 5

            result = engine.render("Test", style, layout, motion)

        assert result.format == "apng"

    def test_render_animated_gaming(self, style, layout, test_image):
        """Test rendering gaming (rainbow) animation."""
        engine = RenderingEngine()
        motion = MotionConfig(type=MotionType.GAMING)

        with patch('src.core.engine.font_manager') as mock_fm:
            mock_fm.font_exists.return_value = True
            engine.text_renderer = MagicMock()
            engine.text_renderer.render_text.return_value = test_image
            engine.animation_generator = MagicMock()
            engine.animation_generator.get_frame_count.return_value = 5

            result = engine.render("Test", style, layout, motion)

        assert result.format == "apng"

    def test_render_font_not_found(self, style, layout):
        """Test error when font not found."""
        engine = RenderingEngine()
        motion = MotionConfig(type=MotionType.NONE)

        with patch('src.core.engine.font_manager') as mock_fm:
            mock_fm.font_exists.return_value = False

            with pytest.raises(ValueError, match="Font not found"):
                engine.render("Test", style, layout, motion)

    def test_encode_webp(self):
        """Test WebP encoding."""
        engine = RenderingEngine()
        image = Image.new('RGBA', (256, 256), (255, 0, 0, 255))

        data = engine._encode_webp(image)

        assert isinstance(data, bytes)
        assert len(data) > 0
        # Check WebP magic bytes (RIFF....WEBP)
        assert data[:4] == b'RIFF'
        assert data[8:12] == b'WEBP'

    def test_encode_apng_single_frame(self):
        """Test APNG encoding with single frame."""
        engine = RenderingEngine()
        image = Image.new('RGBA', (256, 256), (255, 0, 0, 255))

        data = engine._encode_apng([image])

        assert isinstance(data, bytes)
        assert len(data) > 0
        # Check PNG magic bytes
        assert data[:8] == b'\x89PNG\r\n\x1a\n'

    def test_encode_apng_multiple_frames(self):
        """Test APNG encoding with multiple frames."""
        engine = RenderingEngine()
        frames = [
            Image.new('RGBA', (256, 256), (255, 0, 0, 255)),
            Image.new('RGBA', (256, 256), (0, 255, 0, 255)),
            Image.new('RGBA', (256, 256), (0, 0, 255, 255)),
        ]

        data = engine._encode_apng(frames)

        assert isinstance(data, bytes)
        assert len(data) > 0
        # Check PNG magic bytes
        assert data[:8] == b'\x89PNG\r\n\x1a\n'

    def test_encode_apng_empty_frames(self):
        """Test APNG encoding with empty frames list raises error."""
        engine = RenderingEngine()
        with pytest.raises(ValueError, match="No frames to encode"):
            engine._encode_apng([])

    def test_check_size_limit_within_limit(self):
        """Test size check when within limit."""
        engine = RenderingEngine()
        small_data = b"x" * 1000  # 1KB

        with patch('src.core.engine.settings') as mock_settings:
            mock_settings.max_image_size_kb = 10
            assert engine.check_size_limit(small_data) is True

    def test_check_size_limit_exceeds_limit(self):
        """Test size check when exceeding limit."""
        engine = RenderingEngine()
        large_data = b"x" * (2 * 1024 * 1024)  # 2MB

        with patch('src.core.engine.settings') as mock_settings:
            mock_settings.max_image_size_kb = 1024  # 1MB limit
            assert engine.check_size_limit(large_data) is False

    def test_check_size_limit_at_limit(self):
        """Test size check at exactly the limit."""
        engine = RenderingEngine()
        exact_data = b"x" * (1024 * 1024)  # Exactly 1MB

        with patch('src.core.engine.settings') as mock_settings:
            mock_settings.max_image_size_kb = 1024  # 1MB limit
            assert engine.check_size_limit(exact_data) is True

    def test_generate_gaming_frames(self, style, layout, test_image):
        """Test gaming frame generation."""
        engine = RenderingEngine()
        motion = MotionConfig(type=MotionType.GAMING, speed=1.0)

        engine.text_renderer = MagicMock()
        engine.text_renderer.render_text.return_value = test_image
        engine.animation_generator = MagicMock()
        engine.animation_generator.get_frame_count.return_value = 5

        frames = engine._generate_gaming_frames("Test", style, layout, motion)

        assert isinstance(frames, list)
        assert len(frames) == 5

    def test_render_returns_timing_info(self, style, layout, test_image):
        """Test render returns timing information."""
        engine = RenderingEngine()
        motion = MotionConfig(type=MotionType.NONE)

        with patch('src.core.engine.font_manager') as mock_fm:
            mock_fm.font_exists.return_value = True
            engine.text_renderer = MagicMock()
            engine.text_renderer.render_text.return_value = test_image

            result = engine.render("Test", style, layout, motion)

        assert result.render_time_ms >= 0


class TestRenderingEngineIntegration:
    """Integration tests for RenderingEngine with real dependencies."""

    @pytest.fixture
    def setup_fonts(self, tmp_path):
        """Setup font manager with a test font."""
        from src.core.fonts import FontManager

        # Reset singleton
        FontManager._instance = None
        manager = FontManager()

        # We can't easily add a real font, so we'll skip these tests
        # if no fonts are available
        return manager

    def test_render_pipeline_with_mocked_font(self):
        """Test full render pipeline with mocked font."""
        engine = RenderingEngine()

        with patch('src.core.engine.font_manager') as mock_fm, \
             patch.object(engine.text_renderer, 'render_text') as mock_render:

            mock_fm.font_exists.return_value = True
            mock_image = Image.new('RGBA', (256, 256), (255, 0, 0, 255))
            mock_render.return_value = mock_image

            style = TextStyle(font_id="test", text_color="#FF0000")
            layout = LayoutConfig()
            motion = MotionConfig(type=MotionType.NONE)

            result = engine.render("Test", style, layout, motion)

            assert isinstance(result, RenderResult)
            assert result.format == "webp"
