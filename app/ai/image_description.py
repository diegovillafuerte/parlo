"""Image description service — extracts text descriptions from images via OpenAI vision API."""

import logging

from openai import OpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

VISION_PROMPT = (
    "Describe esta imagen en español en máximo 2-3 oraciones. "
    "Si contiene texto visible (menú de servicios, precios, horarios, datos de una cita), "
    "transcríbelo fielmente. Si es una foto de un lugar o persona, descríbela brevemente."
)


async def describe_image(media_url: str, media_content_type: str) -> str:
    """Call OpenAI vision API to get a text description of an image.

    Args:
        media_url: Public URL of the image (from Twilio).
        media_content_type: MIME type, e.g. "image/jpeg".

    Returns:
        Spanish text description, or a fallback string on error.
    """
    if not media_content_type.startswith("image/"):
        return f"[Se recibió un archivo de tipo {media_content_type}]"

    settings = get_settings()
    if not settings.openai_api_key:
        logger.warning("No OpenAI API key — cannot describe image")
        return "[Se recibió una imagen pero no se pudo procesar]"

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {"type": "image_url", "image_url": {"url": media_url}},
                    ],
                }
            ],
        )
        description = response.choices[0].message.content or ""
        return description.strip()

    except Exception:
        logger.exception("Failed to describe image from %s", media_url)
        return "[Se recibió una imagen pero no se pudo procesar]"
