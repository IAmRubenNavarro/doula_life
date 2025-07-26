from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentUpdate
from app.crud import appointment as appointment_crud
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/", response_model=AppointmentRead)
async def create_appointment(appointment: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    return await appointment_crud.create_appointment(db, appointment)

@router.get("/{appointment_id}", response_model=AppointmentRead)
async def get_appointment(appointment_id: UUID, db: AsyncSession = Depends(get_db)):
    appointment = await appointment_crud.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.get("/", response_model=list[AppointmentRead])
async def list_appointments(db: AsyncSession = Depends(get_db)):
    return await appointment_crud.list_appointments(db)

@router.put("/{appointment_id}", response_model=AppointmentRead)
async def update_appointment(appointment_id: UUID, appointment_data: AppointmentUpdate, db: AsyncSession = Depends(get_db)):
    appointment = await appointment_crud.update_appointment(db, appointment_id, appointment_data)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@router.delete("/{appointment_id}", response_model=dict)
async def delete_appointment(appointment_id: UUID, db: AsyncSession = Depends(get_db)):
    success = await appointment_crud.delete_appointment(db, appointment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"detail": "Appointment deleted successfully"}