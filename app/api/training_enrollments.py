from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID

from app.schemas.training_enrollment import (
    TrainingEnrollmentCreate,
    TrainingEnrollmentUpdate,
    TrainingEnrollmentRead,
)

from app.crud import training_enrollment as enrollment_crud
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/", response_model=TrainingEnrollmentRead)
async def create_enrollment(
    enrollment: TrainingEnrollmentCreate,
    db: AsyncSession = Depends(get_db)
) -> TrainingEnrollmentRead:
    """Create a new training enrollment."""
    return await enrollment_crud.create_enrollment(db, enrollment)

@router.get("/{enrollment_id}", response_model=TrainingEnrollmentRead)
async def get_enrollment(
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> TrainingEnrollmentRead:
    """Get a training enrollment by ID."""
    enrollment = await enrollment_crud.get_enrollment(db, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment

@router.get("/", response_model=list[TrainingEnrollmentRead])
async def list_enrollments(
    db: AsyncSession = Depends(get_db)
) -> list[TrainingEnrollmentRead]:
    """List all training enrollments."""
    return await enrollment_crud.list_enrollments(db)

@router.put("/{enrollment_id}", response_model=TrainingEnrollmentRead)
async def update_enrollment(
    enrollment_id: UUID,
    enrollment_data: TrainingEnrollmentUpdate,
    db: AsyncSession = Depends(get_db)
) -> TrainingEnrollmentRead:
    """Update a training enrollment."""
    enrollment = await enrollment_crud.update_enrollment(db, enrollment_id, enrollment_data)
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment

@router.delete("/{enrollment_id}", response_model=dict)
async def delete_enrollment(
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a training enrollment."""
    success = await enrollment_crud.delete_enrollment(db, enrollment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return {"detail": "Enrollment deleted successfully"}