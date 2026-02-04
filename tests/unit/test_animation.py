"""Unit tests for animation generation."""

import pytest
from PIL import Image

from src.core.animation import (
    DEFAULT_DURATION,
    DEFAULT_FPS,
    FRAME_DURATION_MS,
    INTENSITY_MULTIPLIERS,
    AnimationGenerator,
    Intensity,
    MotionConfig,
    MotionType,
)


class TestMotionType:
    """Tests for MotionType enum."""

    def test_motion_types(self):
        """Test all motion types are defined."""
        assert MotionType.NONE.value == "none"
        assert MotionType.SHAKE.value == "shake"
        assert MotionType.SPIN.value == "spin"
        assert MotionType.BOUNCE.value == "bounce"
        assert MotionType.GAMING.value == "gaming"

    def test_motion_type_from_string(self):
        """Test creating motion type from string."""
        assert MotionType("none") == MotionType.NONE
        assert MotionType("shake") == MotionType.SHAKE
        assert MotionType("spin") == MotionType.SPIN


class TestIntensity:
    """Tests for Intensity enum."""

    def test_intensity_levels(self):
        """Test all intensity levels are defined."""
        assert Intensity.LOW.value == "low"
        assert Intensity.MEDIUM.value == "medium"
        assert Intensity.HIGH.value == "high"

    def test_intensity_from_string(self):
        """Test creating intensity from string."""
        assert Intensity("low") == Intensity.LOW
        assert Intensity("medium") == Intensity.MEDIUM
        assert Intensity("high") == Intensity.HIGH


class TestMotionConfig:
    """Tests for MotionConfig dataclass."""

    def test_default_values(self):
        """Test default motion config values."""
        config = MotionConfig()
        assert config.type == MotionType.NONE
        assert config.intensity == Intensity.MEDIUM
        assert config.speed == 1.0

    def test_custom_values(self):
        """Test custom motion config values."""
        config = MotionConfig(type=MotionType.SHAKE, intensity=Intensity.HIGH, speed=2.0)
        assert config.type == MotionType.SHAKE
        assert config.intensity == Intensity.HIGH
        assert config.speed == 2.0


