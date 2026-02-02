"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Logging
    log_level: str = "INFO"

    # Text limits
    max_text_length: int = 20

    # Image size limits (KB)
    max_image_size_kb: int = 1024

    # Default font
    default_font_id: str = "noto_sans_jp_bold"

    # Font directory
    font_directory: str = "./assets/fonts"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8109

    # Metrics server settings
    metrics_port: int = 9109

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
