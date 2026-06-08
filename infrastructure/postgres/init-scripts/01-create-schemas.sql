-- Initialize PostgreSQL schemas for Employee Leave Management System
-- This script runs automatically when the database is first created

-- Create schemas for each microservice
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS leaves;
CREATE SCHEMA IF NOT EXISTS notifications;

-- Grant permissions to the default user (will use POSTGRES_USER from environment)
-- Note: In production, each service should have its own database user with limited permissions
GRANT ALL PRIVILEGES ON SCHEMA auth TO CURRENT_USER;
GRANT ALL PRIVILEGES ON SCHEMA users TO CURRENT_USER;
GRANT ALL PRIVILEGES ON SCHEMA leaves TO CURRENT_USER;
GRANT ALL PRIVILEGES ON SCHEMA notifications TO CURRENT_USER;

-- Set default search path (optional, services will explicitly use schema names)
-- ALTER DATABASE leave_management SET search_path TO auth, users, leaves, notifications, public;

-- Enable UUID extension for all schemas (PostgreSQL 14+)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Schemas created successfully: auth, users, leaves, notifications';
END
$$;