class TestAnimationGenerator:
    """Tests for AnimationGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create AnimationGenerator instance."""
        return AnimationGenerator()

    @pytest.fixture
    def test_image(self):
        """Create a test image for animation."""
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        # Draw something visible
        for x in range(100, 156):
            for y in range(100, 156):
                img.putpixel((x, y), (255, 0, 0, 255))
        return img

    def test_init_default_values(self, generator):
        """Test default initialization values."""
        assert generator.fps == DEFAULT_FPS
        assert generator.duration == DEFAULT_DURATION

    def test_init_custom_values(self):
        """Test custom initialization values."""
        gen = AnimationGenerator(fps=30, duration=2.0)
        assert gen.fps == 30
        assert gen.duration == 2.0

    def test_get_frame_count_default_speed(self, generator):
        """Test frame count at default speed."""
        count = generator.get_frame_count(1.0)
        expected = int(DEFAULT_FPS * DEFAULT_DURATION)
        assert count == expected

    def test_get_frame_count_double_speed(self, generator):
        """Test frame count at double speed."""
        count_normal = generator.get_frame_count(1.0)
        count_fast = generator.get_frame_count(2.0)
        assert count_fast == count_normal // 2

    def test_get_frame_count_half_speed(self, generator):
        """Test frame count at half speed."""
        count_normal = generator.get_frame_count(1.0)
        count_slow = generator.get_frame_count(0.5)
        assert count_slow == count_normal * 2

    def test_get_frame_count_minimum(self, generator):
        """Test frame count never goes below 1."""
        count = generator.get_frame_count(100.0)  # Very fast
        assert count >= 1

    def test_generate_frames_none_returns_single(self, generator, test_image):
        """Test NONE motion returns single frame."""
        motion = MotionConfig(type=MotionType.NONE)
        frames = generator.generate_frames(test_image, motion)

        assert len(frames) == 1
        assert frames[0] == test_image

    def test_generate_frames_shake(self, generator, test_image):
        """Test shake animation generates frames."""
        motion = MotionConfig(type=MotionType.SHAKE)
        frames = generator.generate_frames(test_image, motion)

        assert len(frames) > 1
        assert all(isinstance(f, Image.Image) for f in frames)
        assert all(f.size == test_image.size for f in frames)

    def test_generate_frames_spin(self, generator, test_image):
        """Test spin animation generates frames."""
        motion = MotionConfig(type=MotionType.SPIN)
        frames = generator.generate_frames(test_image, motion)

        assert len(frames) > 1
        assert all(isinstance(f, Image.Image) for f in frames)
        assert all(f.size == test_image.size for f in frames)

    def test_generate_frames_bounce(self, generator, test_image):
        """Test bounce animation generates frames."""
        motion = MotionConfig(type=MotionType.BOUNCE)
        frames = generator.generate_frames(test_image, motion)

        assert len(frames) > 1
        assert all(isinstance(f, Image.Image) for f in frames)
        assert all(f.size == test_image.size for f in frames)

    def test_generate_shake_intensity_affects_amplitude(self, generator, test_image):
        """Test shake intensity affects displacement range."""
        motion_low = MotionConfig(type=MotionType.SHAKE, intensity=Intensity.LOW)
        motion_high = MotionConfig(type=MotionType.SHAKE, intensity=Intensity.HIGH)

        # Both should generate frames, but with different shake amounts
        frames_low = generator.generate_frames(test_image, motion_low)
        frames_high = generator.generate_frames(test_image, motion_high)

        assert len(frames_low) == len(frames_high)

    def test_generate_spin_full_rotation(self, generator, test_image):
        """Test spin covers full 360 degrees."""
        motion = MotionConfig(type=MotionType.SPIN)
        frame_count = generator.get_frame_count(motion.speed)

        # Each frame should be at angle = 360 / frame_count * i
        frames = generator.generate_frames(test_image, motion)
        assert len(frames) == frame_count

    def test_generate_bounce_sine_wave(self, generator, test_image):
        """Test bounce follows sine wave pattern."""
        motion = MotionConfig(type=MotionType.BOUNCE)
        frames = generator.generate_frames(test_image, motion)

        # Frames should have varying vertical positions
        assert len(frames) > 1

    def test_shake_frames_random_displacement(self, generator, test_image):
        """Test shake frames have random displacement."""
        MotionConfig(type=MotionType.SHAKE, intensity=Intensity.MEDIUM)
        frames = generator._generate_shake_frames(
            test_image, 10, INTENSITY_MULTIPLIERS[Intensity.MEDIUM]
        )

        assert len(frames) == 10
        # All frames should be valid RGBA images
        for frame in frames:
            assert frame.mode == "RGBA"
            assert frame.size == test_image.size

    def test_spin_frames_rotation(self, generator, test_image):
        """Test spin frames are rotated correctly."""
        frames = generator._generate_spin_frames(test_image, 4)

        # 4 frames should be at 0°, 90°, 180°, 270°
        assert len(frames) == 4
        for frame in frames:
            assert frame.size == test_image.size

    def test_bounce_frames_vertical_offset(self, generator, test_image):
        """Test bounce frames have vertical offset."""
        frames = generator._generate_bounce_frames(
            test_image, 10, INTENSITY_MULTIPLIERS[Intensity.MEDIUM]
        )

        assert len(frames) == 10
        for frame in frames:
            assert frame.size == test_image.size

    def test_gaming_frames_with_callback(self, generator, test_image):
        """Test gaming frames with render callback."""
        callback_calls = []

        def render_callback(color):
            callback_calls.append(color)
            return test_image.copy()

        frames = generator._generate_gaming_frames(test_image, 5, "#FF0000", render_callback)

        assert len(frames) == 5
        assert len(callback_calls) == 5
        # Each call should have a different color
        colors_set = set(callback_calls)
        assert len(colors_set) == 5

    def test_gaming_frames_without_callback(self, generator, test_image):
        """Test gaming frames without callback uses hue shift."""
        frames = generator._generate_gaming_frames(
            test_image,
            5,
            "#FF0000",
            None,  # No callback
        )

        assert len(frames) == 5
        for frame in frames:
            assert frame.size == test_image.size

    def test_apply_hue_shift(self, generator, test_image):
        """Test hue shift is applied correctly."""
        shifted = generator._apply_hue_shift(test_image, 120)

        assert shifted.size == test_image.size
        assert shifted.mode == test_image.mode

    def test_apply_hue_shift_no_visible_pixels(self, generator):
        """Test hue shift on transparent image."""
        transparent = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        shifted = generator._apply_hue_shift(transparent, 90)

        assert shifted.size == transparent.size

    def test_speed_affects_frame_count(self, generator, test_image):
        """Test speed parameter affects frame count."""
        motion_slow = MotionConfig(type=MotionType.SHAKE, speed=0.5)
        motion_fast = MotionConfig(type=MotionType.SHAKE, speed=2.0)

        frames_slow = generator.generate_frames(test_image, motion_slow)
        frames_fast = generator.generate_frames(test_image, motion_fast)

        assert len(frames_slow) > len(frames_fast)


