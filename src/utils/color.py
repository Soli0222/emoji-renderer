"""Color conversion utilities: HEX <-> RGB <-> HSL."""

import re


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert HEX color to RGB tuple.

    Args:
        hex_color: HEX color string (e.g., "#FF0000" or "#F00")

    Returns:
        Tuple of (R, G, B) values (0-255)

    Raises:
        ValueError: If hex_color is invalid
    """
    hex_color = hex_color.lstrip('#')

    # Handle 3-character shorthand
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)

    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")

    if not re.match(r'^[A-Fa-f0-9]{6}$', hex_color):
        raise ValueError(f"Invalid hex color: {hex_color}")

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (r, g, b)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to HEX color string.

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        HEX color string (e.g., "#FF0000")
    """
    return f"#{r:02X}{g:02X}{b:02X}"


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    """
    Convert RGB to HSL color space.

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        Tuple of (H, S, L) where H is 0-360, S and L are 0-1
    """
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    max_c = max(r_norm, g_norm, b_norm)
    min_c = min(r_norm, g_norm, b_norm)
    delta = max_c - min_c

    # Lightness
    lightness = (max_c + min_c) / 2.0

    if delta == 0:
        h = 0.0
        s = 0.0
    else:
        # Saturation
        s = delta / (1 - abs(2 * lightness - 1))

        # Hue
        if max_c == r_norm:
            h = 60.0 * (((g_norm - b_norm) / delta) % 6)
        elif max_c == g_norm:
            h = 60.0 * (((b_norm - r_norm) / delta) + 2)
        else:
            h = 60.0 * (((r_norm - g_norm) / delta) + 4)

    return (h, s, lightness)


def hsl_to_rgb(h: float, s: float, lightness: float) -> tuple[int, int, int]:
    """
    Convert HSL to RGB color space.

    Args:
        h: Hue (0-360)
        s: Saturation (0-1)
        lightness: Lightness (0-1)

    Returns:
        Tuple of (R, G, B) values (0-255)
    """
    c = (1 - abs(2 * lightness - 1)) * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = lightness - c / 2.0

    r_prime: float
    g_prime: float
    b_prime: float

    if 0 <= h < 60:
        r_prime, g_prime, b_prime = c, x, 0.0
    elif 60 <= h < 120:
        r_prime, g_prime, b_prime = x, c, 0.0
    elif 120 <= h < 180:
        r_prime, g_prime, b_prime = 0.0, c, x
    elif 180 <= h < 240:
        r_prime, g_prime, b_prime = 0.0, x, c
    elif 240 <= h < 300:
        r_prime, g_prime, b_prime = x, 0.0, c
    else:
        r_prime, g_prime, b_prime = c, 0.0, x

    r_val = int((r_prime + m) * 255)
    g_val = int((g_prime + m) * 255)
    b_val = int((b_prime + m) * 255)

    # Clamp values to 0-255
    r_clamped = max(0, min(255, r_val))
    g_clamped = max(0, min(255, g_val))
    b_clamped = max(0, min(255, b_val))

    return (r_clamped, g_clamped, b_clamped)


def rotate_hue(r: int, g: int, b: int, degrees: float) -> tuple[int, int, int]:
    """
    Rotate the hue of an RGB color by a given number of degrees.

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)
        degrees: Hue rotation in degrees

    Returns:
        Tuple of (R, G, B) values with rotated hue
    """
    h, s, lightness = rgb_to_hsl(r, g, b)
    h = (h + degrees) % 360
    return hsl_to_rgb(h, s, lightness)


def validate_hex_color(hex_color: str) -> bool:
    """
    Validate a HEX color string.

    Args:
        hex_color: HEX color string to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return bool(re.match(pattern, hex_color))
