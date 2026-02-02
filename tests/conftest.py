"""Pytest configuration and fixtures."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Reset FontManager singleton
    from src.core.fonts import FontManager
    FontManager._instance = None
    FontManager._fonts = {}
    FontManager._font_cache = {}
    yield
    # Cleanup after test
    FontManager._instance = None
    FontManager._fonts = {}
    FontManager._font_cache = {}


@pytest.fixture
def test_font_dir(tmp_path):
    """Create a temporary font directory."""
    font_dir = tmp_path / "fonts"
    font_dir.mkdir()
    return font_dir


@pytest.fixture
def mock_settings():
    """Mock application settings."""
    with patch('src.config.settings') as mock:
        mock.log_level = "INFO"
        mock.max_text_length = 20
        mock.max_image_size_kb = 1024
        mock.default_font_id = "test_font"
        mock.font_directory = "./assets/fonts"
        mock.host = "0.0.0.0"
        mock.port = 8109
        mock.metrics_port = 9109
        yield mock


@pytest.fixture
def sample_image():
    """Create a sample RGBA image for testing."""
    from PIL import Image
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    # Draw a simple colored square
    for x in range(50, 206):
        for y in range(50, 206):
            img.putpixel((x, y), (255, 128, 64, 255))
    return img


@pytest.fixture
def sample_transparent_image():
    """Create a fully transparent image for testing."""
    from PIL import Image
    return Image.new('RGBA', (256, 256), (0, 0, 0, 0))


@pytest.fixture
def mock_font():
    """Create a mock PIL ImageFont."""
    mock = MagicMock()
    mock.getbbox.return_value = (0, 0, 100, 50)
    return mock


# Markers for test categorization
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Tests that are slow to run")
