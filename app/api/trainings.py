from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID

from app.schemas.training import TrainingCreate, TrainingUpdate, TrainingRead
from app.crud import training as training_crud
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/", response_model=TrainingRead)
async def create_training(
    training: TrainingCreate,
    db: AsyncSession = Depends(get_db)
) -> TrainingRead:
    """Create a new training session."""
    return await training_crud.create_training(db, training)

@router.get("/{training_id}", response_model=TrainingRead)
async def get_training(
    training_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> TrainingRead:
    """Get a training session by ID."""
    training = await training_crud.get_training(db, training_id)
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    return training

@router.get("/", response_model=list[TrainingRead])
async def list_trainings(
    db: AsyncSession = Depends(get_db)
) -> list[TrainingRead]:
    """List all training sessions."""
    return await training_crud.list_trainings(db)

@router.put("/{training_id}", response_model=TrainingRead)
async def update_training(
    training_id: UUID,
    training_data: TrainingUpdate,
    db: AsyncSession = Depends(get_db)
) -> TrainingRead:
    """Update a training session."""
    training = await training_crud.update_training(db, training_id, training_data)
    if not training:
        raise HTTPException(status_code=404, detail="Training not found")
    return training

@router.delete("/{training_id}", response_model=dict)
async def delete_training(
    training_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a training session."""
    success = await training_crud.delete_training(db, training_id)
    if not success:
        raise HTTPException(status_code=404, detail="Training not found")
    return {"detail": "Training deleted successfully"}