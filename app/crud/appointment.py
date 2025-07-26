from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate

async def create_appointment(db: AsyncSession, appointment: AppointmentCreate) -> Appointment:
    appointment = Appointment(**appointment.model_dump())
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment

async def get_appointment(db: AsyncSession, appointment_id: UUID) -> Appointment:
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    return result.scalar_one_or_none()

async def list_appointments(db: AsyncSession) -> list[Appointment]:
    result = await db.execute(select(Appointment))
    return result.scalars().all()

async def update_appointment(db: AsyncSession, appointment_id: UUID, appointment_data: AppointmentUpdate) -> Appointment:
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appointment = result.scalar_one_or_none()
    if appointment:
        for field, value in appointment_data.model_dump(exclude_unset=True).items():
            setattr(appointment, field, value)
        await db.commit()
        await db.refresh(appointment)
    return appointment

async def delete_appointment(db: AsyncSession, appointment_id: UUID) -> bool:
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appointment = result.scalar_one_or_none()
    if appointment:
        await db.delete(appointment)
        await db.commit()
        return True
    return False