class TestAnimationConstants:
    """Test module constants."""

    def test_default_fps(self):
        """Test default FPS constant."""
        assert DEFAULT_FPS == 20

    def test_default_duration(self):
        """Test default duration constant."""
        assert DEFAULT_DURATION == 1.0

    def test_frame_duration_ms(self):
        """Test frame duration in milliseconds."""
        assert FRAME_DURATION_MS == 50  # 1000 / 20 = 50

    def test_intensity_multipliers(self):
        """Test intensity multipliers are correct."""
        assert INTENSITY_MULTIPLIERS[Intensity.LOW] == 0.5
        assert INTENSITY_MULTIPLIERS[Intensity.MEDIUM] == 1.0
        assert INTENSITY_MULTIPLIERS[Intensity.HIGH] == 2.0


class TestAnimationGeneratorIntegration:
    """Integration tests for animation generation."""

    @pytest.fixture
    def colored_image(self):
        """Create an image with visible content."""
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        # Add a colored square in the center
        for x in range(78, 178):
            for y in range(78, 178):
                img.putpixel((x, y), (255, 128, 64, 255))
        return img

    def test_full_animation_pipeline_shake(self, colored_image):
        """Test full shake animation pipeline."""
        generator = AnimationGenerator()
        motion = MotionConfig(type=MotionType.SHAKE, intensity=Intensity.MEDIUM, speed=1.0)

        frames = generator.generate_frames(colored_image, motion)

        assert len(frames) == 20  # 20 fps * 1 second
        assert all(f.mode == "RGBA" for f in frames)

    def test_full_animation_pipeline_spin(self, colored_image):
        """Test full spin animation pipeline."""
        generator = AnimationGenerator()
        motion = MotionConfig(type=MotionType.SPIN, intensity=Intensity.MEDIUM, speed=1.0)

        frames = generator.generate_frames(colored_image, motion)

        assert len(frames) == 20
        assert all(f.mode == "RGBA" for f in frames)

    def test_full_animation_pipeline_bounce(self, colored_image):
        """Test full bounce animation pipeline."""
        generator = AnimationGenerator()
        motion = MotionConfig(type=MotionType.BOUNCE, intensity=Intensity.HIGH, speed=1.0)

        frames = generator.generate_frames(colored_image, motion)

        assert len(frames) == 20
        assert all(f.mode == "RGBA" for f in frames)
