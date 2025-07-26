from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email: EmailStr
    role: str

class UserCreate(UserBase):
    pass

class UserOut(UserBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
