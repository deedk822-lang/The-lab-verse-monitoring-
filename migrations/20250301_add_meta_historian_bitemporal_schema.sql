-- Meta-Historian bi-temporal schema for historical digital twin simulations
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Immutable Anchors: Historical facts that cannot be altered in simulations
CREATE TABLE IF NOT EXISTS immutable_anchors (
    anchor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anchor_type VARCHAR(50) CHECK (anchor_type IN (
        'CONSTITUTIONAL',
        'REGIME_CHANGE',
        'GEOGRAPHIC',
        'DEMOGRAPHIC',
        'INTERNATIONAL'
    )),
    event_date DATE NOT NULL,
    description TEXT NOT NULL,
    confidence_score DECIMAL(3, 2) DEFAULT 1.00 CHECK (confidence_score = 1.00),
    valid_time_range TSRANGE NOT NULL,
    transaction_time_range TSRANGE NOT NULL DEFAULT tstzrange(now(), null),
    source_provenance JSONB NOT NULL,
    CONSTRAINT no_anchor_update EXCLUDE USING gist (
        anchor_id WITH =,
        transaction_time_range WITH &&
    )
);

-- Insert South African Immutable Anchors
INSERT INTO immutable_anchors (
    anchor_type,
    event_date,
    description,
    valid_time_range,
    source_provenance
)
VALUES
    ('REGIME_CHANGE', '1910-05-31', 'Union of South Africa formed', '[1910-05-31,)', '{"source": "South Africa Act 1909", "certainty": "absolute"}'),
    ('REGIME_CHANGE', '1948-05-26', 'National Party victory - Apartheid formalized', '[1948-05-26,)', '{"source": "Electoral records", "certainty": "absolute"}'),
    ('REGIME_CHANGE', '1994-04-27', 'First democratic elections', '[1994-04-27,)', '{"source": "IEC official results", "certainty": "absolute"}'),
    ('CONSTITUTIONAL', '1996-05-08', 'Constitution enacted', '[1996-05-08,)', '{"source": "Act 108 of 1996", "certainty": "absolute"}'),
    ('CONSTITUTIONAL', '1997-02-04', 'Constitution effective', '[1997-02-04,)', '{"source": "Proclamation", "certainty": "absolute"}'),
    ('GEOGRAPHIC', '1994-11-01', 'Nine provinces established', '[1994-11-01,)', '{"source": "Interim Constitution", "certainty": "absolute"}');

-- Flexible Zone: Legislation and policies that can be simulated/changed
CREATE TABLE IF NOT EXISTS flexible_zones (
    zone_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(50) CHECK (domain IN (
        'LEGAL',
        'ECONOMIC',
        'SOCIAL',
        'POLITICAL',
        'CULTURAL',
        'ADMINISTRATIVE'
    )),
    province_code VARCHAR(10) REFERENCES jurisdictions(jurisdiction_code),
    statute_id BIGINT REFERENCES statutes(statute_id),
    policy_name VARCHAR(255),
    valid_time_range TSRANGE NOT NULL,
    transaction_time_range TSRANGE NOT NULL DEFAULT tstzrange(now(), null),
    is_active BOOLEAN DEFAULT true,
    flexibility_score DECIMAL(3, 2) CHECK (flexibility_score BETWEEN 0.0 AND 1.0)
);

CREATE TABLE IF NOT EXISTS flexible_zone_anchor_dependencies (
    zone_id UUID REFERENCES flexible_zones(zone_id) ON DELETE CASCADE,
    anchor_id UUID REFERENCES immutable_anchors(anchor_id) ON DELETE RESTRICT,
    PRIMARY KEY (zone_id, anchor_id)
);

-- Domain-Province Matrix (6 domains × 9 provinces)
CREATE TABLE IF NOT EXISTS domain_province_matrix (
    matrix_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(50) NOT NULL,
    province_code VARCHAR(10) NOT NULL,
    baseline_metrics JSONB NOT NULL,
    current_projection JSONB,
    last_updated TIMESTAMP DEFAULT now(),
    UNIQUE(domain, province_code)
);

INSERT INTO domain_province_matrix (domain, province_code, baseline_metrics)
SELECT d.domain, p.code, '{}'::jsonb
FROM (
    VALUES
        ('LEGAL'),
        ('ECONOMIC'),
        ('SOCIAL'),
        ('POLITICAL'),
        ('CULTURAL'),
        ('ADMINISTRATIVE')
) AS d(domain)
CROSS JOIN (
    VALUES
        ('ZA-EC'),
        ('ZA-FS'),
        ('ZA-GP'),
        ('ZA-KZN'),
        ('ZA-LP'),
        ('ZA-MP'),
        ('ZA-NC'),
        ('ZA-NW'),
        ('ZA-WC')
) AS p(code)
ON CONFLICT DO NOTHING;

-- Belief States: Transaction-time tracking of interpretations
CREATE TABLE IF NOT EXISTS belief_states (
    belief_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID,
    transaction_time TIMESTAMP DEFAULT now(),
    valid_time DATE NOT NULL,
    belief_state VARCHAR(50) CHECK (belief_state IN (
        'initial_gazette',
        'courts_respond',
        'economic_data_revised',
        'historical_revision',
        'counterfactual_branch'
    )),
    interpretation TEXT NOT NULL,
    confidence_level VARCHAR(20) CHECK (confidence_level IN (
        'VERY_HIGH',
        'HIGH',
        'MODERATE',
        'LOW',
        'SPECULATIVE'
    )),
    evidence_links JSONB,
    agent_source VARCHAR(100)
);

-- Counterfactual Simulations
CREATE TABLE IF NOT EXISTS counterfactual_simulations (
    simulation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_action VARCHAR(100) NOT NULL,
    trigger_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    anchor_integrity_check BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    projected_stability JSONB,
    final_recommendation TEXT
);

-- Cascade Effects: Second and third order consequences
CREATE TABLE IF NOT EXISTS cascade_effects (
    cascade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID REFERENCES counterfactual_simulations(simulation_id),
    cause_agent VARCHAR(50),
    effect_domain VARCHAR(50),
    effect_description TEXT,
    probability DECIMAL(3, 2),
    time_horizon INT,
    z_score DECIMAL(5, 2),
    historical_parallel VARCHAR(255),
    parallel_confidence VARCHAR(20)
);

-- Conflict Intensity Index (Social Domain)
CREATE TABLE IF NOT EXISTS conflict_intensity_readings (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID,
    province_code VARCHAR(10),
    timestamp TIMESTAMP DEFAULT now(),
    intensity_score DECIMAL(3, 1) CHECK (intensity_score BETWEEN 0 AND 10),
    trigger_correlation DECIMAL(3, 2),
    narrative_emergence TEXT[],
    nlp_confidence DECIMAL(3, 2)
);
