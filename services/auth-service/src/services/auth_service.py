"""
Authentication service business logic.

Handles login, token refresh, and logout operations.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session

from src.repositories.user_repository import UserRepository
from src.services.security import verify_password, hash_password
from src.services.token_service import TokenService
from src.schemas.auth import LoginRequest, TokenResponse, RegisterUserRequest
from shared.common.exceptions import UnauthorizedException, BadRequestException
from shared.common.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: Session):
        """
        Initialize auth service.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_service = TokenService()
    
    def login(self, request: LoginRequest) -> TokenResponse:
        """
        Authenticate user and generate tokens.
        
        Args:
            request: Login request with email and password
            
        Returns:
            Token response with access and refresh tokens
            
        Raises:
            UnauthorizedException: If credentials are invalid
        """
        # Get user by email
        user = self.user_repo.get_by_email(request.email)
        if not user:
            logger.warning(f"Login attempt for non-existent user: {request.email}")
            raise UnauthorizedException(detail="Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {request.email}")
            raise UnauthorizedException(detail="Account is inactive")
        
        # Verify password
        if not verify_password(request.password, user.password_hash):
            logger.warning(f"Invalid password for user: {request.email}")
            raise UnauthorizedException(detail="Invalid email or password")
        
        # Generate tokens
        access_token = self.token_service.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role
        )
        
        refresh_token = self.token_service.create_refresh_token(
            user_id=user.id,
            email=user.email,
            role=user.role
        )
        
        logger.info(f"User logged in successfully: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.token_service.get_access_token_expires_in()
        )
    
    def refresh(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New token response with fresh access token
            
        Raises:
            UnauthorizedException: If refresh token is invalid
        """
        # Decode refresh token (validation happens in decode_token)
        from shared.common.auth.jwt_middleware import decode_token
        
        try:
            token_data = decode_token(refresh_token, expected_type="refresh")
        except UnauthorizedException:
            raise UnauthorizedException(detail="Invalid or expired refresh token")
        
        # Get user to ensure they still exist and are active
        user = self.user_repo.get_by_id(token_data.sub)
        if not user or not user.is_active:
            raise UnauthorizedException(detail="User not found or inactive")
        
        # Generate new access token
        access_token = self.token_service.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role
        )
        
        logger.info(f"Access token refreshed for user: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Return same refresh token
            token_type="bearer",
            expires_in=self.token_service.get_access_token_expires_in()
        )
    
    def register(self, request: RegisterUserRequest) -> Dict[str, Any]:
        """
        Register a new user (internal use / testing).
        
        Args:
            request: User registration request
            
        Returns:
            Dictionary with user ID and email
            
        Raises:
            BadRequestException: If role is invalid
        """
        # Validate role
        if request.role not in ["employee", "manager"]:
            raise BadRequestException(detail="Invalid role. Must be 'employee' or 'manager'")
        
        # Hash password
        password_hash = hash_password(request.password)
        
        # Create user
        user = self.user_repo.create(
            email=request.email,
            password_hash=password_hash,
            role=request.role
        )
        
        logger.info(f"New user registered: {user.email}")
        
        return {
            "id": str(user.id),
            "email": user.email,
            "role": user.role
        }
