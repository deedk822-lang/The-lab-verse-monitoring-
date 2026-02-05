-- 
-- LEGAL METADATA HISTORIAN DATABASE MIGRATION
-- Version: 1.0.0
-- Date: 2026-02-05
-- Description: Complete schema for South African legal metadata
--              including DIRCO treaty management
-- ============================================================

-- ------------------------------------------------------------
-- 0. DATABASE CONFIGURATION
-- ------------------------------------------------------------

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Configure for DDL operations
SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS = 0;
SET AUTOCOMMIT = 0;

-- Verify/set ngram token size for legal citation search
SET GLOBAL ngram_token_size = 2;

-- ------------------------------------------------------------
-- 1. REFERENCE TABLES
-- ------------------------------------------------------------

CREATE TABLE jurisdictions (
    jurisdiction_code VARCHAR(10) PRIMARY KEY,
    jurisdiction_name VARCHAR(255) NOT NULL,
    jurisdiction_name_local VARCHAR(255),
    jurisdiction_type ENUM('NATIONAL','PROVINCIAL','LOCAL','SUPRANATIONAL','INTERNATIONAL','ORGANIZATION') NOT NULL DEFAULT 'NATIONAL',
    parent_jurisdiction_code VARCHAR(10),

    -- ISO standards
    iso_3166_1_alpha_2 CHAR(2),
    iso_3166_1_alpha_3 CHAR(3),
    iso_3166_2_subdivision VARCHAR(6),
    un_m49_code SMALLINT UNSIGNED,

    -- Hierarchy for nested set model
    materialized_path VARCHAR(500),
    tree_depth TINYINT UNSIGNED DEFAULT 0,
    left_bound INT UNSIGNED,
    right_bound INT UNSIGNED,

    -- DIRCO-specific international designations
    is_recognized_state BOOLEAN DEFAULT TRUE,
    is_un_member_state BOOLEAN DEFAULT FALSE,
    statehood_date DATE,
    diplomatic_recognition_date DATE,
    un_membership_date DATE,
    commonwealth_membership_date DATE,
    sadc_membership_date DATE,
    au_membership_date DATE,
    treaty_eligible BOOLEAN DEFAULT TRUE,
    dirco_priority_tier TINYINT UNSIGNED,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_jurisdiction_code) REFERENCES jurisdictions(jurisdiction_code),
    INDEX idx_jurisdiction_type (jurisdiction_type),
    INDEX idx_materialized_path (materialized_path(100)),
    INDEX idx_iso_alpha2 (iso_3166_1_alpha_2),
    INDEX idx_nested_set (left_bound, right_bound),
    INDEX idx_dirco_priority (dirco_priority_tier)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 2. CORE STATUTE TABLES
-- ------------------------------------------------------------

