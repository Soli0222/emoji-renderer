"""Integration tests for API routes."""

import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from main import app
from src.core.engine import RenderResult
from src.core.fonts import FontInfo


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check_returns_ok(self, client):
        """Test health check returns ok status."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_check_content_type(self, client):
        """Test health check returns JSON."""
        response = client.get("/health")

        assert "application/json" in response.headers["content-type"]


class TestFontsEndpoint:
    """Tests for /fonts endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_font_manager(self):
        """Mock font manager."""
        with patch('src.api.routes.font_manager') as mock:
            mock.list_fonts.return_value = [
                FontInfo(
                    id="noto_sans_jp_bold",
                    name="Noto Sans JP Bold",
                    path="/path/to/font.ttf",
                    categories=["sans-serif"]
                ),
                FontInfo(
                    id="roboto_regular",
                    name="Roboto Regular",
                    path="/path/to/roboto.ttf",
                    categories=["sans-serif"]
                )
            ]
            yield mock

    def test_list_fonts_returns_fonts(self, client, mock_font_manager):
        """Test fonts endpoint returns font list."""
        response = client.get("/fonts")

        assert response.status_code == 200
        fonts = response.json()
        assert len(fonts) == 2

    def test_list_fonts_structure(self, client, mock_font_manager):
        """Test font response structure."""
        response = client.get("/fonts")
        fonts = response.json()

        font = fonts[0]
        assert "id" in font
        assert "name" in font
        assert "categories" in font

    def test_list_fonts_empty(self, client):
        """Test fonts endpoint with no fonts."""
        with patch('src.api.routes.font_manager') as mock:
            mock.list_fonts.return_value = []

            response = client.get("/fonts")

            assert response.status_code == 200
            assert response.json() == []


