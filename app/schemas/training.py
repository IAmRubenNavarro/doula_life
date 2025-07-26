from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class TrainingBase(BaseModel):
    title: str
    description: Optional[str]
    location: Optional[str]
    date: datetime
    duration_minutes: Optional[int]

class TrainingCreate(TrainingBase):
    pass

class TrainingUpdate(TrainingBase):
    pass

class TrainingRead(TrainingBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True