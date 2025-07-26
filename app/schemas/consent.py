from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class ConsentBase(BaseModel):
    user_id: UUID
    agreement: str

class ConsentCreate(ConsentBase):
    pass

class ConsentUpdate(BaseModel):
    agreement: str

class ConsentInDB(ConsentBase):
    id: UUID
    signed_at: datetime

    class Config:
        from_attributes = True
