"""Unit tests for color utilities."""

import pytest

from src.utils.color import (
    hex_to_rgb,
    hsl_to_rgb,
    rgb_to_hex,
    rgb_to_hsl,
    rotate_hue,
    validate_hex_color,
)


class TestHexToRgb:
    """Tests for hex_to_rgb function."""

    def test_standard_six_char_hex(self):
        """Test standard 6-character hex color."""
        assert hex_to_rgb("#FF0000") == (255, 0, 0)
        assert hex_to_rgb("#00FF00") == (0, 255, 0)
        assert hex_to_rgb("#0000FF") == (0, 0, 255)
        assert hex_to_rgb("#FFFFFF") == (255, 255, 255)
        assert hex_to_rgb("#000000") == (0, 0, 0)

    def test_lowercase_hex(self):
        """Test lowercase hex colors."""
        assert hex_to_rgb("#ff0000") == (255, 0, 0)
        assert hex_to_rgb("#abcdef") == (171, 205, 239)

    def test_three_char_shorthand(self):
        """Test 3-character shorthand hex colors."""
        assert hex_to_rgb("#F00") == (255, 0, 0)
        assert hex_to_rgb("#0F0") == (0, 255, 0)
        assert hex_to_rgb("#00F") == (0, 0, 255)
        assert hex_to_rgb("#FFF") == (255, 255, 255)
        assert hex_to_rgb("#ABC") == (170, 187, 204)

    def test_without_hash(self):
        """Test hex colors without # prefix."""
        assert hex_to_rgb("FF0000") == (255, 0, 0)
        assert hex_to_rgb("abc") == (170, 187, 204)

    def test_invalid_hex_length(self):
        """Test invalid hex color length raises ValueError."""
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("#FF00")
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("#FF00001")

    def test_invalid_hex_characters(self):
        """Test invalid hex characters raise ValueError."""
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("#GGGGGG")
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("#XYZ123")


class TestRgbToHex:
    """Tests for rgb_to_hex function."""

    def test_basic_colors(self):
        """Test basic color conversions."""
        assert rgb_to_hex(255, 0, 0) == "#FF0000"
        assert rgb_to_hex(0, 255, 0) == "#00FF00"
        assert rgb_to_hex(0, 0, 255) == "#0000FF"
        assert rgb_to_hex(255, 255, 255) == "#FFFFFF"
        assert rgb_to_hex(0, 0, 0) == "#000000"

    def test_mixed_values(self):
        """Test mixed RGB values."""
        assert rgb_to_hex(128, 64, 32) == "#804020"
        assert rgb_to_hex(171, 205, 239) == "#ABCDEF"


class TestRgbToHsl:
    """Tests for rgb_to_hsl function."""

    def test_pure_red(self):
        """Test pure red conversion."""
        h, s, lightness = rgb_to_hsl(255, 0, 0)
        assert h == pytest.approx(0.0, abs=1)
        assert s == pytest.approx(1.0, abs=0.01)
        assert lightness == pytest.approx(0.5, abs=0.01)

    def test_pure_green(self):
        """Test pure green conversion."""
        h, s, lightness = rgb_to_hsl(0, 255, 0)
        assert h == pytest.approx(120.0, abs=1)
        assert s == pytest.approx(1.0, abs=0.01)
        assert lightness == pytest.approx(0.5, abs=0.01)

    def test_pure_blue(self):
        """Test pure blue conversion."""
        h, s, lightness = rgb_to_hsl(0, 0, 255)
        assert h == pytest.approx(240.0, abs=1)
        assert s == pytest.approx(1.0, abs=0.01)
        assert lightness == pytest.approx(0.5, abs=0.01)

    def test_white(self):
        """Test white (no saturation)."""
        h, s, lightness = rgb_to_hsl(255, 255, 255)
        assert s == pytest.approx(0.0, abs=0.01)
        assert lightness == pytest.approx(1.0, abs=0.01)

    def test_black(self):
        """Test black."""
        h, s, lightness = rgb_to_hsl(0, 0, 0)
        assert s == pytest.approx(0.0, abs=0.01)
        assert lightness == pytest.approx(0.0, abs=0.01)

    def test_gray(self):
        """Test gray (no saturation)."""
        h, s, lightness = rgb_to_hsl(128, 128, 128)
        assert s == pytest.approx(0.0, abs=0.01)
        assert lightness == pytest.approx(0.5, abs=0.02)


