"""One-time script to backfill slugs for existing active organizations."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import async_session_factory
from app.models.organization import Organization, OrganizationStatus
from app.utils.slug import generate_unique_slug


async def backfill():
    async with async_session_factory() as db:
        result = await db.execute(
            select(Organization).where(
                Organization.status == OrganizationStatus.ACTIVE.value,
                Organization.slug.is_(None),
            )
        )
        orgs = result.scalars().all()

        if not orgs:
            print("No organizations need slug backfill.")
            return

        for org in orgs:
            name = org.name or "negocio"
            slug = await generate_unique_slug(db, name)
            org.slug = slug
            print(f"  {org.name} -> {slug}")

        await db.commit()
        print(f"\nBackfilled {len(orgs)} organization(s).")


if __name__ == "__main__":
    asyncio.run(backfill())
