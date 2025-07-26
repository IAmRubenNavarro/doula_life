from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.schemas.consent import ConsentCreate, ConsentInDB, ConsentUpdate
from app.crud import consent as crud
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=ConsentInDB)
async def create_consent(consent: ConsentCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_consent(db, consent)

@router.get("/", response_model=List[ConsentInDB])
async def read_all_consents(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_all_consents(db, skip, limit)

@router.get("/{consent_id}", response_model=ConsentInDB)
async def read_consent(consent_id: UUID, db: AsyncSession = Depends(get_db)):
    consent = await crud.get_consent(db, consent_id)
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    return consent

@router.put("/{consent_id}", response_model=ConsentInDB)
async def update_consent(consent_id: UUID, consent_update: ConsentUpdate, db: AsyncSession = Depends(get_db)):
    consent = await crud.update_consent(db, consent_id, consent_update)
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    return consent

@router.delete("/{consent_id}")
async def delete_consent(consent_id: UUID, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_consent(db, consent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Consent not found")
    return {"ok": True}
