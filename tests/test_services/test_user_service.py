"""Tests for UserService."""
import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch

from app.services.user_service import UserService
from app.models.user import User


class TestUserService:
    """Test cases for UserService."""
    
    def test_create_user_success(self, test_db):
        """Test successful user creation."""
        # Arrange
        service = UserService(test_db)
        username = "john_doe"
        date_of_birth = date(1990, 5, 15)
        
        # Act
        user = service.create_user(username, date_of_birth)
        
        # Assert
        assert user.username == username
        assert user.date_of_birth == date_of_birth
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_create_user_with_invalid_username(self, test_db):
        """Test user creation with invalid username."""
        # Arrange
        service = UserService(test_db)
        invalid_usernames = ["", "user name with a very very very very long name, more than 64 characters..............................................................."]
        
        for username in invalid_usernames:
            # Act & Assert
            with pytest.raises(ValueError):
                service.create_user(username, date(1990, 5, 15))
    
    def test_create_user_with_future_date(self, test_db):
        """Test user creation with future date of birth."""
        # Since we removed future date validation for testing flexibility,
        # this test should pass without raising an exception
        # Arrange
        service = UserService(test_db)
        future_date = date.today().replace(year=date.today().year + 1)
        
        # Act & Assert
        # Should not raise ValueError since we allow future dates
        with pytest.raises(ValueError):
            service.create_user("john_doe", future_date)
        
    
    def test_create_user_duplicate_username(self, test_db):
        """Test creating user with duplicate username."""
        # Arrange
        service = UserService(test_db)
        username = "john_doe"
        date_of_birth = date(1990, 5, 15)
        
        # Create first user
        service.create_user(username, date_of_birth)
        
        # Act & Assert
        with pytest.raises(ValueError, match="User already exists"):
            service.create_user(username, date(1991, 6, 20))
    
    def test_update_user_success(self, test_db):
        """Test successful user update."""
        # Arrange
        service = UserService(test_db)
        username = "john_doe"
        original_date = date(1990, 5, 15)
        new_date = date(1991, 6, 20)
        
        # Create user
        user = service.create_user(username, original_date)
        original_updated_at = user.updated_at
        
        # Act
        updated_user = service.update_user(username, new_date)
        
        # Assert
        assert updated_user.username == username
        assert updated_user.date_of_birth == new_date
        assert updated_user.updated_at > original_updated_at
    
    def test_update_user_not_found(self, test_db):
        """Test updating non-existent user."""
        # Arrange
        service = UserService(test_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            service.update_user("nonexistent", date(1990, 5, 15))
    
    def test_get_user_success(self, test_db):
        """Test successful user retrieval."""
        # Arrange
        service = UserService(test_db)
        username = "john_doe"
        date_of_birth = date(1990, 5, 15)
        
        # Create user
        created_user = service.create_user(username, date_of_birth)
        
        # Act
        retrieved_user = service.get_user(username)
        
        # Assert
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == username
        assert retrieved_user.date_of_birth == date_of_birth
    
    def test_get_user_not_found(self, test_db):
        """Test retrieving non-existent user."""
        # Arrange
        service = UserService(test_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            service.get_user("nonexistent")
    
    def test_calculate_days_until_birthday_future_date(self, test_db):
        """Test calculating days until birthday for future date this year."""
        # Arrange
        service = UserService(test_db)
        today = date.today()
        future_birthday = today.replace(month=12, day=25)  # Christmas
        
        # Act
        days = service.calculate_days_until_birthday(future_birthday)
        
        # Assert
        assert days >= 0
        assert isinstance(days, int)
    
    def test_calculate_days_until_birthday_past_date(self, test_db):
        """Test calculating days until birthday for past date this year."""
        # Arrange
        service = UserService(test_db)
        today = date.today()
        past_birthday = today.replace(month=1, day=1)  # New Year
        
        # Act
        days = service.calculate_days_until_birthday(past_birthday)
        
        # Assert
        assert days >= 0
        assert isinstance(days, int)
    
    def test_calculate_days_until_birthday_today(self, test_db):
        """Test calculating days until birthday when it's today."""
        # Arrange
        service = UserService(test_db)
        today = date.today()
        
        # Act
        days = service.calculate_days_until_birthday(today)
        
        # Assert
        assert days == 0
    
    def test_calculate_days_until_birthday_leap_year(self, test_db):
        """Test calculating days until birthday with leap year consideration."""
        # Arrange
        service = UserService(test_db)
        leap_birthday = date(2000, 2, 29)  # Leap year birthday
        
        # Act
        days = service.calculate_days_until_birthday(leap_birthday)
        
        # Assert
        assert days >= 0
        assert isinstance(days, int)
    
    def test_get_birthday_message_today(self, test_db):
        """Test birthday message when it's the user's birthday today."""
        # Arrange
        service = UserService(test_db)
        today = date.today()
        username = "john_doe"
        
        # Create user with birthday today
        service.create_user(username, today)
        
        # Act
        message = service.get_birthday_message(username)
        
        # Assert
        assert "Happy birthday" in message
        assert username in message
    
    def test_get_birthday_message_future(self, test_db):
        """Test birthday message for future birthday."""
        # Arrange
        service = UserService(test_db)
        today = date.today()
        future_birthday = today.replace(month=12, day=25)  # Christmas
        username = "john_doe"
        
        # Create user with future birthday
        
        # Act
        with pytest.raises(ValueError):
            service.create_user(username, future_birthday)

        with pytest.raises(ValueError):
            service.get_birthday_message(username)
        

    
    def test_get_birthday_message_user_not_found(self, test_db):
        """Test birthday message for non-existent user."""
        # Arrange
        service = UserService(test_db)
        
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            service.get_birthday_message("nonexistent")
    
    def test_create_or_update_user_create_new(self, test_db):
        """Test create_or_update_user for new user."""
        # Arrange
        service = UserService(test_db)
        username = "john_doe"
        date_of_birth = date(1990, 5, 15)
        
        # Act
        user = service.create_or_update_user(username, date_of_birth)
        
        # Assert
        assert user.username == username
        assert user.date_of_birth == date_of_birth
        assert user.id is not None
    
    def test_create_or_update_user_update_existing(self, test_db):
        """Test create_or_update_user for existing user."""
        # Arrange
        service = UserService(test_db)
        username = "john_doe"
        original_date = date(1990, 5, 15)
        new_date = date(1991, 6, 20)
        
        # Create user
        original_user = service.create_user(username, original_date)
        original_updated_at = original_user.updated_at
        
        # Act
        updated_user = service.create_or_update_user(username, new_date)
        
        # Assert
        assert updated_user.username == username
        assert updated_user.date_of_birth == new_date
        assert updated_user.updated_at > original_updated_at 