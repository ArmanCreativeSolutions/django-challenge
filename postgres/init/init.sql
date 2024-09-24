-- Create database
CREATE DATABASE arman;

-- Create user and set password
CREATE USER arman_admin WITH PASSWORD 'fghgj<A!2h';

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE arman TO arman_admin;

-- Grant all privileges on all tables in the schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO arman_admin;

-- Grant all privileges on all sequences in the schema (needed for auto-increment fields)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO arman_admin;

-- Grant all privileges on all functions in the schema
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO arman_admin;
