-- ============================================================================
-- VAAL AI Empire Database Schema Updates
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- ----------------------------------------------------------------------------
-- Model Usage Logging Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Model Information
    model_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,  -- huggingface, zai, qwen, openai, etc.
    task VARCHAR(100) NOT NULL,     -- code_generation, chat, etc.

    -- Usage Metrics
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,

    -- Cost Tracking
    estimated_cost DECIMAL(10, 6),
    currency VARCHAR(3) DEFAULT 'USD',

    -- Client Information
    client_id VARCHAR(255),
    user_id UUID,
    session_id VARCHAR(255),
    request_id VARCHAR(255),

    -- Performance Metrics
    latency_ms INTEGER,
    response_status VARCHAR(50),

    -- Request Details
    prompt_length INTEGER,
    response_length INTEGER,
    temperature DECIMAL(3, 2),
    max_tokens INTEGER,

    -- Metadata
    metadata JSONB,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Indexes will be created below
    CONSTRAINT valid_provider CHECK (provider IN (
        'huggingface', 'zai', 'qwen', 'openai', 'anthropic', 'custom'
    ))
);

-- Create indexes for model_usage_logs
CREATE INDEX idx_model_usage_logs_created_at ON model_usage_logs(created_at DESC);
CREATE INDEX idx_model_usage_logs_provider ON model_usage_logs(provider);
CREATE INDEX idx_model_usage_logs_model_id ON model_usage_logs(model_id);
CREATE INDEX idx_model_usage_logs_client_id ON model_usage_logs(client_id);
CREATE INDEX idx_model_usage_logs_user_id ON model_usage_logs(user_id);
CREATE INDEX idx_model_usage_logs_task ON model_usage_logs(task);
CREATE INDEX idx_model_usage_logs_metadata ON model_usage_logs USING GIN(metadata);

-- Partitioning by date (monthly) for better performance
CREATE TABLE IF NOT EXISTS model_usage_logs_2026_01 PARTITION OF model_usage_logs
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE IF NOT EXISTS model_usage_logs_2026_02 PARTITION OF model_usage_logs
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Add more partitions as needed...

-- ----------------------------------------------------------------------------
-- Security Audit Log Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS security_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event Information
    event_type VARCHAR(100) NOT NULL,  -- prompt_injection, ssrf_blocked, rate_limit, etc.
    severity VARCHAR(20) NOT NULL,     -- info, warning, error, critical

    -- Request Details
    client_ip INET,
    user_agent TEXT,
    request_path VARCHAR(500),
    request_method VARCHAR(10),

    -- Security Context
    blocked BOOLEAN DEFAULT false,
    reason TEXT,
    patterns_matched TEXT[],

    -- Related Entities
    user_id UUID,
    session_id VARCHAR(255),

    -- Payload (sanitized)
    payload_preview TEXT,  -- First 500 chars only

    -- Metadata
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for security_audit_logs
CREATE INDEX idx_security_audit_logs_created_at ON security_audit_logs(created_at DESC);
CREATE INDEX idx_security_audit_logs_event_type ON security_audit_logs(event_type);
CREATE INDEX idx_security_audit_logs_severity ON security_audit_logs(severity);
CREATE INDEX idx_security_audit_logs_client_ip ON security_audit_logs(client_ip);
CREATE INDEX idx_security_audit_logs_blocked ON security_audit_logs(blocked);

-- ----------------------------------------------------------------------------
-- Webhook Events Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event Information
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,  -- atlassian, github, slack, etc.

    -- Processing Status
    status VARCHAR(50) NOT NULL DEFAULT 'received',  -- received, processing, completed, failed
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Payload
    raw_payload JSONB NOT NULL,
    processed_payload JSONB,

    -- Forwarding Details
    forwarded_to VARCHAR(500),
    forward_status INTEGER,
    forward_response TEXT,

    -- Deduplication
    dedupe_key VARCHAR(64) UNIQUE,  -- SHA-256 hash

    -- Metadata
    metadata JSONB,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_status CHECK (status IN (
        'received', 'processing', 'completed', 'failed', 'duplicate'
    ))
);

-- Indexes for webhook_events
CREATE INDEX idx_webhook_events_created_at ON webhook_events(created_at DESC);
CREATE INDEX idx_webhook_events_status ON webhook_events(status);
CREATE INDEX idx_webhook_events_source ON webhook_events(source);
CREATE INDEX idx_webhook_events_event_type ON webhook_events(event_type);
CREATE INDEX idx_webhook_events_dedupe_key ON webhook_events(dedupe_key);

-- ----------------------------------------------------------------------------
-- Users Table (if not exists)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User Information
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),

    -- Authentication
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,

    -- Authorization
    role VARCHAR(50) DEFAULT 'user',
    permissions TEXT[],

    -- Usage Tracking
    total_tokens_used BIGINT DEFAULT 0,
    total_cost DECIMAL(10, 2) DEFAULT 0.00,

    -- Metadata
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_role CHECK (role IN ('user', 'admin', 'developer', 'viewer'))
);

-- Indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ----------------------------------------------------------------------------
-- API Keys Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Key Information
    key_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 hash of the key
    key_prefix VARCHAR(8) NOT NULL,  -- First 8 chars for identification
    name VARCHAR(255),

    -- Owner
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Permissions
    scopes TEXT[],
    rate_limit_override INTEGER,

    -- Status
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Usage Tracking
    last_used_at TIMESTAMP WITH TIME ZONE,
    total_requests BIGINT DEFAULT 0,

    -- Metadata
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for api_keys
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);
CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at);

-- ----------------------------------------------------------------------------
-- Cost Budget Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cost_budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Budget Owner
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Budget Configuration
    budget_type VARCHAR(50) NOT NULL,  -- daily, weekly, monthly, total
    limit_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',

    -- Current Usage
    current_usage DECIMAL(10, 2) DEFAULT 0.00,

    -- Period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Alerts
    alert_threshold DECIMAL(3, 2) DEFAULT 0.80,  -- Alert at 80%
    alert_sent BOOLEAN DEFAULT false,

    -- Status
    is_active BOOLEAN DEFAULT true,
    exceeded BOOLEAN DEFAULT false,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for cost_budgets
CREATE INDEX idx_cost_budgets_user_id ON cost_budgets(user_id);
CREATE INDEX idx_cost_budgets_period ON cost_budgets(period_start, period_end);
CREATE INDEX idx_cost_budgets_is_active ON cost_budgets(is_active);

-- ----------------------------------------------------------------------------
-- Views for Analytics
-- ----------------------------------------------------------------------------

-- Daily usage summary
CREATE OR REPLACE VIEW daily_usage_summary AS
SELECT
    DATE(created_at) as usage_date,
    provider,
    model_id,
    task,
    COUNT(*) as request_count,
    SUM(total_tokens) as total_tokens,
    SUM(estimated_cost) as total_cost,
    AVG(latency_ms) as avg_latency_ms,
    COUNT(CASE WHEN response_status != 'success' THEN 1 END) as error_count
FROM model_usage_logs
GROUP BY DATE(created_at), provider, model_id, task
ORDER BY usage_date DESC;

-- User usage summary
CREATE OR REPLACE VIEW user_usage_summary AS
SELECT
    u.id as user_id,
    u.username,
    u.email,
    COUNT(DISTINCT m.id) as total_requests,
    SUM(m.total_tokens) as total_tokens,
    SUM(m.estimated_cost) as total_cost,
    MAX(m.created_at) as last_request_at
FROM users u
LEFT JOIN model_usage_logs m ON u.id = m.user_id
GROUP BY u.id, u.username, u.email;

-- Provider performance summary
CREATE OR REPLACE VIEW provider_performance AS
SELECT
    provider,
    COUNT(*) as request_count,
    AVG(latency_ms) as avg_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms,
    COUNT(CASE WHEN response_status = 'success' THEN 1 END)::FLOAT /
        COUNT(*)::FLOAT * 100 as success_rate
FROM model_usage_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY provider;

-- ----------------------------------------------------------------------------
-- Functions and Triggers
-- ----------------------------------------------------------------------------

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to cost_budgets table
DROP TRIGGER IF EXISTS update_cost_budgets_updated_at ON cost_budgets;
CREATE TRIGGER update_cost_budgets_updated_at
    BEFORE UPDATE ON cost_budgets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Budget check function
CREATE OR REPLACE FUNCTION check_budget_exceeded()
RETURNS TRIGGER AS $$
DECLARE
    budget_record RECORD;
BEGIN
    -- Find active budgets for this user
    FOR budget_record IN
        SELECT * FROM cost_budgets
        WHERE user_id = NEW.user_id
        AND is_active = true
        AND period_start <= NOW()
        AND period_end >= NOW()
    LOOP
        -- Update current usage
        UPDATE cost_budgets
        SET current_usage = current_usage + COALESCE(NEW.estimated_cost, 0),
            exceeded = (current_usage + COALESCE(NEW.estimated_cost, 0)) > limit_amount,
            alert_sent = CASE
                WHEN (current_usage + COALESCE(NEW.estimated_cost, 0)) / limit_amount >= alert_threshold
                THEN true
                ELSE alert_sent
            END
        WHERE id = budget_record.id;
    END LOOP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply budget check trigger
DROP TRIGGER IF EXISTS check_budget_on_usage ON model_usage_logs;
CREATE TRIGGER check_budget_on_usage
    AFTER INSERT ON model_usage_logs
    FOR EACH ROW
    WHEN (NEW.user_id IS NOT NULL)
    EXECUTE FUNCTION check_budget_exceeded();

-- ----------------------------------------------------------------------------
-- Data Retention Policy
-- ----------------------------------------------------------------------------

-- Function to archive old logs
CREATE OR REPLACE FUNCTION archive_old_logs(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM model_usage_logs
    WHERE created_at < NOW() - MAKE_INTERVAL(days => retention_days)
    AND metadata->>'archived' IS NULL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule: Call this function periodically via cron or application scheduler

-- ----------------------------------------------------------------------------
-- Grant Permissions
-- ----------------------------------------------------------------------------

-- Grant appropriate permissions to application user
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO vaal_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vaal_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO vaal_app_user;
