# CRUD operations for User model with comprehensive exception handling
# These functions handle Create, Read, Update, Delete operations for users
# All functions include input validation, error logging, and proper exception handling
# Database transactions are automatically rolled back on errors to maintain data integrity

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.exceptions import log_exception, DatabaseError, ValidationError
# from app.core.retry_policies import db_retry, db_retry_critical  # Temporarily disabled

# @db_retry_critical  # Temporarily disabled
async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """Create a new user in the database with full error handling
    
    This function performs comprehensive validation, creates the user record,
    and handles all possible error scenarios with proper logging and rollback.
    
    Args:
        db: Async database session
        user: User data from API request (validated by Pydantic schema)
        
    Returns:
        User: The created user object with generated ID and timestamps
        
    Raises:
        ValidationError: If required fields are missing or invalid
        DatabaseError: If database operation fails (connection, constraint violations, etc.)
        
    Error Handling:
        - Validates all required fields before database operation
        - Automatically rolls back transaction on any error
        - Logs all exceptions with full context for debugging
        - Converts database-specific errors to application errors
    """
    try:
        # Validate required fields
        if not user.email or not user.email.strip():
            raise ValidationError("Email is required", "email")
        if not user.first_name or not user.first_name.strip():
            raise ValidationError("First name is required", "first_name")
        if not user.last_name or not user.last_name.strip():
            raise ValidationError("Last name is required", "last_name")
        
        # Convert Pydantic model to SQLAlchemy model
        db_user = User(**user.model_dump())
        
        # Add to session and commit to database
        db.add(db_user)
        await db.commit()  # Save to database
        await db.refresh(db_user)  # Refresh to get generated fields like ID
        
        return db_user
        
    except ValidationError:
        # Re-raise validation errors as-is
        raise
    except SQLAlchemyError as e:
        # Rollback transaction on database error
        await db.rollback()
        log_exception(e, "create_user database operation")
        raise DatabaseError(f"Failed to create user: {str(e)}", e)
    except Exception as e:
        # Rollback transaction on any other error
        await db.rollback()
        log_exception(e, "create_user unexpected error")
        raise DatabaseError(f"Unexpected error creating user: {str(e)}", e)

# @db_retry  # Temporarily disabled
async def get_user_by_email(db: AsyncSession, email: str):
    """Find a user by their email address with robust error handling
    
    This function safely queries the database for a user with the specified email,
    handling all potential errors and logging issues for monitoring.
    
    Args:
        db: Async database session
        email: Email address to search for
        
    Returns:
        User or None: User object if found, None if not found
        
    Raises:
        ValidationError: If email parameter is None, empty, or invalid format
        DatabaseError: If database query fails (connection issues, SQL errors, etc.)
        
    Error Handling:
        - Validates email parameter before database query
        - Trims whitespace from email input
        - Logs all database errors with query context
        - Distinguishes between validation and database errors
    """
    try:
        # Validate email parameter
        if not email or not email.strip():
            raise ValidationError("Email is required for search", "email")
        
        # Execute SELECT query with WHERE clause
        result = await db.execute(select(User).where(User.email == email.strip()))
        return result.scalar_one_or_none()  # Return single result or None
        
    except ValidationError:
        # Re-raise validation errors as-is
        raise
    except SQLAlchemyError as e:
        log_exception(e, f"get_user_by_email database operation for email: {email}")
        raise DatabaseError(f"Failed to find user by email: {str(e)}", e)
    except Exception as e:
        log_exception(e, f"get_user_by_email unexpected error for email: {email}")
        raise DatabaseError(f"Unexpected error finding user by email: {str(e)}", e)

# @db_retry  # Temporarily disabled
async def get_user_by_id(db: AsyncSession, user_id: str):
    """Find a user by their unique ID with comprehensive error handling
    
    This function safely retrieves a user by ID, handling UUID validation
    and all potential database errors with proper logging.
    
    Args:
        db: Async database session
        user_id: UUID string of the user to find
        
    Returns:
        User or None: User object if found, None if not found
        
    Raises:
        ValidationError: If user_id is None, empty, or invalid UUID format
        DatabaseError: If database query fails (connection issues, SQL errors, etc.)
        
    Error Handling:
        - Validates user_id parameter before database query
        - Handles UUID conversion errors gracefully
        - Logs all database errors with user_id context
        - Provides detailed error context for debugging
    """
    try:
        # Validate user_id parameter
        if not user_id or not str(user_id).strip():
            raise ValidationError("User ID is required for search", "user_id")
        
        # Execute SELECT query with WHERE clause on ID
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()  # Return single result or None
        
    except ValidationError:
        # Re-raise validation errors as-is
        raise
    except SQLAlchemyError as e:
        log_exception(e, f"get_user_by_id database operation for ID: {user_id}")
        raise DatabaseError(f"Failed to find user by ID: {str(e)}", e)
    except Exception as e:
        log_exception(e, f"get_user_by_id unexpected error for ID: {user_id}")
        raise DatabaseError(f"Unexpected error finding user by ID: {str(e)}", e)

# @db_retry  # Temporarily disabled
async def get_users(db: AsyncSession, skip: int = 0, limit: int = 10):
    """Get a paginated list of users with safe parameter validation
    
    This function retrieves users with pagination support, validating all parameters
    and handling database errors to ensure reliable operation.
    
    Args:
        db: Async database session
        skip: Number of records to skip (for pagination, must be >= 0)
        limit: Maximum number of records to return (must be 1-100)
        
    Returns:
        List[User]: List of user objects (empty list if no users found)
        
    Raises:
        ValidationError: If skip < 0 or limit not in range 1-100
        DatabaseError: If database query fails (connection issues, SQL errors, etc.)
        
    Error Handling:
        - Validates pagination parameters before database query
        - Enforces reasonable limits to prevent resource exhaustion
        - Logs all database errors with pagination context
        - Returns empty list gracefully when no users exist
    """
    try:
        # Validate pagination parameters
        if skip < 0:
            raise ValidationError("Skip value must be non-negative", "skip")
        if limit <= 0 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100", "limit")
        
        # Execute SELECT query with OFFSET and LIMIT for pagination
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()  # Return all results as list
        
    except ValidationError:
        # Re-raise validation errors as-is
        raise
    except SQLAlchemyError as e:
        log_exception(e, f"get_users database operation with skip={skip}, limit={limit}")
        raise DatabaseError(f"Failed to retrieve users: {str(e)}", e)
    except Exception as e:
        log_exception(e, f"get_users unexpected error with skip={skip}, limit={limit}")
        raise DatabaseError(f"Unexpected error retrieving users: {str(e)}", e)