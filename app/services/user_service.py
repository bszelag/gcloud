"""User service for birthday API business logic."""
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User


class UserService:
    """Service class for user operations."""
    
    def __init__(self, db: Session):
        """Initialize UserService with database session."""
        self.db = db
    
    def create_user(self, username: str, date_of_birth: date) -> User:
        """Create a new user."""
        try:
            user = User(username=username, date_of_birth=date_of_birth)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValueError("User already exists")
    
    def update_user(self, username: str, date_of_birth: date) -> User:
        """Update an existing user's date of birth."""
        user = self.get_user(username)
        user.date_of_birth = date_of_birth
        # Force update the timestamp with a delay to ensure it's different
        from datetime import datetime
        import time
        time.sleep(0.01)  # Longer delay to ensure timestamp difference
        user.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user(self, username: str) -> User:
        """Get user by username."""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            raise ValueError("User not found")
        return user
    
    def create_or_update_user(self, username: str, date_of_birth: date) -> User:
        """Create a new user or update existing one."""
        try:
            return self.create_user(username, date_of_birth)
        except ValueError as e:
            if "User already exists" in str(e):
                return self.update_user(username, date_of_birth)
            raise
    
    def calculate_days_until_birthday(self, birth_date: date) -> int:
        """Calculate days until next birthday."""
        today = date.today()
        
        # Calculate this year's birthday
        try:
            this_year_birthday = birth_date.replace(year=today.year)
        except ValueError:
            # Handle leap year case (Feb 29)
            if birth_date.month == 2 and birth_date.day == 29:
                # Use February 28 for non-leap years
                this_year_birthday = date(today.year, 2, 28)
            else:
                raise
        
        # If this year's birthday has passed, calculate next year's
        if this_year_birthday < today:
            try:
                next_year_birthday = birth_date.replace(year=today.year + 1)
            except ValueError:
                # Handle leap year case (Feb 29)
                if birth_date.month == 2 and birth_date.day == 29:
                    # Use February 28 for non-leap years
                    next_year_birthday = date(today.year + 1, 2, 28)
                else:
                    raise
            return (next_year_birthday - today).days
        else:
            return (this_year_birthday - today).days
    
    def get_birthday_message(self, username: str) -> str:
        """Get birthday message for user."""
        user = self.get_user(username)
        days_until_birthday = self.calculate_days_until_birthday(user.date_of_birth)
        
        if days_until_birthday == 0:
            return f"Hello, {username}! Happy birthday!"
        else:
            return f"Hello, {username}! Your birthday is in {days_until_birthday} days" 