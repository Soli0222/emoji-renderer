"""Animation module - handles frame-by-frame animation generation."""

import logging
import math
import random
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np
from PIL import Image

from src.utils.color import hex_to_rgb, rotate_hue

logger = logging.getLogger(__name__)


# Animation constants
DEFAULT_FPS = 20
DEFAULT_DURATION = 1.0  # seconds
FRAME_DURATION_MS = 50  # 1000 / 20 fps


class MotionType(str, Enum):
    """Animation motion types."""
    NONE = "none"
    SHAKE = "shake"
    SPIN = "spin"
    BOUNCE = "bounce"
    GAMING = "gaming"


class Intensity(str, Enum):
    """Animation intensity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MotionConfig:
    """Motion/animation configuration."""
    type: MotionType = MotionType.NONE
    intensity: Intensity = Intensity.MEDIUM
    speed: float = 1.0


# Intensity multipliers for different effects
INTENSITY_MULTIPLIERS = {
    Intensity.LOW: 0.5,
    Intensity.MEDIUM: 1.0,
    Intensity.HIGH: 2.0
}


class AnimationGenerator:
    """Generates animated frames for various motion types."""

    def __init__(self, fps: int = DEFAULT_FPS, duration: float = DEFAULT_DURATION):
        """
        Initialize the animation generator.

        Args:
            fps: Frames per second
            duration: Duration of one animation cycle in seconds
        """
        self.fps = fps
        self.duration = duration

    def get_frame_count(self, speed: float = 1.0) -> int:
        """
        Calculate number of frames for one animation cycle.

        Args:
            speed: Speed multiplier

        Returns:
            Number of frames
        """
        adjusted_duration = self.duration / speed
        return max(1, int(self.fps * adjusted_duration))

    def generate_frames(
        self,
        base_image: Image.Image,
        motion: MotionConfig,
        text_color: str = "#FFFFFF",
        render_callback: Callable | None = None
    ) -> list[Image.Image]:
        """
        Generate animation frames for the specified motion type.

        Args:
            base_image: Base rendered image
            motion: Motion configuration
            text_color: Original text color (for gaming mode)
            render_callback: Callback to re-render text with new color (for gaming mode)

        Returns:
            List of PIL Images (frames)
        """
        if motion.type == MotionType.NONE:
            return [base_image]

        frame_count = self.get_frame_count(motion.speed)
        intensity_mult = INTENSITY_MULTIPLIERS[motion.intensity]

        if motion.type == MotionType.SHAKE:
            return self._generate_shake_frames(base_image, frame_count, intensity_mult)
        elif motion.type == MotionType.SPIN:
            return self._generate_spin_frames(base_image, frame_count)
        elif motion.type == MotionType.BOUNCE:
            return self._generate_bounce_frames(base_image, frame_count, intensity_mult)
        elif motion.type == MotionType.GAMING:
            return self._generate_gaming_frames(
                base_image, frame_count, text_color, render_callback
            )

        return [base_image]

    def _generate_shake_frames(
        self,
        base_image: Image.Image,
        frame_count: int,
        intensity_mult: float
    ) -> list[Image.Image]:
        """
        Generate shake animation frames.

        Args:
            base_image: Base image
            frame_count: Number of frames
            intensity_mult: Intensity multiplier

        Returns:
            List of frames
        """
        frames = []
        base_shake = 5  # Base shake amplitude in pixels
        shake_range = int(base_shake * intensity_mult)

        # Seed random for reproducibility (optional)
        random.seed(42)

        for _ in range(frame_count):
            # Random displacement
            dx = random.randint(-shake_range, shake_range)
            dy = random.randint(-shake_range, shake_range)

            # Create new canvas and paste shifted image
            frame = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
            frame.paste(base_image, (dx, dy), base_image)
            frames.append(frame)

        return frames

    def _generate_spin_frames(
        self,
        base_image: Image.Image,
        frame_count: int
    ) -> list[Image.Image]:
        """
        Generate spin animation frames.

        Args:
            base_image: Base image
            frame_count: Number of frames

        Returns:
            List of frames
        """
        frames = []

        for i in range(frame_count):
            # Calculate rotation angle
            angle = (360 / frame_count) * i

            # Rotate around center with expand=False to maintain size
            rotated = base_image.rotate(
                angle,
                expand=False,
                center=(base_image.width // 2, base_image.height // 2),
                resample=Image.Resampling.BICUBIC
            )
            frames.append(rotated)

        return frames

    def _generate_bounce_frames(
        self,
        base_image: Image.Image,
        frame_count: int,
        intensity_mult: float
    ) -> list[Image.Image]:
        """
        Generate bounce animation frames.

        Args:
            base_image: Base image
            frame_count: Number of frames
            intensity_mult: Intensity multiplier

        Returns:
            List of frames
        """
        frames = []
        base_amplitude = 10  # Base bounce amplitude in pixels
        amplitude = int(base_amplitude * intensity_mult)

        for i in range(frame_count):
            # Calculate Y offset using sine wave
            t = (2 * math.pi * i) / frame_count
            dy = int(math.sin(t) * amplitude)

            # Create new canvas and paste shifted image
            frame = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
            frame.paste(base_image, (0, dy), base_image)
            frames.append(frame)

        return frames

    def _generate_gaming_frames(
        self,
        base_image: Image.Image,
        frame_count: int,
        text_color: str,
        render_callback: Callable | None
    ) -> list[Image.Image]:
        """
        Generate gaming (rainbow) animation frames.

        Args:
            base_image: Base image (used if no callback)
            frame_count: Number of frames
            text_color: Original text color
            render_callback: Callback to re-render with new color

        Returns:
            List of frames
        """
        frames = []
        base_rgb = hex_to_rgb(text_color)

        for i in range(frame_count):
            # Calculate hue rotation
            hue_shift = (360 / frame_count) * i

            if render_callback is not None:
                # Re-render with rotated color
                new_color = rotate_hue(*base_rgb, hue_shift)
                frame = render_callback(new_color)
                frames.append(frame)
            else:
                # Fallback: apply hue shift to existing image
                frame = self._apply_hue_shift(base_image, hue_shift)
                frames.append(frame)

        return frames

    def _apply_hue_shift(self, image: Image.Image, hue_shift: float) -> Image.Image:
        """
        Apply hue shift to an image using NumPy.

        Args:
            image: Input image
            hue_shift: Hue shift in degrees

        Returns:
            Image with shifted hue
        """
        # Convert to numpy array
        arr = np.array(image.convert('RGBA'))

        # Only process non-transparent pixels
        alpha = arr[:, :, 3]
        mask = alpha > 0

        if not mask.any():
            return image

        # Extract RGB values
        rgb = arr[:, :, :3].astype(np.float32) / 255.0

        # Convert RGB to HSL and rotate hue
        # This is a simplified version - for production, consider using skimage or opencv
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

        max_c = np.maximum(np.maximum(r, g), b)
        min_c = np.minimum(np.minimum(r, g), b)
        delta = max_c - min_c

        # Calculate lightness
        lightness = (max_c + min_c) / 2.0

        # Calculate saturation
        s = np.zeros_like(lightness)
        non_zero = delta > 0
        s[non_zero] = delta[non_zero] / (1 - np.abs(2 * lightness[non_zero] - 1) + 1e-10)

        # Calculate hue
        h = np.zeros_like(lightness)

        r_max = (max_c == r) & non_zero
        g_max = (max_c == g) & non_zero
        b_max = (max_c == b) & non_zero

        h[r_max] = 60.0 * (((g[r_max] - b[r_max]) / (delta[r_max] + 1e-10)) % 6)
        h[g_max] = 60.0 * (((b[g_max] - r[g_max]) / (delta[g_max] + 1e-10)) + 2)
        h[b_max] = 60.0 * (((r[b_max] - g[b_max]) / (delta[b_max] + 1e-10)) + 4)

        # Rotate hue
        h = (h + hue_shift) % 360

        # Convert back to RGB
        c = (1 - np.abs(2 * lightness - 1)) * s
        x = c * (1 - np.abs((h / 60.0) % 2 - 1))
        m = lightness - c / 2.0

        r_new = np.zeros_like(lightness)
        g_new = np.zeros_like(lightness)
        b_new = np.zeros_like(lightness)

        idx = (h >= 0) & (h < 60)
        r_new[idx], g_new[idx], b_new[idx] = c[idx], x[idx], 0

        idx = (h >= 60) & (h < 120)
        r_new[idx], g_new[idx], b_new[idx] = x[idx], c[idx], 0

        idx = (h >= 120) & (h < 180)
        r_new[idx], g_new[idx], b_new[idx] = 0, c[idx], x[idx]

        idx = (h >= 180) & (h < 240)
        r_new[idx], g_new[idx], b_new[idx] = 0, x[idx], c[idx]

        idx = (h >= 240) & (h < 300)
        r_new[idx], g_new[idx], b_new[idx] = x[idx], 0, c[idx]

        idx = (h >= 300) & (h < 360)
        r_new[idx], g_new[idx], b_new[idx] = c[idx], 0, x[idx]

        r_new = ((r_new + m) * 255).clip(0, 255).astype(np.uint8)
        g_new = ((g_new + m) * 255).clip(0, 255).astype(np.uint8)
        b_new = ((b_new + m) * 255).clip(0, 255).astype(np.uint8)

        # Only apply to masked pixels
        result = arr.copy()
        result[:, :, 0][mask] = r_new[mask]
        result[:, :, 1][mask] = g_new[mask]
        result[:, :, 2][mask] = b_new[mask]

        return Image.fromarray(result, 'RGBA')


# Global animation generator instance
animation_generator = AnimationGenerator()
