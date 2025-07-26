from fastapi import APIRouter
from app.core.ai_tools import generate_care_plan

router = APIRouter()

@router.post("/care_plan")
async def create_care_plan(session_notes: str):
    return generate_care_plan(session_notes)