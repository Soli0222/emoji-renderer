"""Font management module - loads and manages available fonts."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import ImageFont

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FontInfo:
    """Information about an available font."""
    id: str
    name: str
    path: str
    categories: list[str]


class FontManager:
    """Manages font loading and access."""

    _instance: Optional["FontManager"] = None
    _fonts: dict[str, FontInfo] = {}
    _font_cache: dict[str, ImageFont.FreeTypeFont] = {}

    def __new__(cls):
        """Singleton pattern for font manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize font manager (only once due to singleton)."""
        if self._initialized:
            return
        self._initialized = True
        self._fonts = {}
        self._font_cache = {}

    def initialize(self, font_directory: str | None = None) -> None:
        """
        Scan font directory and load available fonts.

        Args:
            font_directory: Path to font directory. Uses settings if not provided.
        """
        font_dir = font_directory or settings.font_directory
        font_path = Path(font_dir)

        if not font_path.exists():
            logger.warning(f"Font directory does not exist: {font_dir}")
            font_path.mkdir(parents=True, exist_ok=True)
            return

        # Scan for font files
        font_extensions = {'.ttf', '.otf', '.ttc', '.woff', '.woff2'}

        for font_file in font_path.iterdir():
            if font_file.suffix.lower() in font_extensions:
                font_id = self._generate_font_id(font_file.stem)
                font_name = self._generate_font_name(font_file.stem)
                categories = self._detect_categories(font_file.stem)

                self._fonts[font_id] = FontInfo(
                    id=font_id,
                    name=font_name,
                    path=str(font_file.absolute()),
                    categories=categories
                )
                logger.info(f"Loaded font: {font_id} from {font_file.name}")

        logger.info(f"Total fonts loaded: {len(self._fonts)}")

    def _generate_font_id(self, filename: str) -> str:
        """
        Generate a unique font ID from filename.

        Args:
            filename: Font filename without extension

        Returns:
            Snake_case font ID
        """
        # Convert to lowercase and replace spaces/hyphens with underscores
        font_id = filename.lower()
        font_id = font_id.replace(' ', '_')
        font_id = font_id.replace('-', '_')
        # Remove consecutive underscores
        while '__' in font_id:
            font_id = font_id.replace('__', '_')
        return font_id

    def _generate_font_name(self, filename: str) -> str:
        """
        Generate human-readable font name from filename.

        Args:
            filename: Font filename without extension

        Returns:
            Human-readable font name
        """
        # Replace underscores and hyphens with spaces, then title case
        name = filename.replace('_', ' ').replace('-', ' ')
        return name.title()

    def _detect_categories(self, filename: str) -> list[str]:
        """
        Detect font categories from filename.

        Args:
            filename: Font filename without extension

        Returns:
            List of category strings
        """
        categories = []
        filename_lower = filename.lower()

        if 'serif' in filename_lower and 'sans' not in filename_lower:
            categories.append('serif')
        if 'sans' in filename_lower:
            categories.append('sans-serif')
        if any(word in filename_lower for word in ['hand', 'script', 'cursive']):
            categories.append('handwritten')
        if any(word in filename_lower for word in ['display', 'decorative', 'fancy']):
            categories.append('display')

        # Default to sans-serif if no category detected
        if not categories:
            categories.append('sans-serif')

        return categories

    def get_font(self, font_id: str, size: int) -> ImageFont.FreeTypeFont:
        """
        Get a PIL ImageFont for the specified font ID and size.

        Args:
            font_id: Font identifier
            size: Font size in pixels

        Returns:
            PIL ImageFont object

        Raises:
            ValueError: If font_id is not found
        """
        if font_id not in self._fonts:
            raise ValueError(f"Font not found: {font_id}")

        cache_key = f"{font_id}_{size}"

        if cache_key not in self._font_cache:
            font_info = self._fonts[font_id]
            self._font_cache[cache_key] = ImageFont.truetype(
                font_info.path, size=size
            )

        return self._font_cache[cache_key]

    def font_exists(self, font_id: str) -> bool:
        """
        Check if a font ID exists.

        Args:
            font_id: Font identifier to check

        Returns:
            True if font exists, False otherwise
        """
        return font_id in self._fonts

    def list_fonts(self) -> list[FontInfo]:
        """
        Get list of all available fonts.

        Returns:
            List of FontInfo objects
        """
        return list(self._fonts.values())

    def get_font_info(self, font_id: str) -> FontInfo | None:
        """
        Get information about a specific font.

        Args:
            font_id: Font identifier

        Returns:
            FontInfo object or None if not found
        """
        return self._fonts.get(font_id)


# Global font manager instance
font_manager = FontManager()
