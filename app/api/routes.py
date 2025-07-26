# app/api/routes.py

from fastapi import APIRouter

# Module routers
from app.api.users import router as user_router
from app.api.services import router as services_router
from app.api.appointments import router as appointments_router
from app.api.trainings import router as trainings_router
from app.api.training_enrollments import router as enrollments_router
from app.api.payments import router as payments_router
from app.api.consents import router as consents_router
from app.api.ping import router as ping_router
from app.api.ai import router as ai_router

# Auth router
from app.auth.auth_routes import router as auth_router

# Main router
router = APIRouter()

# Register all route modules with proper prefixes
router.include_router(ping_router, prefix="/ping", tags=["Health"])
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(user_router, prefix="/users", tags=["Users"])
router.include_router(services_router, prefix="/services", tags=["Services"])
router.include_router(appointments_router, prefix="/appointments", tags=["Appointments"])
router.include_router(trainings_router, prefix="/trainings", tags=["Trainings"])
router.include_router(enrollments_router, prefix="/enrollments", tags=["Enrollments"])
router.include_router(payments_router, prefix="/payments", tags=["Payments"])
router.include_router(consents_router, prefix="/consents", tags=["Consents"])
router.include_router(ai_router, prefix="/ai", tags=["AI"])
