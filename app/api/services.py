from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.schemas.service import ServiceCreate, ServiceRead, ServiceUpdate
from app.crud import service as service_crud
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/", response_model=ServiceRead)
async def create_service(
    service: ServiceCreate, db: AsyncSession = Depends(get_db)
) -> ServiceRead:
    return await service_crud.create_service(db=db, data=service)

@router.get("/{service_id}", response_model=ServiceRead)
async def get_service(
    service_id: UUID, db: AsyncSession = Depends(get_db)
) -> ServiceRead:
    service = await service_crud.get_service(db=db, service_id=service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.get("/", response_model=list[ServiceRead])
async def list_services(
    db: AsyncSession = Depends(get_db)
) -> list[ServiceRead]:
    return await service_crud.list_services(db=db)

@router.put("/{service_id}", response_model=ServiceRead)
async def update_service(
    service_id: UUID, service: ServiceUpdate, db: AsyncSession = Depends(get_db)
) -> ServiceRead:
    updated_service = await service_crud.update_service(db=db, service_id=service_id, updates=service)
    if not updated_service:
        raise HTTPException(status_code=404, detail="Service not found")
    return updated_service

@router.delete("/{service_id}", response_model=dict)
async def delete_service(
    service_id: UUID, db: AsyncSession = Depends(get_db)
) -> dict:
    success = await service_crud.delete_service(db=db, service_id=service_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"detail": "Service deleted successfully"}