class TestHslToRgb:
    """Tests for hsl_to_rgb function."""

    def test_pure_red(self):
        """Test pure red conversion."""
        assert hsl_to_rgb(0, 1.0, 0.5) == (255, 0, 0)

    def test_pure_green(self):
        """Test pure green conversion."""
        assert hsl_to_rgb(120, 1.0, 0.5) == (0, 255, 0)

    def test_pure_blue(self):
        """Test pure blue conversion."""
        assert hsl_to_rgb(240, 1.0, 0.5) == (0, 0, 255)

    def test_white(self):
        """Test white (full lightness)."""
        r, g, b = hsl_to_rgb(0, 0, 1.0)
        assert r == 255
        assert g == 255
        assert b == 255

    def test_black(self):
        """Test black (no lightness)."""
        r, g, b = hsl_to_rgb(0, 0, 0)
        assert r == 0
        assert g == 0
        assert b == 0

    def test_various_hues(self):
        """Test various hue angles."""
        # Yellow (60°)
        r, g, b = hsl_to_rgb(60, 1.0, 0.5)
        assert r == 255
        assert g == 255
        assert b == 0

        # Cyan (180°)
        r, g, b = hsl_to_rgb(180, 1.0, 0.5)
        assert r == 0
        assert g == 255
        assert b == 255

        # Magenta (300°)
        r, g, b = hsl_to_rgb(300, 1.0, 0.5)
        assert r == 255
        assert g == 0
        assert b == 255


class TestRotateHue:
    """Tests for rotate_hue function."""

    def test_no_rotation(self):
        """Test zero rotation."""
        r, g, b = rotate_hue(255, 0, 0, 0)
        assert (r, g, b) == (255, 0, 0)

    def test_full_rotation(self):
        """Test 360-degree rotation returns same color."""
        r, g, b = rotate_hue(255, 0, 0, 360)
        assert (r, g, b) == (255, 0, 0)

    def test_120_degree_rotation(self):
        """Test 120-degree rotation (red to green)."""
        r, g, b = rotate_hue(255, 0, 0, 120)
        assert r == 0
        assert g == 255
        assert b == 0

    def test_240_degree_rotation(self):
        """Test 240-degree rotation (red to blue)."""
        r, g, b = rotate_hue(255, 0, 0, 240)
        assert r == 0
        assert g == 0
        assert b == 255

    def test_negative_rotation(self):
        """Test negative rotation."""
        r, g, b = rotate_hue(255, 0, 0, -120)
        # -120 degrees from red should be blue
        assert r == 0
        assert g == 0
        assert b == 255


class TestValidateHexColor:
    """Tests for validate_hex_color function."""

    def test_valid_six_char_hex(self):
        """Test valid 6-character hex colors."""
        assert validate_hex_color("#FF0000") is True
        assert validate_hex_color("#abcdef") is True
        assert validate_hex_color("#123456") is True

    def test_valid_three_char_hex(self):
        """Test valid 3-character hex colors."""
        assert validate_hex_color("#FFF") is True
        assert validate_hex_color("#abc") is True
        assert validate_hex_color("#123") is True

    def test_invalid_no_hash(self):
        """Test invalid hex without hash."""
        assert validate_hex_color("FF0000") is False

    def test_invalid_length(self):
        """Test invalid hex length."""
        assert validate_hex_color("#FF00") is False
        assert validate_hex_color("#FF000000") is False

    def test_invalid_characters(self):
        """Test invalid hex characters."""
        assert validate_hex_color("#GGGGGG") is False
        assert validate_hex_color("#XYZ") is False


class TestRoundTrip:
    """Test round-trip conversions."""

    def test_rgb_hex_roundtrip(self):
        """Test RGB -> HEX -> RGB round-trip."""
        original = (123, 45, 67)
        hex_color = rgb_to_hex(*original)
        result = hex_to_rgb(hex_color)
        assert result == original

    def test_rgb_hsl_roundtrip(self):
        """Test RGB -> HSL -> RGB round-trip."""
        test_colors = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (128, 64, 32),
            (200, 100, 150),
        ]
        for original in test_colors:
            h, s, lightness = rgb_to_hsl(*original)
            result = hsl_to_rgb(h, s, lightness)
            # Allow small rounding errors
            assert abs(result[0] - original[0]) <= 1
            assert abs(result[1] - original[1]) <= 1
            assert abs(result[2] - original[2]) <= 1