class TestGenerateEndpoint:
    """Tests for /generate endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_font_manager(self):
        """Mock font manager."""
        with patch('src.api.routes.font_manager') as mock:
            mock.font_exists.return_value = True
            yield mock

    @pytest.fixture
    def mock_rendering_engine(self):
        """Mock rendering engine."""
        with patch('src.api.routes.rendering_engine') as mock:
            # Create a simple test image
            img = Image.new('RGBA', (256, 256), (255, 0, 0, 255))
            buffer = io.BytesIO()
            img.save(buffer, format='WEBP')
            webp_data = buffer.getvalue()

            mock.render.return_value = RenderResult(
                data=webp_data,
                format="webp",
                size_bytes=len(webp_data),
                render_time_ms=50.0
            )
            mock.check_size_limit.return_value = True
            yield mock

    @pytest.fixture
    def valid_request(self):
        """Create valid request payload."""
        return {
            "text": "テスト",
            "style": {
                "fontId": "noto_sans_jp_bold",
                "textColor": "#FF0000"
            }
        }

    def test_generate_static_image(self, client, mock_font_manager, mock_rendering_engine, valid_request):
        """Test generating a static image."""
        response = client.post("/generate", json=valid_request)

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/webp"

    def test_generate_with_layout(self, client, mock_font_manager, mock_rendering_engine):
        """Test generating with layout options."""
        request = {
            "text": "テスト",
            "layout": {
                "mode": "banner",
                "alignment": "left"
            },
            "style": {
                "fontId": "noto_sans_jp_bold",
                "textColor": "#FF0000"
            }
        }

        response = client.post("/generate", json=request)

        assert response.status_code == 200

    def test_generate_with_animation(self, client, mock_font_manager, mock_rendering_engine):
        """Test generating with animation."""
        # Update mock for APNG output
        img = Image.new('RGBA', (256, 256), (255, 0, 0, 255))
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        png_data = buffer.getvalue()

        mock_rendering_engine.render.return_value = RenderResult(
            data=png_data,
            format="apng",
            size_bytes=len(png_data),
            render_time_ms=100.0
        )

        request = {
            "text": "テスト",
            "style": {
                "fontId": "noto_sans_jp_bold",
                "textColor": "#FF0000"
            },
            "motion": {
                "type": "shake",
                "intensity": "medium",
                "speed": 1.0
            }
        }

        response = client.post("/generate", json=request)

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/apng"

    def test_generate_font_not_found(self, client, mock_rendering_engine):
        """Test error when font not found."""
        with patch('src.api.routes.font_manager') as mock_fm:
            mock_fm.font_exists.return_value = False

            request = {
                "text": "テスト",
                "style": {
                    "fontId": "nonexistent_font",
                    "textColor": "#FF0000"
                }
            }

            response = client.post("/generate", json=request)

            assert response.status_code == 422
            assert "Font not found" in response.json()["detail"]

    def test_generate_invalid_hex_color(self, client, mock_font_manager, mock_rendering_engine):
        """Test error with invalid hex color."""
        request = {
            "text": "テスト",
            "style": {
                "fontId": "noto_sans_jp_bold",
                "textColor": "invalid"
            }
        }

        response = client.post("/generate", json=request)

        assert response.status_code == 422

    def test_generate_empty_text(self, client, mock_font_manager, mock_rendering_engine):
        """Test error with empty text."""
        request = {
            "text": "",
            "style": {
                "fontId": "noto_sans_jp_bold",
                "textColor": "#FF0000"
            }
        }

        response = client.post("/generate", json=request)

        assert response.status_code == 422

    def test_generate_text_too_long(self, client, mock_font_manager, mock_rendering_engine):
        """Test error when text exceeds limit."""
        request = {
            "text": "a" * 100,  # Exceeds max_text_length
            "style": {
                "fontId": "noto_sans_jp_bold",
                "textColor": "#FF0000"
            }
        }

        response = client.post("/generate", json=request)

        assert response.status_code == 422

    def test_generate_size_limit_exceeded(self, client, valid_request):
        """Test error when output size exceeds limit."""
        with patch('src.api.routes.font_manager') as mock_fm, \
             patch('src.api.routes.rendering_engine') as mock_engine:
            mock_fm.font_exists.return_value = True
            mock_engine.check_size_limit.return_value = False
            mock_engine.render.return_value = RenderResult(
                data=b"x" * (2 * 1024 * 1024),
                format="webp",
                size_bytes=2 * 1024 * 1024,
                render_time_ms=50.0
            )

            response = client.post("/generate", json=valid_request)

        assert response.status_code == 400
        assert "exceeds limit" in response.json()["detail"]

    def test_generate_with_outline(self, client, mock_font_manager, mock_rendering_engine):
        """Test generating with outline."""
        request = {
            "text": "テスト",
            "style": {
                "fontId": "noto_sans_jp_bold",
                "textColor": "#FF0000",
                "outlineColor": "#000000",
                "outlineWidth": 5
            }
        }

        response = client.post("/generate", json=request)

        assert response.status_code == 200

    def test_generate_with_shadow(self, client, mock_font_manager, mock_rendering_engine):
        """Test generating with shadow."""
        request = {
            "text": "テスト",
            "style": {
                "fontId": "noto_sans_jp_bold",
                "textColor": "#FF0000",
                "shadow": True
            }
        }

        response = client.post("/generate", json=request)

        assert response.status_code == 200

    def test_generate_multiline_text(self, client, mock_font_manager, mock_rendering_engine):
        """Test generating with multiline text."""
        request = {
            "text": "進捗\nどう？",
            "style": {
                "fontId": "noto_sans_jp_bold",
                "textColor": "#FF0000"
            }
        }

        response = client.post("/generate", json=request)

        assert response.status_code == 200

    def test_generate_all_motion_types(self, client, mock_font_manager, mock_rendering_engine):
        """Test all motion types."""
        motion_types = ["none", "shake", "spin", "bounce", "gaming"]

        for motion_type in motion_types:
            request = {
                "text": "テスト",
                "style": {
                    "fontId": "noto_sans_jp_bold",
                    "textColor": "#FF0000"
                },
                "motion": {
                    "type": motion_type
                }
            }

            response = client.post("/generate", json=request)

            assert response.status_code == 200, f"Failed for motion type: {motion_type}"

    def test_generate_all_intensities(self, client, mock_font_manager, mock_rendering_engine):
        """Test all intensity levels."""
        intensities = ["low", "medium", "high"]

        for intensity in intensities:
            request = {
                "text": "テスト",
                "style": {
                    "fontId": "noto_sans_jp_bold",
                    "textColor": "#FF0000"
                },
                "motion": {
                    "type": "shake",
                    "intensity": intensity
                }
            }

            response = client.post("/generate", json=request)

            assert response.status_code == 200, f"Failed for intensity: {intensity}"

    def test_generate_rendering_error(self, client, mock_font_manager, mock_rendering_engine, valid_request):
        """Test handling of rendering errors."""
        mock_rendering_engine.render.side_effect = Exception("Rendering failed")

        response = client.post("/generate", json=valid_request)

        assert response.status_code == 500
        assert "Internal rendering error" in response.json()["detail"]

    def test_generate_validation_error(self, client, mock_font_manager, mock_rendering_engine, valid_request):
        """Test handling of validation errors."""
        mock_rendering_engine.render.side_effect = ValueError("Invalid parameter")

        response = client.post("/generate", json=valid_request)

        assert response.status_code == 422


class TestOpenAPISpec:
    """Tests for OpenAPI specification."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_openapi_json_available(self, client):
        """Test OpenAPI JSON is available."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        spec = response.json()
        assert "openapi" in spec
        assert "paths" in spec

    def test_openapi_has_all_endpoints(self, client):
        """Test OpenAPI includes all endpoints."""
        response = client.get("/openapi.json")
        spec = response.json()
        paths = spec["paths"]

        assert "/health" in paths
        assert "/fonts" in paths
        assert "/generate" in paths
