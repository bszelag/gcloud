"""Pytest configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.config import settings
from app.main import app


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        settings.test_database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.test_database_url else {},
    )
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session."""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    
    yield db
    
    # Cleanup
    db.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(test_db):
    """Create test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "john_doe",
        "date_of_birth": "1990-05-15"
    }


@pytest.fixture
def sample_user_data_invalid_date():
    """Sample user data with invalid date for testing."""
    return {
        "username": "john_doe",
        "date_of_birth": "invalid-date"
    } 