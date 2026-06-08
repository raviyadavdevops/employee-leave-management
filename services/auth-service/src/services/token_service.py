"""
JWT token service for token generation and management.

Handles creation of access and refresh tokens.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from uuid import UUID
from jose import jwt

from shared.common.logging import get_logger

logger = get_logger(__name__)

# JWT configuration from environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class TokenService:
    """Service for JWT token operations."""
    
    @staticmethod
    def create_access_token(
        user_id: UUID,
        email: str,
        role: str,
        expires_delta: timedelta = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            user_id: User UUID
            email: User email
            role: User role
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload: Dict[str, Any] = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        
        encoded_jwt = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        logger.info(f"Access token created for user {user_id}")
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        user_id: UUID,
        email: str,
        role: str,
        expires_delta: timedelta = None
    ) -> str:
        """
        Create JWT refresh token.
        
        Args:
            user_id: User UUID
            email: User email
            role: User role
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload: Dict[str, Any] = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        
        encoded_jwt = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        logger.info(f"Refresh token created for user {user_id}")
        return encoded_jwt
    
    @staticmethod
    def get_access_token_expires_in() -> int:
        """
        Get access token expiration time in seconds.
        
        Returns:
            Expiration time in seconds
        """
        return ACCESS_TOKEN_EXPIRE_MINUTES * 60
