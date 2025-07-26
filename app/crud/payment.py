from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate
from uuid import UUID

async def create_payment(db: AsyncSession, payment_in: PaymentCreate):
    new_payment = Payment(**payment_in.model_dump())
    db.add(new_payment)
    await db.commit()
    await db.refresh(new_payment)
    return new_payment

async def get_payment(db: AsyncSession, payment_id: UUID):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one_or_none()

async def get_all_payments(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(Payment).offset(skip).limit(limit))
    return result.scalars().all()

async def update_payment(db: AsyncSession, payment_id: UUID, payment_in: PaymentUpdate):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        return None
    for key, value in payment_in.model_dump(exclude_unset=True).items():
        setattr(payment, key, value)
    await db.commit()
    await db.refresh(payment)
    return payment

async def delete_payment(db: AsyncSession, payment_id: UUID):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        return None
    await db.delete(payment)
    await db.commit()
    return payment
