from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class TrainingEnrollmentBase(BaseModel):
    user_id: UUID
    training_id: UUID
    payment_status: Optional[str] = "pending"
    passed_assessment: Optional[bool] = None

class TrainingEnrollmentCreate(TrainingEnrollmentBase):
    pass

class TrainingEnrollmentUpdate(TrainingEnrollmentBase):
    pass

class TrainingEnrollmentRead(TrainingEnrollmentBase):
    id: UUID
    enrolled_at: datetime

    class Config:
        from_attributes = True