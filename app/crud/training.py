from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.models.training import Training
from app.schemas.training import TrainingCreate, TrainingUpdate

async def create_training(db: AsyncSession, training: TrainingCreate) -> Training:
    training_obj = Training(**training.model_dump())
    db.add(training_obj)
    await db.commit()
    await db.refresh(training_obj)
    return training_obj

async def get_training(db: AsyncSession, training_id: UUID) -> Training | None:
     result = await db.execute(select(Training).where(Training.id == training_id))
     return result.scalar_one_or_none()

async def list_trainings(db: AsyncSession) -> list[Training]:
    result = await db.execute(select(Training))
    return result.scalars().all()

async def update_training(db: AsyncSession, training_id: UUID, training_data: TrainingUpdate) -> Training | None:
    result = await db.execute(select(Training).where(Training.id == training_id))
    training = result.scalar_one_or_none()
    if training:
        for field, value in training_data.model_dump(exclude_unset=True).items():
            setattr(training, field, value)
        await db.commit()
        await db.refresh(training)
    return training

async def delete_training(db: AsyncSession, training_id: UUID) -> bool:
    result = await db.execute(select(Training).where(Training.id == training_id))
    training = result.scalar_one_or_none()
    if training:
        await db.delete(training)
        await db.commit()
        return True
    return False
