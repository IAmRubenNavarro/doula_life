from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.schemas.payment import PaymentCreate, PaymentInDB, PaymentUpdate
from app.crud import payment as crud
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=PaymentInDB)
async def create_payment(payment: PaymentCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_payment(db, payment)

@router.get("/", response_model=List[PaymentInDB])
async def read_all_payments(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_all_payments(db, skip, limit)

@router.get("/{payment_id}", response_model=PaymentInDB)
async def read_payment(payment_id: UUID, db: AsyncSession = Depends(get_db)):
    payment = await crud.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.put("/{payment_id}", response_model=PaymentInDB)
async def update_payment(payment_id: UUID, payment_update: PaymentUpdate, db: AsyncSession = Depends(get_db)):
    payment = await crud.update_payment(db, payment_id, payment_update)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.delete("/{payment_id}")
async def delete_payment(payment_id: UUID, db: AsyncSession = Depends(get_db)):
    deleted = await crud.delete_payment(db, payment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"ok": True}
