from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router as api_router
from app.core.config import settings
from app.core.logging_config import get_logger
from app.core.exceptions import log_exception
import logging

# Initialize logging
logger = get_logger(__name__)

app = FastAPI(
    title="Doula Life Backend API",
    description="Backend API for Doula Life application",
    version="1.0.0"
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to catch and log all unhandled exceptions"""
    log_exception(
        exc, 
        f"Unhandled exception in {request.method} {request.url}",
        additional_data={
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "path_params": request.path_params,
            "query_params": dict(request.query_params)
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "error_id": str(id(exc))  # Unique error ID for tracking
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("🚀 Doula Life Backend API starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("Application startup completed successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown"""
    logger.info("🛑 Doula Life Backend API shutting down...")
    logger.info("Application shutdown completed")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add API routes
app.include_router(api_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "doula-life-backend",
            "version": "1.0.0"
        }
    except Exception as e:
        log_exception(e, "Health check endpoint")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "doula-life-backend",
                "error": "Service check failed"
            }
        )

# Log that the module has been loaded
logger.info("FastAPI application configured successfully")

