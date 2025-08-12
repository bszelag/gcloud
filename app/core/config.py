"""Application configuration management."""
import os
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Birthday API"
    debug: bool = False
    log_level: str = "INFO"
    
    # API
    api_v1_str: str = "/api/v1"
    project_name: str = "Birthday API"
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/birthday_api"
    database_engine: str = ""
    database_user: str = ""
    database_password: str = ""
    database_host: str = ""
    database_port: int = 5432
    database_name: str = "birthday_api"

    test_database_url: str = "sqlite:///./test.db"
    
    # Security
    secret_key: str = "your-secret-key-here"
    
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "sqlite://")):
            raise ValueError("Database URL must start with postgresql:// or sqlite://")
        return v

    @field_validator("database_engine")
    @classmethod
    def validate_database_engine(cls, v: str) -> str:
        """Validate database engine."""
        if v and v not in ["postgresql", "sqlite"]:
            raise ValueError("Database engine must be 'postgresql' or 'sqlite'")
        return v

    @property
    def get_database_url(self) -> str:
        """Get the database URL with proper credentials."""
        if self.database_engine == "postgresql" and all([self.database_user, self.database_password, self.database_host]):
            return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"
        return self.database_url

    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings() 