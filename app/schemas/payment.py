from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class PaymentBase(BaseModel):
    user_id: UUID
    amount: float
    payment_method: str
    status: str = Field(..., pattern="^(pending|completed|failed)$")
    service_id: Optional[UUID]
    appointment_id: Optional[UUID]
    trainings_id: Optional[UUID]

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(PaymentBase):
    pass

class PaymentInDB(PaymentBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True