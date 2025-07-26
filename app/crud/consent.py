from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.consent import Consent
from app.schemas.consent import ConsentCreate, ConsentUpdate
from uuid import UUID

async def create_consent(db: AsyncSession, consent_in: ConsentCreate):
    new_consent = Consent(**consent_in.model_dump())
    db.add(new_consent)
    await db.commit()
    await db.refresh(new_consent)
    return new_consent

async def get_consent(db: AsyncSession, consent_id: UUID):
    result = await db.execute(select(Consent).where(Consent.id == consent_id))
    return result.scalar_one_or_none()

async def get_all_consents(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Consent).offset(skip).limit(limit))
    return result.scalars().all()

async def update_consent(db: AsyncSession, consent_id: UUID, consent_in: ConsentUpdate):
    result = await db.execute(select(Consent).where(Consent.id == consent_id))
    consent = result.scalar_one_or_none()
    if not consent:
        return None
    for key, value in consent_in.model_dump(exclude_unset=True).items():
        setattr(consent, key, value)
    await db.commit()
    await db.refresh(consent)
    return consent

async def delete_consent(db: AsyncSession, consent_id: UUID):
    result = await db.execute(select(Consent).where(Consent.id == consent_id))
    consent = result.scalar_one_or_none()
    if not consent:
        return None
    await db.delete(consent)
    await db.commit()
    return consent
