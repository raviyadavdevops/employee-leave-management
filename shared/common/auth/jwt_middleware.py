"""
JWT authentication middleware and dependencies for FastAPI.

Provides JWT token validation and user context extraction for protected endpoints.
"""

import os
from typing import Optional
from datetime import datetime, timezone
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from pydantic import UUID4, ValidationError

from shared.common.schemas.user import TokenPayload, UserContext, UserRole
from shared.common.exceptions import UnauthorizedException, ForbiddenException
from shared.common.logging import get_logger

logger = get_logger(__name__)

# JWT configuration from environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def decode_token(token: str, expected_type: str = "access") -> TokenPayload:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded token payload
        
    Raises:
        UnauthorizedException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        
        # Validate token payload
        token_data = TokenPayload(**payload)
        
        # Check expiration
        if token_data.exp:
            exp_datetime = datetime.fromtimestamp(token_data.exp, tz=timezone.utc)
            if exp_datetime < datetime.now(timezone.utc):
                raise UnauthorizedException(detail="Token has expired")
        
        # Verify expected token type
        if token_data.type != expected_type:
            raise UnauthorizedException(detail=f"Invalid token type. Expected {expected_type}")
            
        return token_data
        
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise UnauthorizedException(detail="Invalid authentication token")
    except ValidationError as e:
        logger.error(f"Token payload validation error: {str(e)}")
        raise UnauthorizedException(detail="Invalid token payload")


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> UserContext:
    """
    Dependency to extract authenticated user from JWT token.
    
    Args:
        authorization: Authorization header value (Bearer token)
        
    Returns:
        User context with ID, email, and role
        
    Raises:
        UnauthorizedException: If no token provided or token is invalid
    """
    if not authorization:
        raise UnauthorizedException(detail="Authorization header missing")
    
    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedException(detail="Invalid authorization header format. Expected 'Bearer <token>'")
    
    token = parts[1]
    
    # Decode token
    token_data = decode_token(token)
    
    # Return user context
    return UserContext(
        user_id=token_data.sub,
        email=token_data.email,
        role=token_data.role
    )


async def get_current_manager(
    current_user: UserContext = Depends(get_current_user)
) -> UserContext:
    """
    Dependency to ensure current user has manager role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User context (guaranteed to be a manager)
        
    Raises:
        ForbiddenException: If user is not a manager
    """
    if not current_user.is_manager():
        raise ForbiddenException(detail="Manager role required")
    
    return current_user


async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[UserContext]:
    """
    Dependency to extract authenticated user from JWT token if present.
    
    Returns None if no token provided, validates if present.
    
    Args:
        authorization: Authorization header value (Bearer token)
        
    Returns:
        User context or None if not authenticated
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except UnauthorizedException:
        return None
