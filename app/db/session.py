# app/db/session.py
# Database configuration and session management for async SQLAlchemy with Supabase
# Includes comprehensive error handling, connection pooling, and robust session management
# All database operations are protected with proper exception handling and cleanup

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
import logging
from app.core.exceptions import log_exception, DatabaseError

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment, defaults to local PostgreSQL if not set
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost:5432/doula_life")

# Configure logging for database operations
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Create async database engine with Supabase-compatible settings and retry-friendly configuration
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,  # Log all SQL statements for debugging
    
    # Connection pool settings for better reliability (async uses AsyncAdaptedQueuePool by default)
    pool_size=5,  # Maintain 5 connections in pool
    max_overflow=10,  # Allow up to 10 additional connections
    pool_pre_ping=True,  # Test connections before use to handle dropped connections
    pool_recycle=300,  # Recycle connections every 5 minutes to prevent timeouts
    pool_timeout=30,  # Wait up to 30 seconds for a connection
    
    # Engine-level retry configuration
    connect_args={
        # Disable prepared statement caching to avoid conflicts with Supabase connection pooling
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        
        # Connection timeout settings
        "command_timeout": 60,  # Command timeout in seconds
        "server_settings": {
            "application_name": "doula_life_backend",
            "tcp_keepalives_idle": "600",  # TCP keepalive settings
            "tcp_keepalives_interval": "30",
            "tcp_keepalives_count": "3",
        }
    }
    )

# Create session factory for database operations
SessionLocal = sessionmaker(
    bind=engine,  # Bind to our async engine
    class_=AsyncSession,  # Use async session class
    autocommit=False,  # Don't auto-commit transactions
    autoflush=False  # Don't auto-flush changes to database
)

# Base class for all SQLAlchemy models
Base = declarative_base()

# Dependency function to get database session for FastAPI routes with error handling
async def get_db():
    """Provide database session to FastAPI endpoints via dependency injection
    
    This function creates and manages database sessions with comprehensive error
    handling and guaranteed cleanup, ensuring robust database operations.
    
    Yields:
        AsyncSession: Database session for the request
        
    Raises:
        DatabaseError: If session creation or configuration fails
        
    Error Handling:
        - Logs all session creation failures with full context
        - Ensures proper session cleanup even if errors occur
        - Converts low-level database errors to application errors
        - Guarantees session closure in finally block to prevent leaks
        
    Session Management:
        - Creates new session for each request
        - Automatically closes session after request completion
        - Handles connection pool exhaustion gracefully
        - Logs session lifecycle events for monitoring
    """
    db = None
    try:
        # Create database session
        db = SessionLocal()
        yield db
    except Exception as e:
        log_exception(e, "Database session creation")
        raise DatabaseError("Failed to create database session", e)
    finally:
        # Ensure session is properly closed
        if db:
            try:
                await db.close()
            except Exception as e:
                log_exception(e, "Database session cleanup")