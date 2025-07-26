import enum
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class AppointmentStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"

class AppointmentBase(BaseModel):
    user_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    appointment_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    state_id: Optional[int] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
        pass

class AppointmentUpdate(AppointmentBase):
        pass

class AppointmentRead(AppointmentBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True