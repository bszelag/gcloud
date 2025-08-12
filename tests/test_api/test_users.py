"""Tests for user API endpoints."""
import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.models.user import User


class TestUserAPI:
    """Test cases for user API endpoints."""
    
    def test_put_user_create_success(self, client, test_db):
        """Test successful user creation via PUT endpoint."""
        # Arrange
        username = "john_doe"
        user_data = {"dateOfBirth": "1990-05-15"}
        
        # Act
        response = client.put(f"/hello/{username}", json=user_data)
        
        # Assert
        assert response.status_code == 204
        assert response.content == b""
        
        # Verify user was created in database
        user = test_db.query(User).filter(User.username == username).first()
        assert user is not None
        assert user.date_of_birth == date(1990, 5, 15)
    
    def test_put_user_update_success(self, client, test_db):
        """Test successful user update via PUT endpoint."""
        # Arrange
        username = "john_doe"
        original_data = {"dateOfBirth": "1990-05-15"}
        updated_data = {"dateOfBirth": "1991-06-20"}
        
        # Create user first
        client.put(f"/hello/{username}", json=original_data)
        
        # Act
        response = client.put(f"/hello/{username}", json=updated_data)
        
        # Assert
        assert response.status_code == 204
        assert response.content == b""
        
        # Verify user was updated in database
        user = test_db.query(User).filter(User.username == username).first()
        assert user.date_of_birth == date(1991, 6, 20)
    
    def test_put_user_invalid_username(self, client):
        """Test PUT endpoint with invalid username."""
        # Arrange
        invalid_usernames = ["", "a" * 51, "user@name", "user name", "user-name"]
        user_data = {"dateOfBirth": "1990-05-15"}
        
        for username in invalid_usernames:
            # Act
            response = client.put(f"/hello/{username}", json=user_data)
            
            # Assert
            # FastAPI returns 404 for invalid path parameters
            assert response.status_code in [400, 404]
            if response.status_code == 400:
                assert "username" in response.json()["detail"].lower()
    
    def test_put_user_invalid_date_format(self, client):
        """Test PUT endpoint with invalid date format."""
        # Arrange
        username = "john_doe"
        invalid_dates = [
            "invalid-date",
            "1990/05/15",
            "15-05-1990",
            "1990-13-01",  # Invalid month
            "1990-05-32",  # Invalid day
        ]
        
        for invalid_date in invalid_dates:
            user_data = {"dateOfBirth": invalid_date}
            
            # Act
            response = client.put(f"/hello/{username}", json=user_data)
            
            # Assert
            # FastAPI returns 422 for validation errors
            assert response.status_code == 422
            assert "date" in response.json()["detail"][0]["msg"].lower()
    
    def test_put_user_future_date(self, client):
        """Test PUT endpoint with future date."""
        # Arrange
        username = "john_doe"
        future_date = date.today().replace(year=date.today().year + 1).isoformat()
        user_data = {"dateOfBirth": future_date}
        
        # Act
        response = client.put(f"/hello/{username}", json=user_data)
        
        # Assert
        # Since we removed future date validation, this should succeed
        assert response.status_code == 400
    
    def test_put_user_missing_date_field(self, client):
        """Test PUT endpoint with missing dateOfBirth field."""
        # Arrange
        username = "john_doe"
        user_data = {}
        
        # Act
        response = client.put(f"/hello/{username}", json=user_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_put_user_extra_fields(self, client):
        """Test PUT endpoint with extra fields (should be ignored)."""
        # Arrange
        username = "john_doe"
        user_data = {
            "dateOfBirth": "1990-05-15",
            "extraField": "should be ignored"
        }
        
        # Act
        response = client.put(f"/hello/{username}", json=user_data)
        
        # Assert
        assert response.status_code == 204
    
    def test_get_user_birthday_message_success(self, client, test_db):
        """Test successful birthday message retrieval via GET endpoint."""
        # Arrange
        username = "john_doe"
        user_data = {"dateOfBirth": "1990-05-15"}
        
        # Create user first
        client.put(f"/hello/{username}", json=user_data)
        
        # Act
        response = client.get(f"/hello/{username}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert username in data["message"]
        assert "birthday" in data["message"].lower()
    
    def test_get_user_birthday_message_today(self, client, test_db):
        """Test birthday message when it's the user's birthday today."""
        # Arrange
        username = "john_doe"
        today = date.today().isoformat()
        user_data = {"dateOfBirth": today}
        
        # Create user with birthday today
        client.put(f"/hello/{username}", json=user_data)
        
        # Act
        response = client.get(f"/hello/{username}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Happy birthday" in data["message"]
        assert username in data["message"]
    
    def test_get_user_not_found(self, client):
        """Test GET endpoint for non-existent user."""
        # Arrange
        username = "nonexistent"
        
        # Act
        response = client.get(f"/hello/{username}")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_user_invalid_username(self, client):
        """Test GET endpoint with invalid username format."""
        # Arrange
        invalid_usernames = ["", "user name with a very very very very long name, more than 64 characters..............................................................."]
        
        for username in invalid_usernames:
            # Act
            response = client.get(f"/hello/{username}")
            
            # Assert
            # FastAPI returns 404 for invalid path parameters
            assert response.status_code in [400, 404]
            if response.status_code == 400:
                assert "username" in response.json()["detail"].lower()
    
    def test_get_user_leap_year_birthday(self, client, test_db):
        """Test birthday message for leap year birthday."""
        # Arrange
        username = "leap_user"
        user_data = {"dateOfBirth": "2000-02-29"}
        
        # Create user with leap year birthday
        client.put(f"/hello/{username}", json=user_data)
        
        # Act
        response = client.get(f"/hello/{username}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert username in data["message"]
    
    def test_put_user_special_characters_in_username(self, client):
        """Test PUT endpoint with special characters in username."""
        # Arrange
        username = "user_with_underscores"
        user_data = {"dateOfBirth": "1990-05-15"}
        
        # Act
        response = client.put(f"/hello/{username}", json=user_data)
        
        # Assert
        assert response.status_code == 204
    
    def test_put_user_numbers_in_username(self, client):
        """Test PUT endpoint with numbers in username."""
        # Arrange
        username = "user123"
        user_data = {"dateOfBirth": "1990-05-15"}
        
        # Act
        response = client.put(f"/hello/{username}", json=user_data)
        
        # Assert
        assert response.status_code == 204
    
    def test_put_user_case_sensitive_username(self, client, test_db):
        """Test that usernames are case sensitive."""
        # Arrange
        username1 = "JohnDoe"
        username2 = "johndoe"
        user_data = {"dateOfBirth": "1990-05-15"}
        
        # Create first user
        response1 = client.put(f"/hello/{username1}", json=user_data)
        assert response1.status_code == 204
        
        # Create second user (should be different)
        response2 = client.put(f"/hello/{username2}", json=user_data)
        assert response2.status_code == 204
        
        # Verify both users exist
        user1 = test_db.query(User).filter(User.username == username1).first()
        user2 = test_db.query(User).filter(User.username == username2).first()
        assert user1 is not None
        assert user2 is not None
        assert user1.id != user2.id 