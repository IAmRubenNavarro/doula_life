# Retry policies for database operations
# Handles transient failures and connection issues with configurable retry strategies
#
# ACTIVE: Re-enabled and extended retry logic for production resilience
# - User operations: @db_retry and @db_retry_critical decorators active
# - Payment operations: Full retry protection on all CRUD operations  
# - Appointment operations: Critical operations protected with aggressive retry
#
# This provides automatic recovery from temporary database connection issues,
# network timeouts, and connection pool exhaustion scenarios.

import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
from sqlalchemy.exc import (
    DisconnectionError,
    TimeoutError,
    OperationalError,
    InterfaceError
)
import asyncpg.exceptions

# Configure logger for retry operations
logger = logging.getLogger(__name__)

# Database exceptions that should trigger retries
DATABASE_RETRY_EXCEPTIONS = (
    # SQLAlchemy exceptions
    DisconnectionError,    # Database connection lost
    TimeoutError,         # Query timeout
    OperationalError,     # General database operational error
    InterfaceError,       # Database interface error
    
    # asyncpg specific exceptions
    asyncpg.exceptions.ConnectionDoesNotExistError,  # Connection doesn't exist
    asyncpg.exceptions.ConnectionFailureError,       # Connection failed
    asyncpg.exceptions.PostgresConnectionError,      # PostgreSQL connection error
    asyncpg.exceptions.TooManyConnectionsError,      # Connection pool exhausted
)

def db_retry_policy():
    """
    Retry decorator for database operations with exponential backoff
    
    Configuration:
    - Max attempts: 3 (initial + 2 retries)
    - Wait strategy: Exponential backoff starting at 1 second, max 10 seconds
    - Only retries on specific database connection/timeout exceptions
    - Logs retry attempts for monitoring
    
    Returns:
        tenacity.retry: Configured retry decorator
    """
    return retry(
        # Stop after 3 total attempts (1 initial + 2 retries)
        stop=stop_after_attempt(3),
        
        # Exponential backoff: 1s, 2s, 4s, 8s, 10s (max)
        wait=wait_exponential(multiplier=1, min=1, max=10),
        
        # Only retry on specific database exceptions
        retry=retry_if_exception_type(DATABASE_RETRY_EXCEPTIONS),
        
        # Log before each retry attempt
        before_sleep=before_sleep_log(logger, logging.WARNING),
        
        # Log after final attempt (success or failure)
        after=after_log(logger, logging.INFO),
        
        # Re-raise the last exception if all retries fail
        reraise=True
    )

def db_retry_policy_aggressive():
    """
    More aggressive retry policy for critical operations
    
    Configuration:
    - Max attempts: 5 (initial + 4 retries)
    - Wait strategy: Exponential backoff starting at 0.5 seconds, max 30 seconds
    - Suitable for critical operations that must succeed
    
    Returns:
        tenacity.retry: Configured retry decorator for critical operations
    """
    return retry(
        # Stop after 5 total attempts
        stop=stop_after_attempt(5),
        
        # More aggressive backoff: 0.5s, 1s, 2s, 4s, 8s, 16s, 30s (max)
        wait=wait_exponential(multiplier=0.5, min=0.5, max=30),
        
        # Same exceptions as regular policy
        retry=retry_if_exception_type(DATABASE_RETRY_EXCEPTIONS),
        
        # Log retry attempts
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        
        # Re-raise the last exception if all retries fail
        reraise=True
    )

# Pre-configured decorators for easy use
db_retry = db_retry_policy()
db_retry_critical = db_retry_policy_aggressive()