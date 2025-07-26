# Centralized exception handling and error utilities
# Provides consistent error handling, logging, and custom exceptions across the application

import logging
import traceback
from typing import Optional, Any, Dict
from fastapi import HTTPException
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    DataError,
    OperationalError,
    TimeoutError,
    DisconnectionError
)
import asyncpg.exceptions

# Configure logger for exception handling
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Custom exception for database-related errors"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

class ValidationError(Exception):
    """Custom exception for data validation errors"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

class BusinessLogicError(Exception):
    """Custom exception for business logic violations"""
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

def log_exception(
    error: Exception, 
    context: str, 
    user_id: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log exception with full context and stack trace
    
    Args:
        error: The exception that occurred
        context: Description of where/when the error occurred
        user_id: Optional user ID for user-specific errors
        additional_data: Optional additional context data
    """
    error_details = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "user_id": user_id,
        "additional_data": additional_data or {},
        "stack_trace": traceback.format_exc()
    }
    
    logger.error(f"Exception in {context}: {error_details}")

def handle_database_error(error: Exception, operation: str) -> HTTPException:
    """
    Convert database errors to appropriate HTTP exceptions
    
    Args:
        error: Database exception
        operation: Description of the operation that failed
        
    Returns:
        HTTPException: Appropriate HTTP exception for the client
    """
    log_exception(error, f"Database operation: {operation}")
    
    # Handle specific database errors
    if isinstance(error, IntegrityError):
        if "unique constraint" in str(error).lower():
            return HTTPException(
                status_code=409,
                detail="Resource already exists with this information"
            )
        elif "foreign key constraint" in str(error).lower():
            return HTTPException(
                status_code=400,
                detail="Referenced resource does not exist"
            )
        else:
            return HTTPException(
                status_code=400,
                detail="Data integrity constraint violated"
            )
    
    elif isinstance(error, DataError):
        return HTTPException(
            status_code=400,
            detail="Invalid data format provided"
        )
    
    elif isinstance(error, (OperationalError, TimeoutError, DisconnectionError)):
        return HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Please try again later."
        )
    
    elif isinstance(error, asyncpg.exceptions.PostgresError):
        # Handle asyncpg specific errors
        if hasattr(error, 'sqlstate'):
            if error.sqlstate == '23505':  # Unique violation
                return HTTPException(
                    status_code=409,
                    detail="Resource already exists"
                )
            elif error.sqlstate == '23503':  # Foreign key violation
                return HTTPException(
                    status_code=400,
                    detail="Referenced resource does not exist"
                )
        
        return HTTPException(
            status_code=500,
            detail="Database error occurred"
        )
    
    elif isinstance(error, SQLAlchemyError):
        return HTTPException(
            status_code=500,
            detail="Database operation failed"
        )
    
    else:
        # Generic error
        return HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

def handle_validation_error(error: Exception, field: Optional[str] = None) -> HTTPException:
    """
    Convert validation errors to appropriate HTTP exceptions
    
    Args:
        error: Validation exception
        field: Optional field name that failed validation
        
    Returns:
        HTTPException: Appropriate HTTP exception for the client
    """
    log_exception(error, f"Validation error on field: {field}")
    
    detail = str(error)
    if field:
        detail = f"Validation failed for field '{field}': {detail}"
    
    return HTTPException(
        status_code=422,
        detail=detail
    )

def handle_business_logic_error(error: Exception, operation: str) -> HTTPException:
    """
    Convert business logic errors to appropriate HTTP exceptions
    
    Args:
        error: Business logic exception
        operation: Description of the business operation that failed
        
    Returns:
        HTTPException: Appropriate HTTP exception for the client
    """
    log_exception(error, f"Business logic error in: {operation}")
    
    return HTTPException(
        status_code=400,
        detail=str(error)
    )

def safe_execute(func, *args, **kwargs):
    """
    Safely execute a function with comprehensive error handling
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or raises appropriate exception
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_exception(e, f"Error executing function {func.__name__}")
        raise

async def safe_execute_async(func, *args, **kwargs):
    """
    Safely execute an async function with comprehensive error handling
    
    Args:
        func: Async function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or raises appropriate exception
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        log_exception(e, f"Error executing async function {func.__name__}")
        raise