from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.models.training_enrollment import TrainingEnrollment
from app.schemas.training_enrollment import TrainingEnrollmentCreate, TrainingEnrollmentUpdate

async def create_enrollment(db: AsyncSession, data: TrainingEnrollmentCreate) -> TrainingEnrollment:
    enrollment = TrainingEnrollment(**data.model_dump())
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment

async def get_enrollment(db: AsyncSession, enrollment_id: UUID) -> TrainingEnrollment | None:
    result = await db.execute(select(TrainingEnrollment).where(TrainingEnrollment.id == enrollment_id))
    return result.scalar_one_or_none()

async def list_enrollments(db: AsyncSession) -> list[TrainingEnrollment]:
    result = await db.execute(select(TrainingEnrollment))
    return result.scalars().all()

async def update_enrollment(db: AsyncSession, enrollment_id: UUID, data: TrainingEnrollmentUpdate) -> TrainingEnrollment | None:
    result = await db.execute(select(TrainingEnrollment).where(TrainingEnrollment.id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if enrollment:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(enrollment, field, value)
        await db.commit()
        await db.refresh(enrollment)

    return enrollment

async def delete_enrollment(db: AsyncSession, enrollment_id: UUID) -> bool:
    result = await db.execute(select(TrainingEnrollment).where(TrainingEnrollment.id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if enrollment:
        await db.delete(enrollment)
        await db.commit()
        return True
    return False