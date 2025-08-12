"""User model for birthday API."""
import re
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """User model for storing birthday information."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __init__(self, username: str = None, date_of_birth: date = None, **kwargs):
        """Initialize User with validation."""
        if username is not None:
            self._validate_username(username)
        if date_of_birth is not None:
            self._validate_date_of_birth(date_of_birth)
        super().__init__(username=username, date_of_birth=date_of_birth, **kwargs)
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        from datetime import datetime
        self.updated_at = datetime.now()
    
    __table_args__ = (
        UniqueConstraint('username', name='uq_users_username'),
    )
    
    def _validate_username(self, username: str) -> None:
        """Validate username format."""
        if not username:
            raise ValueError("Username cannot be empty")
        
        if len(username) > 64:
            raise ValueError("Username cannot be longer than 64 characters")
        

    def _validate_date_of_birth(self, date_of_birth: date) -> None:
        """Validate date of birth."""
        
        if date_of_birth > date.today():
            raise ValueError("Date of birth cannot be in the future")
        
    
    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, username='{self.username}', date_of_birth='{self.date_of_birth}')>" 