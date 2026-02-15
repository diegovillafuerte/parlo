"""Tests for the image description service."""

from unittest.mock import MagicMock, patch

import pytest

from app.ai.image_description import describe_image


@pytest.mark.asyncio
async def test_describe_image_returns_description():
    """describe_image should return the text from the OpenAI vision response."""
    mock_message = MagicMock()
    mock_message.content = "Un menú de servicios con precios en pesos."

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("app.ai.image_description.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        result = await describe_image("https://example.com/menu.jpg", "image/jpeg")

    assert result == "Un menú de servicios con precios en pesos."
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-4.1-mini"
    assert call_kwargs["max_tokens"] == 300


@pytest.mark.asyncio
async def test_describe_image_error_returns_fallback():
    """On API failure, describe_image should return a safe fallback string."""
    with patch("app.ai.image_description.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API down")
        mock_openai_cls.return_value = mock_client

        result = await describe_image("https://example.com/photo.png", "image/png")

    assert result == "[Se recibió una imagen pero no se pudo procesar]"


@pytest.mark.asyncio
async def test_describe_image_rejects_non_image_mime():
    """Non-image MIME types should be rejected without calling OpenAI."""
    result = await describe_image("https://example.com/doc.pdf", "application/pdf")
    assert result == "[Se recibió un archivo de tipo application/pdf]"


@pytest.mark.asyncio
async def test_describe_image_no_api_key():
    """If no OpenAI API key is configured, return fallback."""
    with patch("app.ai.image_description.get_settings") as mock_settings:
        mock_settings.return_value.openai_api_key = None
        result = await describe_image("https://example.com/img.jpg", "image/jpeg")

    assert result == "[Se recibió una imagen pero no se pudo procesar]"


@pytest.mark.asyncio
async def test_describe_image_empty_content():
    """If the model returns empty content, return empty string."""
    mock_message = MagicMock()
    mock_message.content = None

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("app.ai.image_description.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        result = await describe_image("https://example.com/img.jpg", "image/jpeg")

    assert result == ""
