"""Pydantic models for API request/response schemas."""

import re
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator

from src.config import settings


# Regex pattern for hex color validation
HEX_COLOR_PATTERN = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')


class LayoutSchema(BaseModel):
    """Layout configuration for the rendered image."""
    
    mode: Literal["square", "banner"] = Field(
        default="square",
        description="Canvas sizing mode. 'square': 256x256 fixed. 'banner': height 256, width dynamic."
    )
    alignment: Literal["left", "center", "right"] = Field(
        default="center",
        description="Text horizontal alignment."
    )


class StyleSchema(BaseModel):
    """Text styling configuration."""
    
    fontId: str = Field(
        ...,
        description="Must match an ID returned by /fonts.",
        examples=["noto_sans_jp_black"]
    )
    textColor: str = Field(
        ...,
        description="Text color in HEX format.",
        examples=["#FF0000"]
    )
    outlineColor: str = Field(
        default="#FFFFFF",
        description="Outline/stroke color in HEX format."
    )
    outlineWidth: int = Field(
        default=0,
        ge=0,
        le=20,
        description="Outline stroke width in pixels."
    )
    shadow: bool = Field(
        default=False,
        description="Enable drop shadow effect."
    )
    
    @field_validator('textColor', 'outlineColor')
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Validate HEX color format."""
        if not HEX_COLOR_PATTERN.match(v):
            raise ValueError(f"Invalid HEX color format: {v}")
        return v


class MotionSchema(BaseModel):
    """Animation/motion configuration."""
    
    type: Literal["none", "shake", "spin", "bounce", "gaming"] = Field(
        default="none",
        description="Animation type. 'none' outputs static WebP."
    )
    intensity: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Animation intensity/amplitude."
    )
    speed: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Animation speed multiplier."
    )


class RenderRequest(BaseModel):
    """Request schema for /generate endpoint."""
    
    text: str = Field(
        ...,
        description="The text content to render. Newlines (\\n) are supported.",
        examples=["進捗\nどう？"]
    )
    layout: LayoutSchema = Field(
        default_factory=LayoutSchema,
        description="Canvas sizing and text alignment."
    )
    style: StyleSchema = Field(
        ...,
        description="Text styling options."
    )
    motion: MotionSchema = Field(
        default_factory=MotionSchema,
        description="Animation settings."
    )
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text content."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        if len(v) > settings.max_text_length:
            raise ValueError(f"Text exceeds maximum length of {settings.max_text_length} characters")
        return v


class FontSchema(BaseModel):
    """Font information schema."""
    
    id: str = Field(
        ...,
        description="The ID to send in the /generate request."
    )
    name: str = Field(
        ...,
        description="Human readable name."
    )
    categories: List[Literal["serif", "sans-serif", "handwritten", "display"]] = Field(
        default_factory=list,
        description="Font categories."
    )


class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str = Field(
        default="ok",
        description="Health status."
    )


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    detail: str = Field(
        ...,
        description="Error message."
    )
