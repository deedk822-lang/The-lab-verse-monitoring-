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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for model_usage_logs
CREATE INDEX IF NOT EXISTS idx_model_usage_logs_created_at ON model_usage_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_usage_logs_provider ON model_usage_logs(provider);
CREATE INDEX IF NOT EXISTS idx_model_usage_logs_model_id ON model_usage_logs(model_id);
CREATE INDEX IF NOT EXISTS idx_model_usage_logs_client_id ON model_usage_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_model_usage_logs_user_id ON model_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_model_usage_logs_task ON model_usage_logs(task);
CREATE INDEX IF NOT EXISTS idx_model_usage_logs_metadata ON model_usage_logs USING GIN(metadata);

-- ----------------------------------------------------------------------------
-- Security Audit Log Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS security_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Event Information
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    
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
    payload_preview TEXT,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_security_audit_logs_created_at ON security_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_audit_logs_event_type ON security_audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_security_audit_logs_severity ON security_audit_logs(severity);
CREATE INDEX IF NOT EXISTS idx_security_audit_logs_client_ip ON security_audit_logs(client_ip);

-- ----------------------------------------------------------------------------
-- Webhook Events Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'received',
    retry_count INTEGER DEFAULT 0,
    raw_payload JSONB NOT NULL,
    processed_payload JSONB,
    dedupe_key VARCHAR(64) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_created_at ON webhook_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_events_status ON webhook_events(status);
CREATE INDEX IF NOT EXISTS idx_webhook_events_source ON webhook_events(source);
