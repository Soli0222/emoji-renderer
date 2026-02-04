"""Unit tests for font management."""

from unittest.mock import MagicMock, patch

import pytest
from PIL import ImageFont


class TestFontManager:
    """Tests for FontManager class."""

    @pytest.fixture
    def font_manager(self):
        """Create a fresh FontManager instance for testing."""
        # Reset singleton for testing
        from src.core.fonts import FontManager

        FontManager._instance = None
        manager = FontManager()
        return manager

    @pytest.fixture
    def temp_font_dir(self, tmp_path):
        """Create a temporary font directory with dummy font files."""
        # Note: We can't create real font files easily, so we'll mock the loading
        return tmp_path

    def test_singleton_pattern(self):
        """Test that FontManager follows singleton pattern."""
        from src.core.fonts import FontManager

        FontManager._instance = None

        manager1 = FontManager()
        manager2 = FontManager()
        assert manager1 is manager2

    def test_generate_font_id(self, font_manager):
        """Test font ID generation from filenames."""
        assert font_manager._generate_font_id("Noto Sans JP") == "noto_sans_jp"
        assert font_manager._generate_font_id("My-Font-Name") == "my_font_name"
        assert font_manager._generate_font_id("UPPERCASE") == "uppercase"
        assert font_manager._generate_font_id("with__double") == "with_double"

    def test_generate_font_name(self, font_manager):
        """Test human-readable font name generation."""
        assert font_manager._generate_font_name("noto_sans_jp") == "Noto Sans Jp"
        assert font_manager._generate_font_name("my-font-name") == "My Font Name"
        assert font_manager._generate_font_name("simple") == "Simple"

    def test_detect_categories_serif(self, font_manager):
        """Test serif category detection."""
        categories = font_manager._detect_categories("NotoSerif-Regular")
        assert "serif" in categories
        assert "sans-serif" not in categories

    def test_detect_categories_sans_serif(self, font_manager):
        """Test sans-serif category detection."""
        categories = font_manager._detect_categories("NotoSansJP-Bold")
        assert "sans-serif" in categories
        assert "serif" not in categories

    def test_detect_categories_handwritten(self, font_manager):
        """Test handwritten category detection."""
        categories = font_manager._detect_categories("Beautiful-Handwriting")
        assert "handwritten" in categories

        categories = font_manager._detect_categories("Cursive-Script")
        assert "handwritten" in categories

    def test_detect_categories_display(self, font_manager):
        """Test display category detection."""
        categories = font_manager._detect_categories("Fancy-Display-Font")
        assert "display" in categories

    def test_detect_categories_default(self, font_manager):
        """Test default category is sans-serif."""
        categories = font_manager._detect_categories("RegularFont")
        assert "sans-serif" in categories

    def test_font_exists_returns_false_for_unknown(self, font_manager):
        """Test font_exists returns False for unknown fonts."""
        assert font_manager.font_exists("nonexistent_font") is False

    def test_list_fonts_empty_initially(self, font_manager):
        """Test list_fonts returns empty list before initialization."""
        fonts = font_manager.list_fonts()
        assert fonts == []

    def test_get_font_info_returns_none_for_unknown(self, font_manager):
        """Test get_font_info returns None for unknown fonts."""
        info = font_manager.get_font_info("nonexistent_font")
        assert info is None

    def test_get_font_raises_for_unknown(self, font_manager):
        """Test get_font raises ValueError for unknown fonts."""
        with pytest.raises(ValueError, match="Font not found"):
            font_manager.get_font("nonexistent_font", 32)

    def test_initialize_creates_missing_directory(self, font_manager, tmp_path):
        """Test initialize creates font directory if missing."""
        non_existent_dir = tmp_path / "fonts" / "new"
        font_manager.initialize(str(non_existent_dir))
        assert non_existent_dir.exists()

    def test_initialize_loads_fonts(self, font_manager, tmp_path):
        """Test initialize scans and loads font files."""
        # Create dummy font file (won't be loadable, but tests scanning)
        font_file = tmp_path / "TestFont.ttf"
        font_file.write_bytes(b"dummy font data")

        # Mock ImageFont.truetype to avoid actually loading the font
        with patch.object(ImageFont, "truetype", return_value=MagicMock()):
            font_manager.initialize(str(tmp_path))

            # Check font was detected
            assert font_manager.font_exists("testfont")

            # Check font info
            info = font_manager.get_font_info("testfont")
            assert info is not None
            assert info.id == "testfont"
            assert info.name == "Testfont"

    def test_initialize_supports_multiple_extensions(self, font_manager, tmp_path):
        """Test initialize supports various font file extensions."""
        extensions = [".ttf", ".otf", ".ttc", ".woff", ".woff2"]

        for ext in extensions:
            font_file = tmp_path / f"Font{ext}{ext}"
            font_file.write_bytes(b"dummy font data")

        with patch.object(ImageFont, "truetype", return_value=MagicMock()):
            font_manager.initialize(str(tmp_path))

            # Check all extensions were loaded
            fonts = font_manager.list_fonts()
            assert len(fonts) >= len(extensions)

    def test_get_font_caching(self, font_manager, tmp_path):
        """Test font loading is cached."""
        # Create a font file
        font_file = tmp_path / "CacheTest.ttf"
        font_file.write_bytes(b"dummy font data")

        mock_font = MagicMock()

        with patch.object(ImageFont, "truetype", return_value=mock_font) as mock_truetype:
            font_manager.initialize(str(tmp_path))

            # Get the same font twice
            font_manager.get_font("cachetest", 32)
            font_manager.get_font("cachetest", 32)

            # truetype should only be called once for the same size
            calls = [c for c in mock_truetype.call_args_list if c[1].get("size") == 32]
            assert len(calls) == 1

            # But different sizes should trigger new loads
            font_manager.get_font("cachetest", 64)
            calls = [c for c in mock_truetype.call_args_list if c[1].get("size") == 64]
            assert len(calls) == 1


class TestFontInfo:
    """Tests for FontInfo dataclass."""

    def test_font_info_creation(self):
        """Test FontInfo dataclass creation."""
        from src.core.fonts import FontInfo

        info = FontInfo(
            id="test_font", name="Test Font", path="/path/to/font.ttf", categories=["sans-serif"]
        )

        assert info.id == "test_font"
        assert info.name == "Test Font"
        assert info.path == "/path/to/font.ttf"
        assert info.categories == ["sans-serif"]
