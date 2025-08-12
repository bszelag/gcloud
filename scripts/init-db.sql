-- Database initialization script for Birthday API
-- This script runs when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist (handled by POSTGRES_DB env var)
-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE birthday_api TO birthday_user;

-- Create schema if needed
CREATE SCHEMA IF NOT EXISTS public;

-- Set search path
SET search_path TO public;

-- Note: Tables will be created by Alembic migrations
-- This script is mainly for initial setup and permissions
