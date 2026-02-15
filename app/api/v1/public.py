"""Public endpoints — unauthenticated, used by external services (e.g. Twilio)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Location, Organization, OrganizationStatus

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/vcard/{org_id}")
async def get_vcard(
    org_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Generate a vCard 3.0 file for a business.

    Twilio fetches this URL when we send a media message with the vCard.
    No authentication required.
    """
    result = await db.execute(
        select(Organization).where(
            Organization.id == org_id,
            Organization.status == OrganizationStatus.ACTIVE.value,
        )
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    business_name = org.name or "Business"
    phone = (org.settings or {}).get("twilio_phone_number") or org.phone_number

    # Try to get primary location for address
    loc_result = await db.execute(
        select(Location).where(
            Location.organization_id == org.id,
            Location.is_primary.is_(True),
        )
    )
    location = loc_result.scalar_one_or_none()

    # Build vCard 3.0
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{business_name}",
        f"ORG:{business_name}",
    ]

    if phone:
        clean_phone = phone.replace("whatsapp:", "")
        lines.append(f"TEL;TYPE=CELL:{clean_phone}")

    if location and location.address:
        # ADR: PO Box;Extended;Street;City;Region;Postal;Country
        lines.append(f"ADR;TYPE=WORK:;;{location.address};;;;")

    lines.append("END:VCARD")

    vcard_content = "\r\n".join(lines) + "\r\n"

    return Response(
        content=vcard_content,
        media_type="text/vcard",
        headers={"Content-Disposition": f'attachment; filename="{business_name}.vcf"'},
    )
