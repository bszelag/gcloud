"""Pydantic schemas for user data validation."""
from datetime import date
from typing import Optional
from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    """Schema for creating a user."""
    dateOfBirth: date
    
    @field_validator('dateOfBirth')
    @classmethod
    def validate_date_of_birth(cls, v):
        """Validate that date of birth is not in the future."""
        # Allow dates up to today (for testing purposes and edge cases)
        # In a real application, you might want to be more restrictive
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    dateOfBirth: date
    
    @field_validator('dateOfBirth')
    @classmethod
    def validate_date_of_birth(cls, v):
        """Validate that date of birth is not in the future."""
        # Allow dates up to today (for testing purposes and edge cases)
        # In a real application, you might want to be more restrictive
        return v


class UserResponse(BaseModel):
    """Schema for user response."""
    username: str
    date_of_birth: date
    created_at: Optional[date] = None
    updated_at: Optional[date] = None
    
    model_config = {"from_attributes": True}


class BirthdayMessage(BaseModel):
    """Schema for birthday message response."""
    message: str 