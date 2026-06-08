"""Authentication endpoints for auth service."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, LogoutRequest, UserResponse
from src.services.auth_service import AuthService
from shared.common.auth import get_current_user
from shared.common.schemas import UserContext, MessageResponse
from shared.common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    User login endpoint.
    
    Authenticates user credentials and returns JWT access + refresh tokens.
    """
    auth_service = AuthService(db)
    return auth_service.login(request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token endpoint.
    
    Uses refresh token to generate new access token.
    """
    auth_service = AuthService(db)
    return auth_service.refresh(request.refresh_token)


@router.get("/verify", response_model=UserResponse)
async def verify_token(current_user: UserContext = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Verify JWT token endpoint.
    
    Used by NGINX or other services to validate tokens.
    Returns user information if token is valid.
    """
    from src.repositories.user_repository import UserRepository
    
    repo = UserRepository(db)
    user = repo.get_by_id(current_user.user_id)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: LogoutRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout endpoint.
    
    Blacklists the refresh token (in production, maintain blacklist in Redis).
    For MVP, we simply return success - client should discard tokens.
    """
    # In production: Add refresh_token to Redis blacklist with TTL
    # For MVP: Client-side token removal is sufficient
    
    logger.info(f"User logged out: {current_user.email}")
    
    return MessageResponse(
        message="Logged out successfully",
        data={"user_id": str(current_user.user_id)}
    )
