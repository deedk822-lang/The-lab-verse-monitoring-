-- Add columns required for gazette harvesting workflow

ALTER TABLE IF EXISTS ingestion_manifest
    ADD COLUMN IF NOT EXISTS year INTEGER,
    ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS acts_extracted INTEGER DEFAULT 0;

ALTER TABLE IF EXISTS statutes
    ADD COLUMN IF NOT EXISTS confidence_probability NUMERIC(4,3) DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'unreviewed',
    ADD COLUMN IF NOT EXISTS source_metadata JSONB;
