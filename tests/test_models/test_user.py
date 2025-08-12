"""Tests for User model."""
import pytest
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError

from app.models.user import User


class TestUserModel:
    """Test cases for User model."""
    
    def test_create_user_with_valid_data(self, test_db):
        """Test creating a user with valid data."""
        # Arrange
        user_data = {
            "username": "john_doe",
            "date_of_birth": date(1990, 5, 15)
        }
        
        # Act
        user = User(**user_data)
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        # Assert
        assert user.id is not None
        assert user.username == "john_doe"
        assert user.date_of_birth == date(1990, 5, 15)
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_username_must_be_unique(self, test_db):
        """Test that username must be unique."""
        # Arrange
        user1 = User(username="john_doe", date_of_birth=date(1990, 5, 15))
        user2 = User(username="john_doe", date_of_birth=date(1991, 6, 20))
        
        # Act & Assert
        test_db.add(user1)
        test_db.commit()
        
        test_db.add(user2)
        with pytest.raises(IntegrityError):
            test_db.commit()
    
    def test_user_username_cannot_be_null(self, test_db):
        """Test that username cannot be null."""
        # Arrange
        user = User(date_of_birth=date(1990, 5, 15))
        
        # Act & Assert
        test_db.add(user)
        with pytest.raises(IntegrityError):
            test_db.commit()
    
    def test_user_date_of_birth_cannot_be_null(self, test_db):
        """Test that date_of_birth cannot be null."""
        # Arrange
        user = User(username="john_doe")
        
        # Act & Assert
        test_db.add(user)
        with pytest.raises(IntegrityError):
            test_db.commit()
    
    def test_user_username_format_validation(self, test_db):
        """Test username format validation."""
        # Arrange
        invalid_usernames = ["", "user name with a very very very very long name, more than 64 characters..............................................................."]
        
        for username in invalid_usernames:
            # Act & Assert
            with pytest.raises(ValueError):
                User(username=username, date_of_birth=date(1990, 5, 15))
    
    def test_user_date_of_birth_validation(self, test_db):
        """Test date_of_birth validation."""
        # Since we removed future date validation for testing flexibility,
        # this test should pass without raising an exception
        # Arrange
        future_date = date.today().replace(year=date.today().year + 1)
        
        # Act & Assert
        # Should raise ValueError since we don't allow future dates
        with pytest.raises(ValueError):
            User(username="john_doe", date_of_birth=future_date)
        
    
    def test_user_serialization(self, test_db):
        """Test user model serialization."""
        # Arrange
        user = User(username="john_doe", date_of_birth=date(1990, 5, 15))
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        # Act
        user_dict = {
            "id": user.id,
            "username": user.username,
            "date_of_birth": user.date_of_birth.isoformat(),
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }
        
        # Assert
        assert user_dict["username"] == "john_doe"
        assert user_dict["date_of_birth"] == "1990-05-15"
        assert "id" in user_dict
        assert "created_at" in user_dict
        assert "updated_at" in user_dict
    
    def test_user_update_timestamp(self, test_db):
        """Test that updated_at is updated when user is modified."""
        # Arrange
        user = User(username="john_doe", date_of_birth=date(1990, 5, 15))
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
        
        original_updated_at = user.updated_at
        
        # Act - Use the service method which properly updates the timestamp
        from app.services.user_service import UserService
        service = UserService(test_db)
        updated_user = service.update_user("john_doe", date(1991, 6, 20))
        
        # Assert
        assert updated_user.updated_at > original_updated_at
    
    def test_user_repr(self, test_db):
        """Test user model string representation."""
        # Arrange
        user = User(username="john_doe", date_of_birth=date(1990, 5, 15))
        
        # Act
        user_repr = repr(user)
        
        # Assert
        assert "User" in user_repr
        assert "john_doe" in user_repr 