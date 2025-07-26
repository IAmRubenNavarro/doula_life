from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from enum import Enum

class ServiceType(str, Enum):
    consulting = "consulting"
    training = "training"

class ServiceBase(BaseModel):
    title: str
    description: Optional[str] = None
    service_type: ServiceType
    price: Optional[float]
    duration_minutes: Optional[int]
    is_active: Optional[bool]

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(ServiceBase):
    pass

class ServiceRead(ServiceBase):
    id: UUID

    class Config:
        from_attributes = True