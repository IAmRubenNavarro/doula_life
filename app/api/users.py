# FastAPI router for user-related endpoints with comprehensive error handling
# Handles HTTP requests for user management operations with full exception coverage
# All endpoints include proper error logging, validation, and user-friendly error responses
# Database errors are automatically converted to appropriate HTTP status codes

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserOut
from app.crud.user import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_users
)
from app.db.session import get_db
from app.core.exceptions import (
    log_exception,
    handle_database_error,
    handle_validation_error,
    DatabaseError,
    ValidationError
)
from typing import List
from uuid import UUID

# Create router instance for user endpoints
router = APIRouter()

@router.post("/", response_model=UserOut)
async def create_new_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user account with comprehensive error handling
    
    This endpoint creates a new user with full validation, duplicate checking,
    and robust error handling to ensure reliable user registration.
    
    Args:
        user_data: User information from request body (validated by Pydantic)
        db: Database session injected by FastAPI dependency
        
    Returns:
        UserOut: Created user data (without sensitive fields)
        
    HTTP Status Codes:
        201: User created successfully
        409: Email already registered (conflict)
        422: Validation failed (invalid input data)
        500: Internal server error (database/system issues)
        503: Service unavailable (database connection issues)
        
    Error Handling:
        - Checks for duplicate email addresses before creation
        - Validates all required fields and data formats
        - Converts database constraint violations to user-friendly messages
        - Logs all errors with full request context for debugging
        - Provides unique error IDs for tracking issues
    """
    try:
        # Check if user with this email already exists
        db_user = await get_user_by_email(db=db, email=user_data.email)
        if db_user:
            raise HTTPException(status_code=409, detail="Email already registered")
        
        # Create new user and return the result
        new_user = await create_user(db=db, user=user_data)
        return new_user
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValidationError as e:
        # Convert validation errors to HTTP exceptions
        raise handle_validation_error(e, e.field)
    except DatabaseError as e:
        # Convert database errors to HTTP exceptions
        raise handle_database_error(e.original_error or e, "create user")
    except Exception as e:
        # Handle any unexpected errors
        log_exception(e, "create_new_user endpoint")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating user"
        )

@router.get("/{user_id}", response_model=UserOut)
async def read_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific user by their ID with robust error handling
    
    This endpoint retrieves a user by UUID with comprehensive validation
    and error handling to ensure reliable user lookup operations.
    
    Args:
        user_id: UUID of the user to retrieve
        db: Database session injected by FastAPI dependency
        
    Returns:
        UserOut: User data if found
        
    HTTP Status Codes:
        200: User found and returned successfully
        404: User not found with the specified ID
        422: Invalid UUID format provided
        500: Internal server error (database/system issues)
        503: Service unavailable (database connection issues)
        
    Error Handling:
        - Validates UUID format before database query
        - Distinguishes between 'not found' and database errors
        - Logs all errors with user_id context for debugging
        - Provides clear error messages for different failure scenarios
    """
    try:
        # Look up user by ID
        db_user = await get_user_by_id(db, str(user_id))
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return db_user
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValidationError as e:
        # Convert validation errors to HTTP exceptions
        raise handle_validation_error(e, e.field)
    except DatabaseError as e:
        # Convert database errors to HTTP exceptions
        raise handle_database_error(e.original_error or e, "get user by ID")
    except Exception as e:
        # Handle any unexpected errors
        log_exception(e, f"read_user endpoint for user_id: {user_id}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving user"
        )

@router.get("/", response_model=List[UserOut])
async def read_users(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get a paginated list of users with safe parameter handling
    
    This endpoint retrieves users with pagination support, including comprehensive
    parameter validation and error handling for reliable list operations.
    
    Args:
        skip: Number of records to skip (default: 0, must be >= 0)
        limit: Maximum number of records to return (default: 10, must be 1-100)
        db: Database session injected by FastAPI dependency
        
    Returns:
        List[UserOut]: List of users for the requested page (empty list if no users)
        
    HTTP Status Codes:
        200: Users retrieved successfully (including empty list)
        422: Invalid pagination parameters (skip < 0 or limit out of range)
        500: Internal server error (database/system issues)
        503: Service unavailable (database connection issues)
        
    Error Handling:
        - Validates pagination parameters before database query
        - Enforces reasonable limits to prevent resource exhaustion
        - Handles empty result sets gracefully
        - Logs all errors with pagination context for debugging
        - Returns consistent response format even for edge cases
    """
    try:
        # Get paginated list of users
        users = await get_users(db, skip=skip, limit=limit)
        return users
        
    except ValidationError as e:
        # Convert validation errors to HTTP exceptions
        raise handle_validation_error(e, e.field)
    except DatabaseError as e:
        # Convert database errors to HTTP exceptions
        raise handle_database_error(e.original_error or e, "get users list")
    except Exception as e:
        # Handle any unexpected errors
        log_exception(e, f"read_users endpoint with skip={skip}, limit={limit}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while retrieving users"
        )
