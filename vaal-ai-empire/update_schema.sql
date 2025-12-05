-- This script updates the Vercel Postgres schema to include the model_usage_logs table.
-- Run this script against your Vercel Postgres database.

CREATE TABLE model_usage_logs (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    task VARCHAR(255),
    tokens_used INTEGER,
    cost_usd REAL,
    client_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