CREATE TABLE statutes (
    -- Primary keys
    statute_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    statute_uuid CHAR(36) DEFAULT (UUID()) NOT NULL,

    -- Natural key components
    jurisdiction_code VARCHAR(10) NOT NULL,
    statute_type ENUM('ACT','ORDINANCE','REGULATION','PROCLAMATION','NOTICE','BILL','RULE','BYLAW') NOT NULL DEFAULT 'ACT',
    statute_number VARCHAR(50) NOT NULL,
    version_identifier VARCHAR(20) NOT NULL DEFAULT 'original',

    -- Temporal tracking (all dates in South African local time)
    enacted_date DATE,
    effective_date DATE,
    gazette_publication_date DATE,
    gazette_number VARCHAR(50),
    gazette_year SMALLINT UNSIGNED,
    assent_date DATE,
    repealed_date DATE,
    sunset_date DATE,

    -- Content fields
    short_title VARCHAR(500),
    long_title VARCHAR(2000),
    official_citation VARCHAR(500),
    regnal_year_citation VARCHAR(100),
    preamble_text LONGTEXT,
    full_text LONGTEXT,
    plain_text LONGTEXT,
    original_markup LONGTEXT,

    -- Status and lifecycle
    status ENUM('DRAFT','ENACTED','IN_FORCE','AMENDED','REPEALED','EXPIRED','SUSPENDED','SUPERSEDED') DEFAULT 'DRAFT',
    is_current BOOLEAN GENERATED ALWAYS AS (
        CASE 
            WHEN status = 'IN_FORCE' AND (sunset_date IS NULL OR sunset_date > CURDATE()) AND repealed_date IS NULL
            THEN TRUE 
            ELSE FALSE 
        END
    ) STORED,
    is_historical BOOLEAN GENERATED ALWAYS AS (
        CASE WHEN repealed_date IS NOT NULL OR sunset_date < CURDATE() THEN TRUE ELSE FALSE END
    ) STORED,

    -- Version linking
    prior_version_statute_id BIGINT UNSIGNED,
    consolidating_statute_id BIGINT UNSIGNED,
    repealed_by_statute_id BIGINT UNSIGNED,

    -- Source and audit
    source_manifest_id BIGINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    UNIQUE KEY uk_statute_natural_key (jurisdiction_code, statute_type, statute_number, version_identifier),
    UNIQUE KEY uk_statute_uuid (statute_uuid),

    -- Foreign keys
    FOREIGN KEY (jurisdiction_code) REFERENCES jurisdictions(jurisdiction_code),
    FOREIGN KEY (prior_version_statute_id) REFERENCES statutes(statute_id),
    FOREIGN KEY (consolidating_statute_id) REFERENCES statutes(statute_id),
    FOREIGN KEY (repealed_by_statute_id) REFERENCES statutes(statute_id),

    -- Core query indexes
    INDEX idx_jurisdiction_status_effective (jurisdiction_code, status, effective_date),
    INDEX idx_jurisdiction_current (jurisdiction_code, is_current, effective_date),
    INDEX idx_statute_number (statute_number),
    INDEX idx_effective_date (effective_date),
    INDEX idx_repealed_date (repealed_date),
    INDEX idx_sunset_date (sunset_date),
    INDEX idx_status_current (status, is_current),
    INDEX idx_gazette_ref (gazette_number, gazette_year),

    -- Covering indexes for common patterns
    INDEX idx_jurisdiction_covering (jurisdiction_code, status, effective_date, statute_id, short_title, statute_type),
    INDEX idx_citation_lookup (statute_number, statute_type, jurisdiction_code, statute_id, short_title),

    -- Full-text search indexes
    FULLTEXT INDEX ft_short_title (short_title) WITH PARSER ngram,
    FULLTEXT INDEX ft_long_title (long_title) WITH PARSER ngram,
    FULLTEXT INDEX ft_preamble (preamble_text) WITH PARSER ngram,
    FULLTEXT INDEX ft_full_text (full_text) WITH PARSER ngram,
    FULLTEXT INDEX ft_combined (short_title, long_title, preamble_text, full_text) WITH PARSER ngram

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC
PARTITION BY RANGE (YEAR(effective_date)) (
    PARTITION p_before_1910 VALUES LESS THAN (1910),
    PARTITION p_1910_1919 VALUES LESS THAN (1920),
    PARTITION p_1920_1929 VALUES LESS THAN (1930),
    PARTITION p_1930_1939 VALUES LESS THAN (1940),
    PARTITION p_1940_1949 VALUES LESS THAN (1950),
    PARTITION p_1950_1959 VALUES LESS THAN (1960),
    PARTITION p_1960_1969 VALUES LESS THAN (1970),
    PARTITION p_1970_1979 VALUES LESS THAN (1980),
    PARTITION p_1980_1989 VALUES LESS THAN (1990),
    PARTITION p_1990_1999 VALUES LESS THAN (2000),
    PARTITION p_2000_2009 VALUES LESS THAN (2010),
    PARTITION p_2010_2019 VALUES LESS THAN (2020),
    PARTITION p_2020_2029 VALUES LESS THAN (2030),
    PARTITION p_2030_2039 VALUES LESS THAN (2040),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

CREATE TABLE clauses (
    clause_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    clause_uuid CHAR(36) DEFAULT (UUID()) NOT NULL,

    -- Relationship fields
    statute_id BIGINT UNSIGNED NOT NULL,
    parent_clause_id BIGINT UNSIGNED,

    -- Hierarchy tracking
    hierarchy_level TINYINT UNSIGNED NOT NULL DEFAULT 0,
    breadth_position DECIMAL(10,4) NOT NULL DEFAULT 0.0000,
    materialized_path VARCHAR(1000),
    tree_depth TINYINT UNSIGNED GENERATED ALWAYS AS (
        LENGTH(materialized_path) - LENGTH(REPLACE(materialized_path, '.', ''))
    ) STORED,

    -- Identification
    clause_number VARCHAR(100) NOT NULL,
    clause_type ENUM('CHAPTER','PART','SECTION','SUBSECTION','PARAGRAPH','SUBPARAGRAPH','ITEM','SUBITEM','SCHEDULE','ANNEXURE','PREAMBLE','INTERPRETATION') NOT NULL,
    clause_nature ENUM('OPERATIVE','DEFINITIONAL','MACHINERY','TRANSITIONAL','INTERPRETATIVE','PREAMBULAR','EXAMPLE') DEFAULT 'OPERATIVE',

    -- Content
    clause_title VARCHAR(500),
    clause_heading VARCHAR(500),
    clause_text LONGTEXT,
    plain_text LONGTEXT,

    -- Flags and metadata
    is_substantive BOOLEAN DEFAULT TRUE,
    contains_cross_reference BOOLEAN DEFAULT FALSE,
    is_amended BOOLEAN DEFAULT FALSE,
    is_inserted BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    is_repealed BOOLEAN DEFAULT FALSE,
    amendment_notes TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Constraints
    FOREIGN KEY (statute_id) REFERENCES statutes(statute_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_clause_id) REFERENCES clauses(clause_id),
    UNIQUE KEY uk_clause_path (statute_id, materialized_path(200)),

    -- Hierarchy indexes
    INDEX idx_statute_hierarchy (statute_id, hierarchy_level, breadth_position),
    INDEX idx_materialized_path (materialized_path(200)),
    INDEX idx_clause_number (statute_id, clause_number),
    INDEX idx_parent (parent_clause_id),
    INDEX idx_substantive (is_substantive),
    INDEX idx_clause_type (statute_id, clause_type, hierarchy_level),

    -- Navigation indexes
    INDEX idx_sibling_nav (parent_clause_id, breadth_position, clause_id, clause_type),

    -- Full-text indexes
    FULLTEXT INDEX ft_clause_title (clause_title, clause_heading) WITH PARSER ngram,
    FULLTEXT INDEX ft_clause_text (clause_text) WITH PARSER ngram,
    FULLTEXT INDEX ft_clause_combined (clause_title, clause_heading, clause_text) WITH PARSER ngram

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC
PARTITION BY RANGE (statute_id) (
    PARTITION p_clauses_1 VALUES LESS THAN (10000),
    PARTITION p_clauses_2 VALUES LESS THAN (20000),
    PARTITION p_clauses_3 VALUES LESS THAN (50000),
    PARTITION p_clauses_4 VALUES LESS THAN (100000),
    PARTITION p_clauses_5 VALUES LESS THAN (200000),
    PARTITION p_clauses_6 VALUES LESS THAN (500000),
    PARTITION p_clauses_7 VALUES LESS THAN (1000000),
    PARTITION p_clauses_max VALUES LESS THAN MAXVALUE
);

-- ------------------------------------------------------------
-- 3. INGESTION AND AUDIT TABLES
-- ------------------------------------------------------------

CREATE TABLE ingestion_manifest (
    manifest_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    manifest_uuid CHAR(36) DEFAULT (UUID()) NOT NULL,

    -- Source tracking
    source_system VARCHAR(100) NOT NULL,
    source_environment ENUM('production','staging','development','testing','archive') DEFAULT 'production',
    source_format ENUM('XML','JSON','PDF','HTML','TXT','CSV','DOCX','OCR','API','MANUAL') NOT NULL,
    source_version VARCHAR(20),
    original_uri VARCHAR(2000),
    file_path VARCHAR(1000) NOT NULL,
    file_name VARCHAR(255),

    -- Integrity verification
    sha256_checksum CHAR(64),
    md5_checksum CHAR(32),
    file_size_bytes BIGINT UNSIGNED,
    compression_ratio DECIMAL(5,2),

    -- Batch correlation
    ingestion_batch_id VARCHAR(100),
    correlation_id VARCHAR(100),
    batch_sequence_number INT UNSIGNED,

    -- Processing state machine
    status ENUM(
        'DISCOVERED','PENDING','QUEUED','VALIDATING','TRANSFORMING',
        'LOADING','VERIFYING','COMPLETED',
        'VALIDATION_FAILED','TRANSFORMATION_FAILED','LOAD_FAILED','VERIFICATION_FAILED',
        'RETRYING','CANCELLED','ARCHIVED'
    ) DEFAULT 'PENDING',
    status_history JSON,

    -- Retry management
    retry_count TINYINT UNSIGNED DEFAULT 0,
    max_retries TINYINT UNSIGNED DEFAULT 3,
    next_retry_at TIMESTAMP NULL,
    retry_backoff_seconds INT UNSIGNED DEFAULT 60,

    -- Timing metrics
    discovered_at TIMESTAMP NULL,
    queued_at TIMESTAMP NULL,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    processing_duration_seconds INT UNSIGNED GENERATED ALWAYS AS (
        TIMESTAMPDIFF(SECOND, started_at, completed_at)
    ) STORED,
    queue_wait_seconds INT UNSIGNED GENERATED ALWAYS AS (
        TIMESTAMPDIFF(SECOND, queued_at, started_at)
    ) STORED,

    -- Record metrics
    records_discovered INT UNSIGNED DEFAULT 0,
    records_processed INT UNSIGNED DEFAULT 0,
    records_inserted INT UNSIGNED DEFAULT 0,
    records_updated INT UNSIGNED DEFAULT 0,
    records_failed INT UNSIGNED DEFAULT 0,
    records_skipped INT UNSIGNED DEFAULT 0,

    -- Priority and scheduling
    priority TINYINT UNSIGNED DEFAULT 5,
    scheduled_for TIMESTAMP NULL,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Indexes
    UNIQUE KEY uk_manifest_uuid (manifest_uuid),
    INDEX idx_status_time (status, created_at),
    INDEX idx_status_priority_retry (status, priority, next_retry_at),
    INDEX idx_source_time (source_system, created_at),
    INDEX idx_batch (ingestion_batch_id),
    INDEX idx_correlation (correlation_id),
    INDEX idx_scheduled (scheduled_for, status),
    INDEX idx_file_checksum (sha256_checksum),

    -- Partial index for active work (MySQL 8.0.13+)
    INDEX idx_active_queue (status, priority, manifest_id) WHERE status IN ('PENDING','QUEUED','RETRYING')

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
    PARTITION p_ingest_2023_01 VALUES LESS THAN (202302),
    PARTITION p_ingest_2023_02 VALUES LESS THAN (202303),
    -- ... additional monthly partitions
    PARTITION p_ingest_2024_01 VALUES LESS THAN (202402),
    PARTITION p_ingest_2024_02 VALUES LESS THAN (202403),
    PARTITION p_ingest_2024_03 VALUES LESS THAN (202404),
    PARTITION p_ingest_2024_04 VALUES LESS THAN (202405),
    PARTITION p_ingest_2024_05 VALUES LESS THAN (202406),
    PARTITION p_ingest_2024_06 VALUES LESS THAN (202407),
    PARTITION p_ingest_2024_07 VALUES LESS THAN (202408),
    PARTITION p_ingest_2024_08 VALUES LESS THAN (202409),
    PARTITION p_ingest_2024_09 VALUES LESS THAN (202410),
    PARTITION p_ingest_2024_10 VALUES LESS THAN (202411),
    PARTITION p_ingest_2024_11 VALUES LESS THAN (202412),
    PARTITION p_ingest_2024_12 VALUES LESS THAN (202501),
    PARTITION p_ingest_2025_01 VALUES LESS THAN (202502),
    PARTITION p_ingest_future VALUES LESS THAN MAXVALUE
);

CREATE TABLE ingestion_errors (
    error_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    manifest_id BIGINT UNSIGNED NOT NULL,

    -- Error classification
    error_code VARCHAR(50) NOT NULL,
    error_category ENUM('SCHEMA','VALIDATION','TRANSFORMATION','LOAD','NETWORK','PERMISSION','TIMEOUT','UNKNOWN') DEFAULT 'UNKNOWN',
    error_severity ENUM('WARNING','ERROR','CRITICAL','FATAL') DEFAULT 'ERROR',

    -- Error details
    error_message TEXT,
    error_stack TEXT,
    error_context JSON,

    -- Record identification
    record_identifier VARCHAR(500),
    record_sequence_number INT UNSIGNED,
    field_name VARCHAR(100),
    field_value TEXT,
    expected_format TEXT,

    -- Resolution
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    resolution_notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (manifest_id) REFERENCES ingestion_manifest(manifest_id) ON DELETE CASCADE,
    INDEX idx_manifest (manifest_id),
    INDEX idx_error_code (error_code),
    INDEX idx_severity (error_severity),
    INDEX idx_category (error_category),
    INDEX idx_created (created_at),
    INDEX idx_unresolved (is_resolved, error_severity) WHERE is_resolved = FALSE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 4. RELATIONSHIP AND HISTORY TABLES
-- ------------------------------------------------------------

CREATE TABLE amendment_history (
    amendment_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- Amendment relationship
    amended_statute_id BIGINT UNSIGNED NOT NULL,
    amending_statute_id BIGINT UNSIGNED NOT NULL,

    -- Amendment details
    amendment_type ENUM('TEXTUAL','STRUCTURAL','REPEAL','REVIVAL','CONSOLIDATION','REENACTMENT','RENUMBERING') NOT NULL,
    amendment_description TEXT,
    amendment_text LONGTEXT,

    -- Affected scope
    prior_version_clause_id BIGINT UNSIGNED,
    new_version_clause_id BIGINT UNSIGNED,
    affected_clauses JSON,
    affected_provisions TEXT,

    -- Temporal
    effective_date DATE,
    proclaimed_date DATE,
    gazette_reference VARCHAR(100),

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (amended_statute_id) REFERENCES statutes(statute_id),
    FOREIGN KEY (amending_statute_id) REFERENCES statutes(statute_id),
    FOREIGN KEY (prior_version_clause_id) REFERENCES clauses(clause_id),
    FOREIGN KEY (new_version_clause_id) REFERENCES clauses(clause_id),

    INDEX idx_amended (amended_statute_id),
    INDEX idx_amending (amending_statute_id),
    INDEX idx_effective (effective_date),
    INDEX idx_type (amendment_type),
    INDEX idx_amended_effective (amended_statute_id, effective_date)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE cross_references (
    reference_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- Source
    source_statute_id BIGINT UNSIGNED,
    source_clause_id BIGINT UNSIGNED,
    source_clause_path VARCHAR(200),

    -- Reference type
    reference_type ENUM('EXPLICIT','IMPLICIT','DEFINED_TERM','PENALTY_REFERENCE','SAVINGS_CLAUSE','TRANSITIONAL','EXPLANATORY','HISTORICAL') DEFAULT 'EXPLICIT',
    reference_nature ENUM('MANDATORY','PERMISSIVE','DEFINITIONAL','ILLUSTRATIVE','CONDITIONAL') DEFAULT 'MANDATORY',

    -- Internal targets
    target_statute_id BIGINT UNSIGNED,
    target_clause_id BIGINT UNSIGNED,
    target_clause_path VARCHAR(200),

    -- External targets
    target_treaty_id BIGINT UNSIGNED,
    target_jurisdiction_code VARCHAR(10),
    external_citation VARCHAR(500),
    external_url VARCHAR(1000),

    -- Parsing metadata
    citation_text VARCHAR(500) NOT NULL,
    citation_context TEXT,
    parsed_confidence DECIMAL(3,2) DEFAULT 1.00,
    parsing_method ENUM('REGEX','NLP','MANUAL','IMPORTED','VALIDATED') DEFAULT 'REGEX',
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP NULL,

    -- Verification
    verification_status ENUM('UNVERIFIED','CONFIRMED','MOVED','BROKEN','DISPUTED','SUPERSEDED') DEFAULT 'UNVERIFIED',
    last_verified_at TIMESTAMP NULL,
    verification_notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (source_statute_id) REFERENCES statutes(statute_id),
    FOREIGN KEY (source_clause_id) REFERENCES clauses(clause_id),
    FOREIGN KEY (target_statute_id) REFERENCES statutes(statute_id),
    FOREIGN KEY (target_clause_id) REFERENCES clauses(clause_id),
    FOREIGN KEY (target_jurisdiction_code) REFERENCES jurisdictions(jurisdiction_code),

    INDEX idx_source (source_statute_id, source_clause_id),
    INDEX idx_target_statute (target_statute_id),
    INDEX idx_target_clause (target_clause_id),
    INDEX idx_citation (citation_text(200)),
    INDEX idx_external (external_citation(200)),
    INDEX idx_verification (verification_status, last_verified_at),
    INDEX idx_confidence (parsed_confidence),

    FULLTEXT INDEX ft_citation_context (citation_context) WITH PARSER ngram

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 5. DIRCO TREATY TABLES
-- ------------------------------------------------------------

CREATE TABLE treaties (
    treaty_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    treaty_uuid CHAR(36) DEFAULT (UUID()) NOT NULL,

    -- Identification
    treaty_series_number VARCHAR(100),
    sadc_treaty_number VARCHAR(50),
    au_treaty_number VARCHAR(50),
    dirco_reference VARCHAR(50),
    un_registration_number VARCHAR(50),
    un_treaty_collection VARCHAR(50),

    -- Classification
    treaty_type ENUM('BILATERAL','MULTILATERAL','PLURILATERAL','REGIONAL','ORGANIZATIONAL','CONSTITUENT') NOT NULL,
    treaty_subtype VARCHAR(50),
    vienna_category VARCHAR(100),

    -- Subject matter
    subject_keywords JSON,
    subject_categories JSON,

    -- Titles
    title_en VARCHAR(1000) NOT NULL,
    title_fr VARCHAR(1000),
    title_other VARCHAR(1000),
    short_title VARCHAR(255),
    abbreviation VARCHAR(50),

    -- Temporal
    adoption_date DATE,
    signature_date DATE,
    ratification_date DATE,
    entry_into_force_date DATE,
    provisional_application_date DATE,
    termination_date DATE,
    duration_years SMALLINT UNSIGNED,
    is_indefinite BOOLEAN DEFAULT FALSE,

    -- Depository
    depository_state VARCHAR(100),
    depository_organization VARCHAR(200),
    depository_contact TEXT,

    -- Languages
    authentic_languages JSON,
    authoritative_language_for_za ENUM('ENGLISH','AFRIKAANS','BOTH','NEITHER','NOT_SPECIFIED') DEFAULT 'NOT_SPECIFIED',

    -- Parties
    party_countries JSON,
    party_count SMALLINT UNSIGNED,
    signatory_count SMALLINT UNSIGNED,

    -- Status
    status ENUM('NEGOTIATING','ADOPTED','SIGNED','RATIFIED','IN_FORCE','AMENDED','TERMINATED','SUSPENDED','SUPERSEDED') DEFAULT 'NEGOTIATING',

    -- Content
    treaty_text LONGTEXT,
    preamble_text LONGTEXT,
    annexes JSON,
    protocols JSON,

    -- South Africa specific - Section 231 Constitution
    section_231_approval_date DATE,
    parliamentary_resolution_number VARCHAR(50),
    ncop_resolution_number VARCHAR(50),
    presidential_proclamation_number VARCHAR(50),
    constitutional_court_validation BOOLEAN DEFAULT FALSE,
    constitutional_court_case_reference VARCHAR(100),

    -- DIRCO workflow
    negotiation_lead_directorate ENUM('LEGAL','MULTILATERAL','BILATERAL','CONSULAR','PROTOCOL','DISARMAMENT','TRADE','HUMAN_RIGHTS','ENVIRONMENT','OTHER'),
    cabinet_memorandum_number VARCHAR(50),
    state_law_adviser_clearance BOOLEAN DEFAULT FALSE,
    clearance_date DATE,
    responsible_officer VARCHAR(100),
    responsible_officer_contact VARCHAR(255),

    -- Domestic implementation
    domestic_implementation_required BOOLEAN DEFAULT TRUE,
    implementation_act_id BIGINT UNSIGNED,
    implementation_status ENUM('NONE_REQUIRED','REQUIRED_PENDING','PARTIALLY_IMPLEMENTED','FULLY_IMPLEMENTED','OVER_IMPLEMENTED','EXCEEDS_REQUIREMENTS') DEFAULT 'REQUIRED_PENDING',
    implementation_assessment_date DATE,
    implementation_assessment_summary TEXT,
    implementation_gap_analysis TEXT,

    -- Version linking
    prior_version_treaty_id BIGINT UNSIGNED,
    successor_treaty_id BIGINT UNSIGNED,
    parent_treaty_id BIGINT UNSIGNED,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    UNIQUE KEY uk_treaty_uuid (treaty_uuid),
    UNIQUE KEY uk_dirco_ref (dirco_reference),

    -- Foreign keys
    FOREIGN KEY (prior_version_treaty_id) REFERENCES treaties(treaty_id),
    FOREIGN KEY (successor_treaty_id) REFERENCES treaties(treaty_id),
    FOREIGN KEY (parent_treaty_id) REFERENCES treaties(treaty_id),

    -- Core indexes
    INDEX idx_series (treaty_series_number),
    INDEX idx_sadc (sadc_treaty_number),
    INDEX idx_au (au_treaty_number),
    INDEX idx_entry_force (entry_into_force_date),
    INDEX idx_status (status),
    INDEX idx_type_status (treaty_type, status),
    INDEX idx_approval_date (section_231_approval_date),
    INDEX idx_implementation (implementation_status, implementation_assessment_date),

    -- Full-text indexes
    FULLTEXT INDEX ft_title_en (title_en) WITH PARSER ngram,
    FULLTEXT INDEX ft_title_fr (title_fr) WITH PARSER ngram,
    FULLTEXT INDEX ft_treaty_text (treaty_text) WITH PARSER ngram,
    FULLTEXT INDEX ft_preamble (preamble_text) WITH PARSER ngram,
    FULLTEXT INDEX ft_combined (title_en, preamble_text, treaty_text) WITH PARSER ngram

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC
PARTITION BY RANGE (YEAR(entry_into_force_date)) (
    PARTITION p_treaty_before_1900 VALUES LESS THAN (1900),
    PARTITION p_treaty_1900_1949 VALUES LESS THAN (1950),
    PARTITION p_treaty_1950_1959 VALUES LESS THAN (1960),
    PARTITION p_treaty_1960_1969 VALUES LESS THAN (1970),
    PARTITION p_treaty_1970_1979 VALUES LESS THAN (1980),
    PARTITION p_treaty_1980_1989 VALUES LESS THAN (1990),
    PARTITION p_treaty_1990_1994 VALUES LESS THAN (1995),
    PARTITION p_treaty_1995_1999 VALUES LESS THAN (2000),
    PARTITION p_treaty_2000_2009 VALUES LESS THAN (2010),
    PARTITION p_treaty_2010_2019 VALUES LESS THAN (2020),
    PARTITION p_treaty_2020_2029 VALUES LESS THAN (2030),
    PARTITION p_treaty_future VALUES LESS THAN MAXVALUE
);

CREATE TABLE treaty_actions (
    action_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    action_uuid CHAR(36) DEFAULT (UUID()) NOT NULL,

    treaty_id BIGINT UNSIGNED NOT NULL,

    -- Action classification
    action_type ENUM(
        'SIGNATURE_SIMPLE','SIGNATURE_DEFINITIVE','SIGNATURE_CONDITIONAL','SIGNATURE_AD_REFERENDUM',
        'RATIFICATION','ACCESSION','ACCEPTANCE','APPROVAL','SUCCESSION','CONTINUATION','PROVISIONAL_APPLICATION',
        'RESERVATION','DECLARATION_INTERPRETATIVE','DECLARATION_SUBSTANTIVE','DECLARATION_TERRITORIAL',
        'OBJECTION','WITHDRAWAL_OBJECTION','MODIFICATION_OF_RESERVATION','WITHDRAWAL_OF_RESERVATION',
        'AMENDMENT','PROTOCOL','EXTENSION','MODIFICATION','TERMINATION_AGREEMENT',
        'DENUNCIATION','WITHDRAWAL','EXPIRY','SUPERSESSION',
        'ENTRY_INTO_FORCE','ENTRY_INTO_FORCE_FOR_STATE'
    ) NOT NULL,
    action_subtype VARCHAR(50),

    -- Actor
    acting_state_id VARCHAR(10),
    acting_entity VARCHAR(200),
    acting_organization_code VARCHAR(20),
    authorized_signatory VARCHAR(255),
    signatory_title VARCHAR(100),
    full_powers_reference VARCHAR(200),

    -- Dates
    action_date DATE NOT NULL,
    action_time TIME,
    effective_date DATE,
    notification_date DATE,
    notification_receipt_date DATE,
    notification_processed_date DATE,
    depositary_confirmation_date DATE,

    -- Reservation/declaration specific
    reservation_text LONGTEXT,
    reservation_scope VARCHAR(500),
    reservation_provisions JSON,
    reservation_validity ENUM('PERMISSIBLE','IMPERMISSIBLE','OBJECTED_TO','DISPUTED','WITHDRAWN') DEFAULT 'PERMISSIBLE',

    -- Objection specific
    target_state_id VARCHAR(10),
    target_reservation_id BIGINT UNSIGNED,
    objection_grounds TEXT,
    prevents_entry_into_force BOOLEAN DEFAULT FALSE,
    prevents_treaty_operation BOOLEAN DEFAULT FALSE,

    -- Amendment specific
    amended_provisions JSON,
    resulting_treaty_id BIGINT UNSIGNED,

    -- Description
    action_description TEXT,
    action_document_url VARCHAR(1000),
    action_document_reference VARCHAR(200),

    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP NULL,

    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    source_reference VARCHAR(500),

    FOREIGN KEY (treaty_id) REFERENCES treaties(treaty_id) ON DELETE CASCADE,
    FOREIGN KEY (acting_state_id) REFERENCES jurisdictions(jurisdiction_code),
    FOREIGN KEY (target_state_id) REFERENCES jurisdictions(jurisdiction_code),
    FOREIGN KEY (resulting_treaty_id) REFERENCES treaties(treaty_id),

    UNIQUE KEY uk_action_uuid (action_uuid),
    INDEX idx_treaty_date (treaty_id, action_date),
    INDEX idx_treaty_type_date (treaty_id, action_type, action_date),
    INDEX idx_type_date (action_type, action_date),
    INDEX idx_acting_state (acting_state_id),
    INDEX idx_target_state (target_state_id),
    INDEX idx_effective (effective_date),
    INDEX idx_notification (notification_receipt_date),
    INDEX idx_reservation (reservation_validity),
    INDEX idx_resulting (resulting_treaty_id)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
PARTITION BY RANGE (treaty_id) (
    PARTITION p_actions_1 VALUES LESS THAN (1000),
    PARTITION p_actions_2 VALUES LESS THAN (5000),
    PARTITION p_actions_3 VALUES LESS THAN (10000),
    PARTITION p_actions_4 VALUES LESS THAN (50000),
    PARTITION p_actions_5 VALUES LESS THAN (100000),
    PARTITION p_actions_max VALUES LESS THAN MAXVALUE
);

CREATE TABLE treaty_parties (
    treaty_id BIGINT UNSIGNED NOT NULL,
    country_code VARCHAR(10) NOT NULL,

    -- Party relationship
    party_type ENUM('ORIGINAL_SIGNATORY','SUBSEQUENT_SIGNATORY','ORIGINAL_NEGOTIATOR','ACceding_STATE','SUCCESSION','CONTINUATION','TRANSFERRED_RIGHTS') DEFAULT 'ORIGINAL_SIGNATORY',

    -- Key dates
    signature_date DATE,
    signature_type ENUM('SIMPLE','DEFINITIVE','CONDITIONAL','AD_REFERENDUM'),
    ratification_date DATE,
    ratification_type ENUM('RATIFICATION','ACCEPTANCE','APPROVAL'),
    accession_date DATE,
    succession_date DATE,
    entry_into_force_for_state DATE,

    -- Current status
    current_status ENUM('ACTIVE','WITHDRAWN','DENOUNCED','SUSPENDED','IN_DEFAULT','INACTIVE_DISPUTE') DEFAULT 'ACTIVE',
    status_effective_date DATE,

    -- Withdrawal
    withdrawal_notification_date DATE,
    withdrawal_effective_date DATE,
    withdrawal_grounds TEXT,

    -- Reservations and declarations
    reservations_count SMALLINT UNSIGNED DEFAULT 0,
    declarations_count SMALLINT UNSIGNED DEFAULT 0,

    -- Implementation
    domestic_implementation_status ENUM('NOT_REQUIRED','PENDING','PARTIAL','COMPLETE','EXCEEDS') DEFAULT 'NOT_REQUIRED',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (treaty_id, country_code),

    FOREIGN KEY (treaty_id) REFERENCES treaties(treaty_id) ON DELETE CASCADE,
    FOREIGN KEY (country_code) REFERENCES jurisdictions(jurisdiction_code),

    INDEX idx_country (country_code),
    INDEX idx_country_status (country_code, current_status),
    INDEX idx_status (current_status),
    INDEX idx_entry_force (entry_into_force_for_state),
    INDEX idx_ratification (ratification_date)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE treaty_statute_links (
    link_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    -- Treaty reference
    treaty_id BIGINT UNSIGNED NOT NULL,
    treaty_article_reference VARCHAR(100),

    -- Statute reference
    statute_id BIGINT UNSIGNED,
    clause_id BIGINT UNSIGNED,

    -- Implementation details
    implementation_mechanism ENUM('DIRECT_INCORPORATION','SELF_EXECUTING','TRANSFORMATIVE_LEGISLATION','EXECUTIVE_ACTION','JUDICIAL_RECOGNITION','CUSTOMARY_LAW_STATUS','POLITICAL_COMMITMENT') NOT NULL,
    transformation_type ENUM('WHOLESALE_ADOPTION','SELECTIVE_IMPLEMENTATION','EXCEEDING_TREATY','RESTRICTIVE_IMPLEMENTATION','DIVERGENT_IMPLEMENTATION') DEFAULT 'SELECTIVE_IMPLEMENTATION',
    implementation_completeness ENUM('NONE','PARTIAL','COMPLETE','EXCEEDS') DEFAULT 'NONE',

    -- Fidelity assessment
    implementation_fidelity_score DECIMAL(3,2),
    implementation_fidelity_assessment TEXT,
    gap_analysis TEXT,

    -- Self-execution
    is_self_executing BOOLEAN,
    declared_non_self_executing BOOLEAN,
    non_self_execution_authority VARCHAR(100),
    non_self_execution_date DATE,
    non_self_execution_text TEXT,
    requires_legislative_implementation BOOLEAN,

    -- Verification
    verified_by VARCHAR(100),
    verified_at TIMESTAMP NULL,
    verification_method ENUM('LEGAL_OPINION','JUDICIAL_INTERPRETATION','LEGISLATIVE_HISTORY','COMPARATIVE_ANALYSIS') DEFAULT 'LEGAL_OPINION',

    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (treaty_id) REFERENCES treaties(treaty_id) ON DELETE CASCADE,
    FOREIGN KEY (statute_id) REFERENCES statutes(statute_id),
    FOREIGN KEY (clause_id) REFERENCES clauses(clause_id),

    UNIQUE KEY uk_treaty_statute (treaty_id, statute_id, treaty_article_reference),
    INDEX idx_statute (statute_id),
    INDEX idx_mechanism (implementation_mechanism),
    INDEX idx_fidelity (implementation_fidelity_score),
    INDEX idx_self_exec (is_self_executing, declared_non_self_executing)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- 6. SAMPLE DATA INSERTION
-- ------------------------------------------------------------

-- 6.1 Jurisdictions
INSERT INTO jurisdictions (jurisdiction_code, jurisdiction_name, jurisdiction_type, iso_3166_1_alpha_2, materialized_path, tree_depth, is_recognized_state, treaty_eligible) VALUES
('ZA', 'Republic of South Africa', 'NATIONAL', 'ZA', 'ZA', 0, TRUE, TRUE),
('ZA-EC', 'Eastern Cape', 'PROVINCIAL', NULL, 'ZA.ZA-EC', 1, FALSE, FALSE),
('ZA-FS', 'Free State', 'PROVINCIAL', NULL, 'ZA.ZA-FS', 1, FALSE, FALSE),
('ZA-GP', 'Gauteng', 'PROVINCIAL', NULL, 'ZA.ZA-GP', 1, FALSE, FALSE),
('ZA-KZN', 'KwaZulu-Natal', 'PROVINCIAL', NULL, 'ZA.ZA-KZN', 1, FALSE, FALSE),
('ZA-LP', 'Limpopo', 'PROVINCIAL', NULL, 'ZA.ZA-LP', 1, FALSE, FALSE),
('ZA-MP', 'Mpumalanga', 'PROVINCIAL', NULL, 'ZA.ZA-MP', 1, FALSE, FALSE),
('ZA-NC', 'Northern Cape', 'PROVINCIAL', NULL, 'ZA.ZA-NC', 1, FALSE, FALSE),
('ZA-NW', 'North-West', 'PROVINCIAL', NULL, 'ZA.ZA-NW', 1, FALSE, FALSE),
('ZA-WC', 'Western Cape', 'PROVINCIAL', NULL, 'ZA.ZA-WC', 1, FALSE, FALSE),
('NA', 'Republic of Namibia', 'NATIONAL', 'NA', 'NA', 0, TRUE, TRUE),
('BW', 'Republic of Botswana', 'NATIONAL', 'BW', 'BW', 0, TRUE, TRUE),
('ZW', 'Republic of Zimbabwe', 'NATIONAL', 'ZW', 'ZW', 0, TRUE, TRUE),
('MZ', 'Republic of Mozambique', 'NATIONAL', 'MZ', 'MZ', 0, TRUE, TRUE),
('SADC', 'Southern African Development Community', 'ORGANIZATION', NULL, 'SADC', 0, FALSE, TRUE),
('AU', 'African Union', 'ORGANIZATION', NULL, 'AU', 0, FALSE, TRUE),
('UN', 'United Nations', 'ORGANIZATION', NULL, 'UN', 0, FALSE, TRUE);

-- 6.2 Constitution of South Africa, 1996
INSERT INTO statutes (
    jurisdiction_code, statute_type, statute_number, version_identifier,
    enacted_date, effective_date, gazette_number, gazette_year,
    short_title, long_title, preamble_text, status
) VALUES (
    'ZA', 'ACT', '108 of 1996', 'original',
    '1996-05-08', '1997-02-04', '17678', 1996,
    'Constitution of the Republic of South Africa, 1996',
    'To introduce a new Constitution for the Republic of South Africa and to provide for matters incidental thereto.',
    'We, the people of South Africa,\nRecognise the injustices of our past;\nHonour those who suffered for justice and freedom in our land;\nRespect those who have worked to build and develop our country; and\nBelieve that South Africa belongs to all who live in it, united in our diversity.',
    'IN_FORCE'
);

SET @constitution_id = LAST_INSERT_ID();

-- Constitution Chapters
INSERT INTO clauses (statute_id, clause_number, clause_type, hierarchy_level, breadth_position, materialized_path, clause_title, clause_text, clause_nature) VALUES
(@constitution_id, '1', 'CHAPTER', 0, 1.0000, '1', 'Chapter 1', 'Founding Provisions', 'OPERATIVE'),
(@constitution_id, '2', 'CHAPTER', 0, 2.0000, '2', 'Chapter 2', 'Bill of Rights', 'OPERATIVE'),
(@constitution_id, '3', 'CHAPTER', 0, 3.0000, '3', 'Chapter 3', 'Co-operative Government', 'OPERATIVE'),
(@constitution_id, '4', 'CHAPTER', 0, 4.0000, '4', 'Chapter 4', 'Parliament', 'OPERATIVE'),
(@constitution_id, '5', 'CHAPTER', 0, 5.0000, '5', 'Chapter 5', 'The President and National Executive', 'OPERATIVE'),
(@constitution_id, '6', 'CHAPTER', 0, 6.0000, '6', 'Chapter 6', 'Provinces', 'OPERATIVE'),
(@constitution_id, '7', 'CHAPTER', 0, 7.0000, '7', 'Chapter 7', 'Local Government', 'OPERATIVE'),
(@constitution_id, '8', 'CHAPTER', 0, 8.0000, '8', 'Chapter 8', 'Courts and Administration of Justice', 'OPERATIVE'),
(@constitution_id, '9', 'CHAPTER', 0, 9.0000, '9', 'Chapter 9', 'State Institutions Supporting Constitutional Democracy', 'OPERATIVE'),
(@constitution_id, '10', 'CHAPTER', 0, 10.0000, '10', 'Chapter 10', 'Public Administration', 'OPERATIVE'),
(@constitution_id, '11', 'CHAPTER', 0, 11.0000, '11', 'Chapter 11', 'Security Services', 'OPERATIVE'),
(@constitution_id, '12', 'CHAPTER', 0, 12.0000, '12', 'Chapter 12', 'Traditional Leaders', 'OPERATIVE'),
(@constitution_id, '13', 'CHAPTER', 0, 13.0000, '13', 'Chapter 13', 'Finance', 'OPERATIVE'),
(@constitution_id, '14', 'CHAPTER', 0, 14.0000, '14', 'Chapter 14', 'General Provisions', 'OPERATIVE');

-- Bill of Rights sections (sample)
INSERT INTO clauses (statute_id, clause_number, clause_type, hierarchy_level, breadth_position, materialized_path, clause_title, clause_text, clause_nature, is_substantive) VALUES
(@constitution_id, '2.7', 'SECTION', 1, 2.0700, '2.7', 'Life', 'Everyone has the right to life.', 'OPERATIVE', TRUE),
(@constitution_id, '2.9', 'SECTION', 1, 2.0900, '2.9', 'Equality', 'Everyone is equal before the law and has the right to equal protection and benefit of the law.', 'OPERATIVE', TRUE),
(@constitution_id, '2.10', 'SECTION', 1, 2.1000, '2.10', 'Human Dignity', 'Everyone has inherent dignity and the right to have their dignity respected and protected.', 'OPERATIVE', TRUE),
(@constitution_id, '2.16', 'SECTION', 1, 2.1600, '2.16', 'Freedom of Expression', '(1) Everyone has the right to freedom of expression, which includes—\n(a) freedom of the press and other media;\n(b) freedom to receive or impart information or ideas;\n(c) freedom of artistic creativity; and\n(d) academic freedom and freedom of scientific research.', 'OPERATIVE', TRUE),
(@constitution_id, '2.231', 'SECTION', 1, 2.2310, '2.231', 'International agreements', '(1) The negotiating and signing of all international agreements is the responsibility of the national executive.\n(2) An international agreement binds the Republic only after it has been approved by resolution in both the National Assembly and the National Council of Provinces, unless it is an agreement referred to in subsection (3).\n(3) An international agreement of a technical, administrative or executive nature, or an agreement which does not require either ratification or accession, entered into by the national executive, binds the Republic without approval by the National Assembly and the National Council of Provinces, but must be tabled in the Assembly and the Council within a reasonable time.\n(4) Any international agreement becomes law in the Republic when it is enacted into law by national legislation; but a self-executing provision of an agreement that has been approved by Parliament is law in the Republic unless it is inconsistent with the Constitution or an Act of Parliament.\n(5) The Republic is bound by international agreements which were binding on the Republic when this Constitution took effect.', 'OPERATIVE', TRUE);

-- 6.3 PAIA and amendment chain
INSERT INTO statutes (
    jurisdiction_code, statute_type, statute_number, version_identifier,
    enacted_date, effective_date, short_title, long_title, status
) VALUES (
    'ZA', 'ACT', '2 of 2000', 'original',
    '2000-02-03', '2001-03-09',
    'Promotion of Access to Information Act',
    'To give effect to the constitutional right of access to any information held by the State and any information that is held by another person and that is required for the exercise or protection of any rights; and to provide for matters connected therewith.',
    'IN_FORCE'
);

SET @paia_id = LAST_INSERT_ID();

INSERT INTO statutes (
    jurisdiction_code, statute_type, statute_number, version_identifier,
    enacted_date, effective_date, short_title, long_title, prior_version_statute_id, status
) VALUES (
    'ZA', 'ACT', '54 of 2002', 'amending',
    '2002-12-18', '2003-02-15',
    'Promotion of Access to Information Amendment Act',
    'To amend the Promotion of Access to Information Act, 2000, so as to regulate access to information held by a private body for the purpose of protecting personal information; and to provide for matters connected therewith.',
    @paia_id,
    'IN_FORCE'
);

-- 6.4 Vienna Convention on the Law of Treaties
INSERT INTO treaties (
    treaty_series_number, title_en, short_title, abbreviation,
    adoption_date, signature_date, entry_into_force_date,
    depository_state, depository_organization, authentic_languages, party_count,
    status, dirco_reference, subject_keywords, treaty_type
) VALUES (
    'UNTS 1155',
    'Vienna Convention on the Law of Treaties',
    'Vienna Convention on the Law of Treaties',
    'VCLT 1969',
    '1969-05-23', '1969-05-23', '1980-01-27',
    'Austria', 'United Nations Secretary-General',
    '["English","French","Chinese","Russian","Spanish"]',
    116,
    'IN_FORCE', 'T-1993-0001',
    '["treaty law","international law","state responsibility","interpretation"]',
    'MULTILATERAL'
);

SET @vclt_id = LAST_INSERT_ID();

-- South African accession to VCLT
INSERT INTO treaty_actions (
    treaty_id, action_type, action_date, effective_date, acting_state_id,
    action_description, is_verified, verified_at
) VALUES (
    @vclt_id, 'ACCESSION', '1993-06-28', '1993-06-28', 'ZA',
    'South Africa acceded to the Vienna Convention on the Law of Treaties, deposited instrument of accession with the Secretary-General of the United Nations.',
    TRUE, '2024-01-15 10:30:00'
);

INSERT INTO treaty_parties (
    treaty_id, country_code, party_type, accession_date, entry_into_force_for_state,
    current_status, domestic_implementation_status
) VALUES (
    @vclt_id, 'ZA', 'ACceding_STATE', '1993-06-28', '1993-06-28',
    'ACTIVE', 'COMPLETE'
);

-- 6.5 SADC Treaty
INSERT INTO treaties (
    sadc_treaty_number, title_en, short_title,
    signature_date, entry_into_force_date,
    status, dirco_reference, party_count, subject_keywords, treaty_type
) VALUES (
    'SADC-T-001',
    'Treaty of the Southern African Development Community',
    'SADC Treaty',
    '1992-08-17', '1993-10-05',
    'AMENDED', 'T-1992-0001', 16,
    '["regional integration","economic cooperation","political cooperation","Southern Africa"]',
    'REGIONAL'
);

SET @sadc_treaty_id = LAST_INSERT_ID();

-- SADC member states
INSERT INTO treaty_parties (treaty_id, country_code, party_type, signature_date, ratification_date, entry_into_force_for_state, current_status) VALUES
(@sadc_treaty_id, 'ZA', 'ORIGINAL_SIGNATORY', '1992-08-17', '1993-09-30', '1993-10-05', 'ACTIVE'),
(@sadc_treaty_id, 'NA', 'ORIGINAL_SIGNATORY', '1992-08-17', '1993-03-09', '1993-10-05', 'ACTIVE'),
(@sadc_treaty_id, 'BW', 'ORIGINAL_SIGNATORY', '1992-08-17', '1992-12-29', '1993-10-05', 'ACTIVE'),
(@sadc_treaty_id, 'ZW', 'ORIGINAL_SIGNATORY', '1992-08-17', '1993-09-24', '1993-10-05', 'ACTIVE'),
(@sadc_treaty_id, 'MZ', 'ORIGINAL_SIGNATORY', '1992-08-17', '1993-08-18', '1993-10-05', 'ACTIVE');

-- 6.6 Ingestion manifest samples
INSERT INTO ingestion_manifest (
    source_system, source_format, original_uri, file_path, file_name,
    sha256_checksum, file_size_bytes, ingestion_batch_id,
    status, records_processed, records_inserted, records_failed,
    started_at, completed_at, priority
) VALUES (
    'GOVZA', 'XML', 'https://www.gov.za/sites/default/files/gcis_document/202401/gg49234.xml',
    '/data/ingestion/2024/gg49234.xml', 'gg49234.xml',
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 15728640,
    'BATCH-2024-001',
    'COMPLETED', 47, 47, 0,
    '2024-01-15 08:00:00', '2024-01-15 08:03:42', 5
);

INSERT INTO ingestion_manifest (
    source_system, source_format, original_uri, file_path, file_name,
    status, retry_count, error_code, error_message, priority
) VALUES (
    'SABINET', 'XML', 'https://api.sabinet.co.za/v2/statutes/batch-2024-03.xml',
    '/data/ingestion/failed/batch-2024-03.xml', 'batch-2024-03.xml',
    'VALIDATION_FAILED', 0, 'XSD_SCHEMA_VIOLATION',
    'Element statute_number: missing required element at line 1847, column 12. Schema validation failed for 3 of 50 records.', 5
);

-- 6.7 Cross references and treaty implementation links
INSERT INTO cross_references (
    source_statute_id, source_clause_path,
    target_treaty_id, reference_type, citation_text
) VALUES (
    @constitution_id, '2.231',
    @vclt_id, 'EXPLICIT',
    'the Vienna Convention on the Law of Treaties'
);

INSERT INTO treaty_statute_links (
    treaty_id, statute_id,
    implementation_mechanism, transformation_type,
    implementation_completeness
) VALUES (
    @vclt_id, @constitution_id,
    'TRANSFORMATIVE_LEGISLATION', 'SELECTIVE_IMPLEMENTATION',
    'PARTIAL'
);

-- ------------------------------------------------------------
-- 7. VERIFICATION AND COMPLETION
-- ------------------------------------------------------------

-- Re-enable constraints
SET FOREIGN_KEY_CHECKS = 1;
SET UNIQUE_CHECKS = 1;

-- Commit transaction
COMMIT;

-- Verify installation
SELECT 'Migration completed successfully' as status,
       (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE') as table_count,
       (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE()) as index_count,
       (SELECT COUNT(*) FROM information_schema.partitions WHERE table_schema = DATABASE() AND partition_name IS NOT NULL) as partition_count;

-- Sample verification queries
-- SELECT * FROM statutes WHERE short_title LIKE '%Constitution%' LIMIT 5;
-- SELECT * FROM clauses WHERE statute_id = @constitution_id AND materialized_path LIKE '2.%' ORDER BY breadth_position LIMIT 10;
-- SELECT * FROM treaties WHERE dirco_reference IS NOT NULL LIMIT 5;
