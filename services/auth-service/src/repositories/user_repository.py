"""
User repository for database operations.

Handles CRUD operations for users in the auth schema.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.user import User
from shared.common.exceptions import NotFoundException, ConflictException
from shared.common.logging import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Repository for User model database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def create(self, email: str, password_hash: str, role: str) -> User:
        """
        Create new user.
        
        Args:
            email: User email address
            password_hash: Hashed password
            role: User role ('employee' or 'manager')
            
        Returns:
            Created User object
            
        Raises:
            ConflictException: If email already exists
        """
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"User created: {user.id}")
            return user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"User creation failed: {str(e)}")
            raise ConflictException(detail=f"User with email {email} already exists")
    
    def update(self, user_id: UUID, **kwargs) -> User:
        """
        Update user fields.
        
        Args:
            user_id: User UUID
            **kwargs: Fields to update
            
        Returns:
            Updated User object
            
        Raises:
            NotFoundException: If user not found
        """
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"User updated: {user.id}")
        return user
    
    def delete(self, user_id: UUID) -> None:
        """
        Delete user (soft delete by setting is_active=False).
        
        Args:
            user_id: User UUID
            
        Raises:
            NotFoundException: If user not found
        """
        user = self.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        
        user.is_active = False
        self.db.commit()
        logger.info(f"User deactivated: {user.id}")
