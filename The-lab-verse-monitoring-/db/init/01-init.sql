-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS labverse;

-- Create tables
CREATE TABLE labverse.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created__at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE labverse.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES labverse.users(id),
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP
);

CREATE TABLE labverse.requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES labverse.users(id),
    model VARCHAR(50),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost DECIMAL(10,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE labverse.market_intelligence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL,
    data JSONB,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_users_email ON labverse.users(email);
CREATE INDEX idx_api_keys_user_id ON labverse.api_keys(user_id);
CREATE INDEX idx_requests_user_id ON labverse.requests(user_id);
CREATE INDEX idx_requests_created_at ON labverse.requests(created_at);
CREATE INDEX idx_market_intelligence_company ON labverse.market_intelligence(company_name);
CREATE INDEX idx_market_intelligence_data ON labverse.market_intelligence USING gin(data);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON labverse.users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

GRANT ALL PRIVILEGES ON SCHEMA labverse TO labverse;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA labverse TO labverse;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA labverse TO labverse;
