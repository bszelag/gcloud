"""Hello API endpoints."""
import re
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.user_service import UserService
from app.schemas.user import UserCreate, BirthdayMessage

router = APIRouter()


def validate_username(username: str) -> str:
    """Validate username format."""
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be empty"
        )
    
    if len(username) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be longer than 50 characters"
        )
    
    # Username should contain only alphanumeric characters and underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username can only contain alphanumeric characters and underscores"
        )
    
    return username


@router.put("/hello/{username}", status_code=status.HTTP_204_NO_CONTENT)
def put_user(
    username: str,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create or update user's date of birth."""
    # Validate username
    validate_username(username)
    
    # Create service and handle user creation/update
    service = UserService(db)
    try:
        service.create_or_update_user(username, user_data.dateOfBirth)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/hello/{username}", response_model=BirthdayMessage)
def get_user_birthday_message(
    username: str,
    db: Session = Depends(get_db)
):
    """Get birthday message for user."""
    # Validate username
    validate_username(username)
    
    # Create service and get birthday message
    service = UserService(db)
    try:
        message = service.get_birthday_message(username)
        return BirthdayMessage(message=message)
    except ValueError as e:
        if "User not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 