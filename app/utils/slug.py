"""Slug generation utilities for URL-friendly business identifiers."""

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a business name.

    Handles Mexican Spanish characters (accents, ñ, etc).
    Examples:
        "Barbería Don Carlos" -> "barberia-don-carlos"
        "Salón de Belleza María" -> "salon-de-belleza-maria"
        "Uñas & Pestañas Glam!!" -> "unas-pestanas-glam"
    """
    # NFD decomposition then strip combining marks (accents)
    slug = unicodedata.normalize("NFKD", name)
    slug = "".join(c for c in slug if not unicodedata.combining(c))
    slug = slug.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    slug = re.sub(r"-+", "-", slug)
    return slug


async def generate_unique_slug(db: AsyncSession, name: str) -> str:
    """Generate a unique slug, appending a number on collision.

    Args:
        db: Database session.
        name: Business name.

    Returns:
        Unique slug string.
    """
    from app.models.organization import Organization

    base_slug = generate_slug(name)
    if not base_slug:
        base_slug = "negocio"

    slug = base_slug
    counter = 1
    while True:
        result = await db.execute(select(Organization.id).where(Organization.slug == slug))
        if result.scalar_one_or_none() is None:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1
