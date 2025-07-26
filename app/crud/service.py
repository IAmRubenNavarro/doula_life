from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from uuid import UUID
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceUpdate

async def create_service(db: AsyncSession, data: ServiceCreate) -> Service:
    service = Service(**data.dict())    
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service

async def get_service(db: AsyncSession, service_id: UUID) -> Service:
    result = await db.execute(select(Service).where(Service.id == service_id))
    return result.scalar_one_or_none()

async def list_services(db: AsyncSession) -> list[Service]:
    result = await db.execute(select(Service).where(Service.is_active == True))
    return result.scalars().all()

async def update_service(db: AsyncSession, service_id: UUID, data: ServiceUpdate) -> Service:
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if service:
        for field, value in data.dict(exclude_unset=True).items():
            setattr(service, field, value)
        await db.commit()
        await db.refresh(service)
    return service

async def delete_service(db: AsyncSession, service_id: UUID) -> bool:
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalar_one_or_none()
    if service:
        await db.delete(service)
        await db.commit()
        return True
    return False