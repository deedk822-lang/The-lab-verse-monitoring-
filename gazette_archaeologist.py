#!/usr/bin/env python3
"""
gazette_archaeologist.py
Meta-Historian: Production Gazette Harvester for South African Government Gazettes
Target: 1950 (Apartheid Legislative Cascade)
 codex/implement-database-connection-pooling-739ujd
Deployment: GitHub Actions + S3-compatible storage + PostgreSQL

Deployment: GitHub Actions + Alibaba Cloud OSS + PostgreSQL
 codex/add-improvements-to-meta-historian-agent

Improvements:
- Connection pooling for database
- Concurrent downloads with rate limiting
- Retry logic with exponential backoff
- Comprehensive metrics tracking
- Batch database operations
- Better error recovery
- Health checks
- Progress tracking
"""

 codex/implement-database-connection-pooling-739ujd
import argparse

import importlib.util
 codex/add-improvements-to-meta-historian-agent
import json
import hashlib
import logging
import os
import re
import tempfile
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime
 codex/implement-database-connection-pooling-739ujd
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

 codex/add-improvements-to-meta-historian-agent
import pdfplumber
import psycopg2
from psycopg2 import pool
from psycopg2.extras import Json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


 codex/implement-database-connection-pooling-739ujd

ALIBABA_OSS_AVAILABLE = importlib.util.find_spec("oss2") is not None
if ALIBABA_OSS_AVAILABLE:
    import oss2
else:
    logging.warning("oss2 not available, falling back to boto3")

# ------------ Configuration ------------
 codex/add-improvements-to-meta-historian-agent
CONFIG = {
    "target_year": int(os.getenv("TARGET_YEAR", "1950")),
    "base_url": "https://gazettes.africa/gazettes/za",
    "postgres_dsn": os.getenv("DATABASE_URL", "postgresql://historian:pass@localhost:5432/meta_historian"),
    # Connection pooling
    "db_pool_min": int(os.getenv("DB_POOL_MIN", "2")),
    "db_pool_max": int(os.getenv("DB_POOL_MAX", "10")),
 codex/implement-database-connection-pooling-739ujd
    # Storage
    "bucket_name": os.getenv("BUCKET_NAME", "meta-historian-gazettes"),
    "s3_endpoint": os.getenv("S3_ENDPOINT"),
    "s3_access_key": os.getenv("S3_ACCESS_KEY_ID"),
    "s3_secret_key": os.getenv("S3_SECRET_ACCESS_KEY"),
    "s3_region": os.getenv("AWS_REGION", "us-east-1"),
    # Rate limiting and concurrency
    "rate_limit_seconds": float(os.getenv("RATE_LIMIT", "2.0")),
    "max_workers": int(os.getenv("MAX_WORKERS", "3")),

    # Storage: 'alibaba' or 'aws'
    "storage_provider": os.getenv("STORAGE_PROVIDER", "alibaba"),
    "bucket_name": os.getenv("BUCKET_NAME", "meta-historian-gazettes"),
    # Alibaba Cloud OSS settings
    "alibaba_access_key": os.getenv("ALIBABA_ACCESS_KEY_ID"),
    "alibaba_secret_key": os.getenv("ALIBABA_ACCESS_KEY_SECRET"),
    "alibaba_endpoint": os.getenv("ALIBABA_ENDPOINT", "https://oss-cn-shanghai.aliyuncs.com"),
    "alibaba_region": os.getenv("ALIBABA_REGION", "cn-shanghai"),
    # AWS S3 settings (fallback)
    "aws_access_key": os.getenv("AWS_ACCESS_KEY_ID"),
    "aws_secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "s3_endpoint": os.getenv("S3_ENDPOINT"),  # For MinIO compatibility
    # Rate limiting and concurrency
    "rate_limit_seconds": float(os.getenv("RATE_LIMIT", "2.0")),
    "max_workers": int(os.getenv("MAX_WORKERS", "3")),  # Concurrent downloads
 codex/add-improvements-to-meta-historian-agent
    "max_retries": int(os.getenv("MAX_RETRIES", "3")),
    # Processing limits
    "max_full_text_chars": 50000,
    "max_gazette_number": 200,  # Safety limit per year
    "consecutive_404_threshold": 15,
 codex/implement-database-connection-pooling-739ujd

    "batch_size": 10,  # Batch inserts
 codex/add-improvements-to-meta-historian-agent
    # Timeouts
    "request_timeout": 30,
    "connection_timeout": 10,
    # Confidence scoring
    "confidence_level": "VERY_HIGH",
    "min_act_length": 300,
    "min_section_count": 1,
}

 codex/implement-database-connection-pooling-739ujd
logger = logging.getLogger("gazette_archaeologist")


# ------------ Logging ------------
def setup_logging(target_year: int) -> None:

# ------------ Logging ------------
def setup_logging():
 codex/add-improvements-to-meta-historian-agent
    """Configure structured logging"""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"

    # File handler
 codex/implement-database-connection-pooling-739ujd
    file_handler = logging.FileHandler(f"harvester_{target_year}.log")

    file_handler = logging.FileHandler(f"harvester_{CONFIG['target_year']}.log")
 codex/add-improvements-to-meta-historian-agent
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Quiet noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("pdfplumber").setLevel(logging.WARNING)


 codex/implement-database-connection-pooling-739ujd

setup_logging()
logger = logging.getLogger("gazette_archaeologist")


 codex/add-improvements-to-meta-historian-agent
# ------------ Metrics Tracking ------------
@dataclass
class HarvestMetrics:
    """Track harvesting statistics"""

    gazettes_discovered: int = 0
    gazettes_processed: int = 0
    gazettes_skipped: int = 0
    gazettes_failed: int = 0
    acts_extracted: int = 0
    acts_stored: int = 0
    acts_updated: int = 0
    download_errors: int = 0
    parse_errors: int = 0
    storage_errors: int = 0
    db_errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    def duration(self) -> float:
        """Get duration in seconds"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    def summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            "duration_seconds": round(self.duration(), 2),
            "gazettes": {
                "discovered": self.gazettes_discovered,
                "processed": self.gazettes_processed,
                "skipped": self.gazettes_skipped,
                "failed": self.gazettes_failed,
                "success_rate": round(
                    self.gazettes_processed / max(1, self.gazettes_discovered) * 100, 2
                ),
            },
            "acts": {
                "extracted": self.acts_extracted,
                "stored": self.acts_stored,
                "updated": self.acts_updated,
                "success_rate": round(self.acts_stored / max(1, self.acts_extracted) * 100, 2),
            },
            "errors": {
                "download": self.download_errors,
                "parse": self.parse_errors,
                "storage": self.storage_errors,
                "database": self.db_errors,
                "total": self.download_errors
                + self.parse_errors
                + self.storage_errors
                + self.db_errors,
            },
        }


# ------------ Data Models ------------
@dataclass
class ParsedAct:
    """Structured extraction matching the Meta-Historian statute schema"""

    act_number: str  # "Act 41 of 1950"
    short_title: str
    long_title: str
    assent_date: Optional[date]
    commencement_date: Optional[date]
    preamble: str
    sections: Dict[str, Dict]
    full_text: str
    era: str
    page_range: Tuple[int, int]
    source_gazette_id: str
    source_url: str
    pdf_oss_key: str
    pdf_sha256: str
    field_confidence: Dict[str, str]

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate parsed data quality"""
        errors = []

        if not self.act_number or len(self.act_number) < 5:
            errors.append("Invalid act_number")

        if not self.short_title or len(self.short_title) < 3:
            errors.append("Invalid short_title")

        if len(self.full_text) < CONFIG["min_act_length"]:
            errors.append(f"Full text too short ({len(self.full_text)} chars)")

        if len(self.sections) < CONFIG["min_section_count"]:
            errors.append(f"Insufficient sections ({len(self.sections)})")

        if not self.assent_date:
            errors.append("Missing assent_date")

        return len(errors) == 0, errors

    def to_db_record(self) -> Dict[str, Any]:
        """Convert to database insertion format matching the statutes schema"""
 codex/implement-database-connection-pooling-739ujd
        source_metadata = {
            "source_gazette_id": self.source_gazette_id,
            "source_url": self.source_url,
            "pdf_oss_key": self.pdf_oss_key,
            "pdf_sha256": self.pdf_sha256,
        }

 codex/add-improvements-to-meta-historian-agent
        return {
            "act_number": self.act_number,
            "short_title": self.short_title[:255],
            "long_title": self.long_title[:1000] if self.long_title else None,
            "assent_date": self.assent_date,
            "commencement_date": self.commencement_date,
            "era": self.era,
            "preamble": self.preamble[:5000] if self.preamble else None,
            "objects_clause": Json(self._extract_objects()),
            "full_text": self.full_text[: CONFIG["max_full_text_chars"]],
            "sections": Json(self.sections),
            "confidence_level": CONFIG["confidence_level"],
            "confidence_probability": self._calculate_confidence(),
            "is_anchor": True,
            "anchor_type": "legislative",
            "source_gazette_id": self.source_gazette_id,
            "source_url": self.source_url,
 codex/implement-database-connection-pooling-739ujd
            "source_metadata": Json(source_metadata),

 codex/add-improvements-to-meta-historian-agent
            "semantic_embedding": None,
            "triggered_by_events": None,
            "triggered_by_studies": None,
            "submitted_by": "gazette_archaeologist_v2",
            "verification_status": "verified"
            if self.field_confidence.get("overall") == "HIGH"
            else "pending",
        }

    def _calculate_confidence(self) -> float:
        """Calculate numerical confidence score"""
        scores = {
            "HIGH": 0.95,
            "MODERATE": 0.75,
            "LOW": 0.50,
        }

        # Weighted confidence
        weights = {
            "act_number": 0.3,
            "long_title": 0.2,
            "sections": 0.3,
            "preamble": 0.1,
            "overall": 0.1,
        }

        total_score = 0.0
        for field_name, weight in weights.items():
            level = self.field_confidence.get(field_name, "LOW")
            total_score += scores.get(level, 0.5) * weight

        return round(min(0.98, total_score), 3)

    def _extract_objects(self) -> Dict[str, Any]:
        """Extract legislative purpose from long title"""
        if not self.long_title:
            return {}

        long_title_lower = self.long_title.lower()
        patterns = [
            r"(?:to provide for|to make provision for)\s*(.+?)(?:;|\.|$)",
            r"(?:to amend|to consolidate|to repeal)\s*(.+?)(?:;|\.|$)",
            r"(?:for the regulation of|to regulate)\s*(.+?)(?:;|\.|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, long_title_lower)
            if match:
                return {
                    "purpose": match.group(1).strip()[:500],
                    "extracted_from": "long_title",
                    "confidence": "HIGH",
                }

        # Fallback: first sentence
        first_sentence = re.split(r"[.;]", self.long_title)[0]
        return {
            "purpose": first_sentence.strip()[:500],
            "extracted_from": "first_sentence",
            "confidence": "LOW",
        }


# ------------ Main Harvester ------------
class GazetteArchaeologist:
    """
    Production gazette harvester with:
    - Connection pooling
    - Concurrent processing
    - Comprehensive error handling
    - Metrics tracking
    """

 codex/implement-database-connection-pooling-739ujd
    def __init__(self, year: int, max_workers: int, dry_run: bool):
        self.metrics = HarvestMetrics()
        self.session = self._create_session()
        self.storage = None
        self.db_pool = None
        self.year = year
        self.dry_run = dry_run

        if not self.dry_run:
            self.storage = self._init_storage()
            self.db_pool = self._init_db_pool()
            self._ensure_tables()


    def __init__(self):
        self.metrics = HarvestMetrics()
        self.session = self._create_session()
        self.storage = self._init_storage()
        self.db_pool = self._init_db_pool()
        self._ensure_tables()
 codex/add-improvements-to-meta-historian-agent
        self._lock = threading.Lock()

        # Rate limiting
        self._last_request_time = 0
        self._rate_limiter_lock = threading.Lock()

 codex/implement-database-connection-pooling-739ujd
        logger.info("Gazette Archaeologist initialized (dry_run=%s)", self.dry_run)

        logger.info("Gazette Archaeologist initialized")
 codex/add-improvements-to-meta-historian-agent

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=CONFIG["max_retries"],
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update(
            {
                "User-Agent": "Meta-Historian/2.0 (Academic Research; github.com/meta-historian)",
                "Accept": "application/pdf, text/html",
            }
        )

        return session

 codex/implement-database-connection-pooling-739ujd
    def _init_storage(self) -> Dict[str, Any]:
        """Initialize S3-compatible storage"""
        kwargs = {"region_name": CONFIG["s3_region"]}

    def _init_storage(self):
        """Initialize Alibaba Cloud OSS or AWS S3"""
        provider = CONFIG["storage_provider"]

        if provider == "alibaba" and ALIBABA_OSS_AVAILABLE:
            if not all([CONFIG["alibaba_access_key"], CONFIG["alibaba_secret_key"]]):
                raise ValueError("Alibaba credentials not configured")

            auth = oss2.Auth(CONFIG["alibaba_access_key"], CONFIG["alibaba_secret_key"])
            bucket = oss2.Bucket(auth, CONFIG["alibaba_endpoint"], CONFIG["bucket_name"])

            # Test connection
            try:
                bucket.get_bucket_info()
                logger.info(f"Connected to Alibaba Cloud OSS: {CONFIG['bucket_name']}")
            except Exception as exc:
                raise ConnectionError(f"Failed to connect to Alibaba OSS: {exc}") from exc

            return {"type": "alibaba", "client": bucket}

        # AWS S3 / MinIO
        import boto3

        kwargs = {"region_name": os.getenv("AWS_REGION", "us-east-1")}
 codex/add-improvements-to-meta-historian-agent

        if CONFIG["s3_endpoint"]:
            kwargs["endpoint_url"] = CONFIG["s3_endpoint"]

 codex/implement-database-connection-pooling-739ujd
        if CONFIG["s3_access_key"]:
            kwargs["aws_access_key_id"] = CONFIG["s3_access_key"]
            kwargs["aws_secret_access_key"] = CONFIG["s3_secret_key"]

        if CONFIG["aws_access_key"]:
            kwargs["aws_access_key_id"] = CONFIG["aws_access_key"]
            kwargs["aws_secret_access_key"] = CONFIG["aws_secret_key"]
 codex/add-improvements-to-meta-historian-agent

        client = boto3.client("s3", **kwargs)

        # Test connection
        try:
            client.head_bucket(Bucket=CONFIG["bucket_name"])
 codex/implement-database-connection-pooling-739ujd
            logger.info("Connected to S3: %s", CONFIG["bucket_name"])
        except Exception as exc:
            raise ConnectionError(f"Failed to connect to S3: {exc}") from exc

        return {"client": client}

            logger.info(f"Connected to S3: {CONFIG['bucket_name']}")
        except Exception as exc:
            raise ConnectionError(f"Failed to connect to S3: {exc}") from exc

        return {"type": "s3", "client": client}
 codex/add-improvements-to-meta-historian-agent

    def _init_db_pool(self) -> pool.ThreadedConnectionPool:
        """Initialize PostgreSQL connection pool with health check"""
        max_retries = 5

        for attempt in range(max_retries):
            try:
                conn_pool = psycopg2.pool.ThreadedConnectionPool(
                    CONFIG["db_pool_min"],
                    CONFIG["db_pool_max"],
                    CONFIG["postgres_dsn"],
                    connect_timeout=CONFIG["connection_timeout"],
                )

                # Test connection
                with self._get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")

                logger.info(
                    "Database pool initialized (%s-%s connections)",
                    CONFIG["db_pool_min"],
                    CONFIG["db_pool_max"],
                )
                return conn_pool

            except Exception as exc:
                logger.warning(
                    "DB pool init attempt %s/%s failed: %s",
                    attempt + 1,
                    max_retries,
                    exc,
                )
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
                else:
                    raise RuntimeError(
                        "Failed to initialize database pool after "
                        f"{max_retries} attempts"
                    ) from exc

        raise RuntimeError("Failed to initialize database pool")

    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections from pool"""
 codex/implement-database-connection-pooling-739ujd
        if not self.db_pool:
            raise RuntimeError("Database pool not initialized")

 codex/add-improvements-to-meta-historian-agent
        conn = None
        try:
            conn = self.db_pool.getconn()
            conn.autocommit = False
            yield conn
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.db_pool.putconn(conn)

 codex/implement-database-connection-pooling-739ujd
    def _ensure_tables(self) -> None:
        """Ensure ingestion_manifest and statutes tables exist"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:

    def _ensure_tables(self):
        """Ensure ingestion_manifest and statutes tables exist"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                # Ingestion tracking for idempotency
 codex/add-improvements-to-meta-historian-agent
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ingestion_manifest (
                        gazette_id TEXT PRIMARY KEY,
                        year INTEGER NOT NULL,
                        number INTEGER NOT NULL,
                        oss_key TEXT NOT NULL,
                        pdf_sha256 TEXT NOT NULL,
                        source_url TEXT,
                        processed_at TIMESTAMP WITH TIME ZONE,
                        status TEXT CHECK (status IN ('pending', 'processing', 'done', 'failed')),
                        error_text TEXT,
                        acts_extracted INTEGER DEFAULT 0,
                        retry_count INTEGER DEFAULT 0
                    );

                    CREATE INDEX IF NOT EXISTS idx_manifest_status ON ingestion_manifest(status);
                    CREATE INDEX IF NOT EXISTS idx_manifest_year ON ingestion_manifest(year);
                    CREATE INDEX IF NOT EXISTS idx_manifest_retry ON ingestion_manifest(retry_count)
                        WHERE status = 'failed';
                """
                )

 codex/implement-database-connection-pooling-739ujd
                cur.execute(
                    """
                    ALTER TABLE ingestion_manifest
                        ADD COLUMN IF NOT EXISTS year INTEGER,
                        ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
                        ADD COLUMN IF NOT EXISTS acts_extracted INTEGER DEFAULT 0;
                """
                )


                # Ensure statutes table has required fields
 codex/add-improvements-to-meta-historian-agent
                cur.execute(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'statutes') THEN
                            CREATE TABLE statutes (
                                statute_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                                act_number VARCHAR(50) UNIQUE,
                                short_title VARCHAR(255) NOT NULL,
                                long_title TEXT,
                                assent_date DATE,
                                commencement_date DATE,
                                repeal_date DATE,
                                era VARCHAR(20),
                                preamble TEXT,
                                objects_clause JSONB,
                                full_text TEXT,
                                sections JSONB,
                                confidence_level VARCHAR(20),
                                confidence_probability DECIMAL(4,3),
                                is_anchor BOOLEAN DEFAULT FALSE,
                                anchor_type VARCHAR(20),
                                source_gazette_id VARCHAR(100),
                                source_url TEXT,
 codex/implement-database-connection-pooling-739ujd
                                source_metadata JSONB,

 codex/add-improvements-to-meta-historian-agent
                                submitted_by VARCHAR(100),
                                verification_status VARCHAR(20),
                                transaction_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                                valid_from DATE,
                                valid_to DATE,
                                belief_state VARCHAR(50) DEFAULT 'current',
                                superseded_by UUID REFERENCES statutes(statute_id)
                            );

                            CREATE INDEX idx_statutes_act_number ON statutes(act_number);
                            CREATE INDEX idx_statutes_era ON statutes(era);
                            CREATE INDEX idx_statutes_assent_date ON statutes(assent_date);
                        END IF;
                    END
                    $$;
                """
                )

 codex/implement-database-connection-pooling-739ujd
                cur.execute(
                    """
                    ALTER TABLE statutes
                        ADD COLUMN IF NOT EXISTS confidence_probability DECIMAL(4,3),
                        ADD COLUMN IF NOT EXISTS verification_status VARCHAR(20),
                        ADD COLUMN IF NOT EXISTS source_metadata JSONB;
                """
                )

                conn.commit()

    def _rate_limit(self) -> None:

                conn.commit()

    def _rate_limit(self):
 codex/add-improvements-to-meta-historian-agent
        """Thread-safe rate limiting"""
        with self._rate_limiter_lock:
            elapsed = time.time() - self._last_request_time
            if elapsed < CONFIG["rate_limit_seconds"]:
                time.sleep(CONFIG["rate_limit_seconds"] - elapsed)
            self._last_request_time = time.time()

    def _manifest_exists(self, gazette_id: str) -> bool:
        """Check if gazette already processed successfully"""
 codex/implement-database-connection-pooling-739ujd
        if self.dry_run:
            return False

 codex/add-improvements-to-meta-historian-agent
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM ingestion_manifest WHERE gazette_id = %s AND status = 'done'",
                    (gazette_id,),
                )
                return cur.fetchone() is not None

    def _update_manifest(
        self,
        gazette_id: str,
        year: int,
        number: int,
        oss_key: str,
        sha256: str,
        url: str,
        status: str,
        error: Optional[str] = None,
        acts_count: int = 0,
 codex/implement-database-connection-pooling-739ujd
    ) -> None:
        """Upsert manifest record"""
        if self.dry_run:
            return

    ):
        """Upsert manifest record"""
 codex/add-improvements-to-meta-historian-agent
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ingestion_manifest
                    (gazette_id, year, number, oss_key, pdf_sha256, source_url,
                     processed_at, status, error_text, acts_extracted, retry_count)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, 0)
                    ON CONFLICT (gazette_id)
                    DO UPDATE SET
                        processed_at = CURRENT_TIMESTAMP,
                        status = EXCLUDED.status,
                        error_text = EXCLUDED.error_text,
                        acts_extracted = EXCLUDED.acts_extracted,
                        retry_count = ingestion_manifest.retry_count +
                            CASE WHEN EXCLUDED.status = 'failed' THEN 1 ELSE 0 END
                """,
                    (gazette_id, year, number, oss_key, sha256, url, status, error, acts_count),
                )

                conn.commit()

 codex/implement-database-connection-pooling-739ujd
    def harvest_year(self) -> None:
        """Main entry: Harvest all gazettes for target year with concurrent processing"""
        year = self.year

        logger.info("🚀 Starting archaeological excavation of year %s", year)
        logger.info(
            "Configuration: %s workers, %ss rate limit, dry_run=%s",
            CONFIG["max_workers"],
            CONFIG["rate_limit_seconds"],
            self.dry_run,

    def harvest_year(self, year: Optional[int] = None):
        """
        Main entry: Harvest all gazettes for target year with concurrent processing
        """
        if year is None:
            year = CONFIG["target_year"]

        logger.info("🚀 Starting archaeological excavation of year %s", year)
        logger.info(
            "Configuration: %s workers, %ss rate limit",
            CONFIG["max_workers"],
            CONFIG["rate_limit_seconds"],
 codex/add-improvements-to-meta-historian-agent
        )

        # Health checks
        if not self._health_check():
            raise RuntimeError("Health check failed, aborting harvest")

        # Discover gazettes
        gazette_numbers = self._discover_gazettes(year)
        self.metrics.gazettes_discovered = len(gazette_numbers)
        logger.info("📚 Discovered %s gazettes for %s", len(gazette_numbers), year)

        # Process concurrently with thread pool
        with ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
            futures = {
                executor.submit(self._process_gazette, year, num): num
                for num in gazette_numbers
            }

            for future in as_completed(futures):
                num = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    logger.exception("💥 Fatal error processing %s/%s: %s", year, num, exc)
                    with self._lock:
                        self.metrics.gazettes_failed += 1

        self.metrics.end_time = datetime.now()

        # Final summary
        summary = self.metrics.summary()
        logger.info("✅ Harvest complete for %s", year)
        logger.info("Summary: %s", json.dumps(summary, indent=2))

        # Save metrics
        self._save_metrics(year, summary)
 codex/implement-database-connection-pooling-739ujd
        self._write_metrics_file(year, summary)

 codex/add-improvements-to-meta-historian-agent

    def _health_check(self) -> bool:
        """Verify all systems operational before starting"""
        logger.info("Running health checks...")

 codex/implement-database-connection-pooling-739ujd
        checks = {"database": True, "storage": True, "network": False}

        if not self.dry_run:
            checks["database"] = False
            checks["storage"] = False

        # Database check
        if not self.dry_run:
            try:
                with self._get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM ingestion_manifest")
                        count = cur.fetchone()[0]
                        logger.info("✓ Database: %s manifests in database", count)
                        checks["database"] = True
            except Exception as exc:
                logger.error("✗ Database check failed: %s", exc)

        # Storage check
        if not self.dry_run:
            try:
                client = self.storage["client"]
                client.head_bucket(Bucket=CONFIG["bucket_name"])
                logger.info("✓ Storage: Connected to %s", CONFIG["bucket_name"])
                checks["storage"] = True
            except Exception as exc:
                logger.error("✗ Storage check failed: %s", exc)

        checks = {"database": False, "storage": False, "network": False}

        # Database check
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM ingestion_manifest")
                    count = cur.fetchone()[0]
                    logger.info("✓ Database: %s manifests in database", count)
                    checks["database"] = True
        except Exception as exc:
            logger.error("✗ Database check failed: %s", exc)

        # Storage check
        try:
            if self.storage["type"] == "alibaba":
                bucket = self.storage["client"]
                bucket.get_bucket_info()
            else:
                client = self.storage["client"]
                client.head_bucket(Bucket=CONFIG["bucket_name"])

            logger.info("✓ Storage: Connected to %s", self.storage["type"])
            checks["storage"] = True
        except Exception as exc:
            logger.error("✗ Storage check failed: %s", exc)
 codex/add-improvements-to-meta-historian-agent

        # Network check
        try:
            response = self.session.head(CONFIG["base_url"], timeout=10)
            logger.info("✓ Network: Gazette source accessible (status %s)", response.status_code)
            checks["network"] = True
        except Exception as exc:
            logger.error("✗ Network check failed: %s", exc)

        all_ok = all(checks.values())
        if all_ok:
            logger.info("✓ All health checks passed")
        else:
            logger.error("✗ Health checks failed: %s", checks)

        return all_ok

    def _discover_gazettes(self, year: int) -> List[int]:
        """Discover available gazette numbers by probing"""
        found = []
        consecutive_404 = 0
        max_probe = CONFIG["max_gazette_number"]

        logger.info("Discovering gazettes for %s (max %s)...", year, max_probe)

        for n in range(1, max_probe + 1):
            url = f"{CONFIG['base_url']}/{year}/{n}.pdf"

            try:
                self._rate_limit()
                resp = self.session.head(url, allow_redirects=True, timeout=10)

                if resp.status_code == 200:
                    found.append(n)
                    consecutive_404 = 0
                    logger.debug("Found: %s/%s", year, n)
                else:
                    consecutive_404 += 1

            except requests.RequestException as exc:
                logger.debug("Request failed for %s/%s: %s", year, n, exc)
                consecutive_404 += 1

            # Stop after too many consecutive misses
            if consecutive_404 >= CONFIG["consecutive_404_threshold"]:
                logger.info(
                    "Stopping discovery after %s consecutive misses at gazette %s",
                    consecutive_404,
                    n,
                )
                break

            # Progress indicator
            if n % 20 == 0:
                logger.info("Discovery progress: %s/%s checked, %s found", n, max_probe, len(found))

        return sorted(found)

 codex/implement-database-connection-pooling-739ujd
    def _upload_to_storage(self, key: str, data: bytes, metadata: Dict[str, str]) -> bool:
        """Upload to S3-compatible storage with error handling"""
        if self.dry_run:
            logger.info("Dry run: skipping upload for %s", key)
            return True
        try:
            self.storage["client"].put_object(
                Bucket=CONFIG["bucket_name"],
                Key=key,
                Body=data,
                ContentType="application/pdf",
                Metadata={k: str(v)[:1024] for k, v in metadata.items()},
            )

    def _upload_to_storage(self, key: str, data: bytes, metadata: Dict) -> bool:
        """Upload to Alibaba OSS or S3 with error handling"""
        try:
            if self.storage["type"] == "alibaba":
                bucket = self.storage["client"]
                headers = {f"x-oss-meta-{k}": str(v)[:1024] for k, v in metadata.items()}
                bucket.put_object(key, data, headers=headers)
            else:
                # S3/MinIO
                self.storage["client"].put_object(
                    Bucket=CONFIG["bucket_name"],
                    Key=key,
                    Body=data,
                    ContentType="application/pdf",
                    Metadata={k: str(v)[:1024] for k, v in metadata.items()},
                )
 codex/add-improvements-to-meta-historian-agent

            logger.debug("Uploaded to storage: %s", key)
            return True

        except Exception as exc:
            logger.error("Storage upload failed for %s: %s", key, exc)
            with self._lock:
                self.metrics.storage_errors += 1
            return False

 codex/implement-database-connection-pooling-739ujd
    def _process_gazette(self, year: int, gazette_num: int) -> None:

    def _process_gazette(self, year: int, gazette_num: int):
 codex/add-improvements-to-meta-historian-agent
        """Process single gazette: download, store, parse, ingest"""
        url = f"{CONFIG['base_url']}/{year}/{gazette_num}.pdf"
        gazette_id = f"ZA_Gazette_{year}_{gazette_num:04d}"
        oss_key = f"gazettes/{year}/{gazette_num:04d}.pdf"

        # Idempotency check
        if self._manifest_exists(gazette_id):
            logger.info("⏩ Skipping %s (already processed)", gazette_id)
            with self._lock:
                self.metrics.gazettes_skipped += 1
            return

        logger.info("📥 Processing %s", gazette_id)
        self._update_manifest(gazette_id, year, gazette_num, oss_key, "", url, "processing")

        # Download
        try:
            self._rate_limit()
            resp = self.session.get(url, timeout=CONFIG["request_timeout"])
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("❌ Download failed for %s: %s", gazette_id, exc)
            self._update_manifest(
                gazette_id,
                year,
                gazette_num,
                oss_key,
                "",
                url,
                "failed",
                str(exc),
            )
            with self._lock:
                self.metrics.download_errors += 1
                self.metrics.gazettes_failed += 1
            return

        pdf_bytes = resp.content

        # Validate PDF
        if not pdf_bytes.startswith(b"%PDF"):
            error_msg = "Invalid PDF magic bytes"
            logger.error("❌ %s for %s", error_msg, gazette_id)
            self._update_manifest(
                gazette_id,
                year,
                gazette_num,
                oss_key,
                "",
                url,
                "failed",
                error_msg,
            )
            with self._lock:
                self.metrics.download_errors += 1
                self.metrics.gazettes_failed += 1
            return

        # Checksum
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()

 codex/implement-database-connection-pooling-739ujd
        # Upload to S3

        # Upload to OSS/S3
 codex/add-improvements-to-meta-historian-agent
        metadata = {
            "gazette-id": gazette_id,
            "source-url": url,
            "harvest-date": datetime.now().isoformat(),
            "content-sha256": sha256,
            "year": str(year),
            "number": str(gazette_num),
        }

        if not self._upload_to_storage(oss_key, pdf_bytes, metadata):
            self._update_manifest(
                gazette_id,
                year,
                gazette_num,
                oss_key,
                sha256,
                url,
                "failed",
                "Upload failed",
            )
            with self._lock:
                self.metrics.gazettes_failed += 1
            return

        # Parse Acts
        try:
            acts = self._extract_acts(pdf_bytes, year, gazette_num)
            logger.info("📜 Extracted %s acts from %s", len(acts), gazette_id)

            with self._lock:
                self.metrics.acts_extracted += len(acts)

            # Validate and enrich acts
            valid_acts = []
            for act in acts:
                act.source_gazette_id = gazette_id
                act.pdf_oss_key = oss_key
                act.pdf_sha256 = sha256
                act.source_url = url

                is_valid, errors = act.validate()
                if is_valid:
                    valid_acts.append(act)
                else:
                    logger.warning("Invalid act %s: %s", act.act_number, errors)

            # Batch store acts
            stored_count, updated_count = self._batch_store_acts(valid_acts)

            with self._lock:
                self.metrics.acts_stored += stored_count
                self.metrics.acts_updated += updated_count
                self.metrics.gazettes_processed += 1

            self._update_manifest(
                gazette_id,
                year,
                gazette_num,
                oss_key,
                sha256,
                url,
                "done",
                None,
                len(valid_acts),
            )

            logger.info(
                "✅ Stored %s new + %s updated acts from %s",
                stored_count,
                updated_count,
                gazette_id,
            )

        except Exception as exc:
            logger.exception("💥 Parsing failed for %s: %s", gazette_id, exc)
            self._update_manifest(
                gazette_id,
                year,
                gazette_num,
                oss_key,
                sha256,
                url,
                "failed",
                str(exc),
            )
            with self._lock:
                self.metrics.parse_errors += 1
                self.metrics.gazettes_failed += 1

    def _extract_acts(self, pdf_bytes: bytes, year: int, gazette_num: int) -> List[ParsedAct]:
        """Extract individual Acts from PDF with improved error handling"""
        acts = []
        temp_path = None

        try:
            # Write to temp file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_bytes)
                temp_path = tmp.name

            # Extract with pdfplumber
            with pdfplumber.open(temp_path) as pdf:
                # Extract text with page markers
                pages_text = []
                for i, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text() or ""
                        pages_text.append(f"---PAGE {i + 1}---\n{text}")
                    except Exception as exc:
                        logger.warning("Failed to extract page %s: %s", i + 1, exc)
                        pages_text.append(f"---PAGE {i + 1}---\n[EXTRACTION FAILED]")

                full_text = "\n".join(pages_text)

                # Split into Act blocks
                act_blocks = self._split_into_acts(full_text, year)
                logger.debug("Found %s act blocks", len(act_blocks))

                # Parse each block
                for i, block in enumerate(act_blocks):
                    try:
                        act = self._parse_act_block(block, year, gazette_num)
                        if act:
                            acts.append(act)
                    except Exception as exc:
                        logger.warning("Failed to parse act block %s: %s", i + 1, exc)
                        continue

        except Exception as exc:
            logger.error("PDF extraction failed: %s", exc)
            raise

        finally:
            # Cleanup temp file
            if temp_path:
                try:
                    os.unlink(temp_path)
                except Exception as exc:
                    logger.warning("Failed to delete temp file %s: %s", temp_path, exc)

        return acts

    def _split_into_acts(self, text: str, year: int) -> List[str]:
        """Split gazette text into individual Act blocks using regex"""
        # Pattern matches: "ACT No. 41 of 1950", "Act 30 of 1950", "No. 41/1950"
        header_pattern = re.compile(
            r"(?:^|\n)(?:(?:ACT|Act)\s*[Nn]?[Oo]?\.?\s*(\d+)\s*(?:of|,|/)\s*(\d{4})|"
            r"No\.?\s*(\d+)\s*/\s*(\d{4}))",
            re.IGNORECASE,
        )

        matches = list(header_pattern.finditer(text))
        blocks = []

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block = text[start:end].strip()

            # Validate: must contain year and reasonable length
            if len(block) > CONFIG["min_act_length"] and str(year) in block[:200]:
                blocks.append(block)
            elif len(block) > 1000:  # Long blocks might be valid even without year in preview
                blocks.append(block)

        return blocks

    def _parse_act_block(self, block: str, year: int, gazette_num: int) -> Optional[ParsedAct]:
        """Parse single Act block into structured data with improved extraction"""
        # Normalize whitespace
        text = re.sub(r"[\u00A0\u2002\u2003]", " ", block)
        text = re.sub(r"\s+", " ", text)
        lines = text.split("\n")

        if not lines:
            return None

        # Extract Act Number
        act_num = None
        first_lines = " ".join(lines[:5])
        match = re.search(
            r"(?:Act|ACT|No\.?)\s*\.?\s*(\d+)\s*(?:of|,|/)\s*(\d{4})",
            first_lines,
            re.IGNORECASE,
        )
        if match:
            act_num = match.group(1)
            act_year = match.group(2)
        else:
            return None

        act_number = f"Act {act_num} of {act_year}"

        # Extract Long Title
        long_title = ""
        enacting_match = re.search(
            r"(?:BE IT ENACTED|To provide for|To amend|To consolidate|To repeal).*?(?=\n\s*1\.|\n\s*ARRANGEMENT|\n\s*WHEREAS|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if enacting_match:
            long_title = enacting_match.group(0).strip()[:1000]

        # Extract Preamble
        preamble = ""
        whereas_match = re.search(
            r"(WHEREAS|PREAMBLE).*?(?=\n\s*BE IT ENACTED|\n\s*NOW THEREFORE|\n\s*1\.)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if whereas_match:
            preamble = whereas_match.group(0).strip()[:5000]

        # Extract Sections with improved regex
        sections = {}
        sec_pattern = re.compile(
            r"\n\s*(\d+[A-Z]?)\.?\s+([^\n]{10,500}?)(?=\n\s*\d+[A-Z]?\.?\s+|\Z)",
            re.DOTALL,
        )

        for match in sec_pattern.finditer(text):
            sec_num = match.group(1)
            sec_text = match.group(2).strip()

            # Extract section title (first line or sentence)
            title_match = re.match(r"^([^\.\n]{5,200})", sec_text)
            title = title_match.group(1) if title_match else f"Section {sec_num}"

            sections[f"s{sec_num}"] = {
                "title": title[:200],
                "text": sec_text[:2000],
            }

        # Extract assent date
        assent_date = date(year, 1, 1)
        date_patterns = [
            r"assented to[^\d]*(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s*,?\s*(\d{4})",
            r"(\d{1,2})(?:st|nd|rd|th)?\s+day\s+of\s+(\w+)\s*,?\s*(\d{4})",
        ]

        for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE)
            if date_match:
                try:
                    from dateutil import parser

                    date_str = f"{date_match.group(1)} {date_match.group(2)} {date_match.group(3)}"
                    assent_date = parser.parse(date_str).date()
                    break
                except Exception as exc:
                    logger.debug("Date parsing failed: %s", exc)

        # Determine era
        if 1948 <= year < 1994:
            era = "apartheid_1948"
        elif year >= 1994:
            era = "democratic_1994"
        else:
            era = "union_1910"

        # Confidence scoring
        field_confidence = {
            "act_number": "HIGH" if act_num else "LOW",
            "long_title": "HIGH" if len(long_title) > 50 else "LOW",
            "preamble": "HIGH" if len(preamble) > 100 else "MODERATE",
            "sections": "HIGH" if len(sections) >= CONFIG["min_section_count"] else "LOW",
            "overall": "HIGH"
            if all([act_num, len(long_title) > 50, len(sections) >= CONFIG["min_section_count"]])
            else "MODERATE",
        }

        # Derive short title
        short_title = self._derive_short_title(long_title, text, act_num, year)

        return ParsedAct(
            act_number=act_number,
            short_title=short_title,
            long_title=long_title,
            assent_date=assent_date,
            commencement_date=None,
            preamble=preamble,
            sections=sections,
            full_text=text[: CONFIG["max_full_text_chars"]],
            era=era,
            page_range=(0, 0),
            source_gazette_id="",
            source_url="",
            pdf_oss_key="",
            pdf_sha256="",
            field_confidence=field_confidence,
        )

    def _derive_short_title(self, long_title: str, full_text: str, act_num: str, year: int) -> str:
        """Derive short title from content with better heuristics"""
        long_title_lower = (long_title or "").lower()
        full_text_lower = full_text[:3000].lower()

        # Known Apartheid-era acts
        known_acts = {
            "group areas": "Group Areas Act",
            "population registration": "Population Registration Act",
            "suppression of communism": "Suppression of Communism Act",
            "unlawful organisations": "Unlawful Organisations Act",
            "native land": "Native Land Act",
            "mixed marriages": "Prohibition of Mixed Marriages Act",
            "immorality": "Immorality Amendment Act",
            "pass laws": "Pass Laws Act",
            "bantu education": "Bantu Education Act",
            "separate amenities": "Reservation of Separate Amenities Act",
            "bantu authorities": "Bantu Authorities Act",
        }

        for key, title in known_acts.items():
            if key in long_title_lower or key in full_text_lower:
                return title

        # Extract from "Short title" section
        short_match = re.search(
            r"(?:short title|this act may be cited).*?(?:as\s+)?[\"\']?([^\"\'\n.]{5,100})[\"\']?",
            full_text,
            re.IGNORECASE,
        )
        if short_match:
            return short_match.group(1).strip()[:100]

        # Extract from long title keywords
        if "to amend" in long_title_lower:
            target_match = re.search(r"to amend\s+(?:the\s+)?([^,;.]{5,80})", long_title_lower)
            if target_match:
                return f"{target_match.group(1).strip()} Amendment Act"

        # Fallback: generic title
        return f"Act No. {act_num} of {year}"

    def _batch_store_acts(self, acts: List[ParsedAct]) -> Tuple[int, int]:
        """
        Store multiple acts efficiently using batch operations

        Returns:
            Tuple of (stored_count, updated_count)
        """
 codex/implement-database-connection-pooling-739ujd
        if not acts or self.dry_run:

        if not acts:
 codex/add-improvements-to-meta-historian-agent
            return 0, 0

        stored = 0
        updated = 0

        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    for act in acts:
                        record = act.to_db_record()

                        # Check if exists
                        cur.execute(
                            "SELECT statute_id, transaction_time FROM statutes WHERE act_number = %s",
                            (act.act_number,),
                        )
                        existing = cur.fetchone()

                        if existing:
                            # Update existing
                            cur.execute(
                                """
                                UPDATE statutes
                                SET belief_state = %s,
                                    transaction_time = CURRENT_TIMESTAMP,
                                    long_title = COALESCE(%s, long_title),
                                    preamble = COALESCE(%s, preamble),
                                    sections = COALESCE(%s::jsonb, sections),
                                    full_text = COALESCE(%s, full_text),
 codex/implement-database-connection-pooling-739ujd
                                    confidence_probability = GREATEST(confidence_probability, %s),
                                    verification_status = COALESCE(%s, verification_status),
                                    source_metadata = COALESCE(%s::jsonb, source_metadata)

                                    confidence_probability = GREATEST(confidence_probability, %s)
 codex/add-improvements-to-meta-historian-agent
                                WHERE act_number = %s
                            """,
                                (
                                    f"revised_{datetime.now().isoformat()}",
                                    record["long_title"],
                                    record["preamble"],
                                    Json(record["sections"]),
                                    record["full_text"],
                                    record["confidence_probability"],
 codex/implement-database-connection-pooling-739ujd
                                    record["verification_status"],
                                    Json(record["source_metadata"]),

 codex/add-improvements-to-meta-historian-agent
                                    act.act_number,
                                ),
                            )
                            updated += 1
                        else:
                            # Insert new
                            columns = ", ".join(record.keys())
                            placeholders = ", ".join(["%s"] * len(record))

                            cur.execute(
                                f"""
                                INSERT INTO statutes ({columns})
                                VALUES ({placeholders})
                            """,
                                list(record.values()),
                            )
                            stored += 1

                conn.commit()

        except Exception as exc:
            logger.error("Batch store failed: %s", exc)
            with self._lock:
                self.metrics.db_errors += 1
            raise

        return stored, updated

 codex/implement-database-connection-pooling-739ujd
    def _save_metrics(self, year: int, summary: Dict[str, Any]) -> None:
        """Save harvest metrics to database"""
        if self.dry_run:
            return

    def _save_metrics(self, year: int, summary: Dict):
        """Save harvest metrics to database"""
 codex/add-improvements-to-meta-historian-agent
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS harvest_metrics (
                            metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                            harvest_year INTEGER NOT NULL,
                            harvest_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            duration_seconds NUMERIC,
                            gazettes_discovered INTEGER,
                            gazettes_processed INTEGER,
                            gazettes_failed INTEGER,
                            acts_extracted INTEGER,
                            acts_stored INTEGER,
                            error_count INTEGER,
                            summary JSONB
                        )
                    """
                    )

                    cur.execute(
                        """
                        INSERT INTO harvest_metrics
                        (harvest_year, duration_seconds, gazettes_discovered, gazettes_processed,
                         gazettes_failed, acts_extracted, acts_stored, error_count, summary)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                        (
                            year,
                            summary["duration_seconds"],
                            summary["gazettes"]["discovered"],
                            summary["gazettes"]["processed"],
                            summary["gazettes"]["failed"],
                            summary["acts"]["extracted"],
                            summary["acts"]["stored"],
                            summary["errors"]["total"],
                            Json(summary),
                        ),
                    )

                    conn.commit()
                    logger.info("Metrics saved to database")

        except Exception as exc:
            logger.error("Failed to save metrics: %s", exc)

 codex/implement-database-connection-pooling-739ujd
    def _write_metrics_file(self, year: int, summary: Dict[str, Any]) -> None:
        """Write metrics summary to harvest_metrics.json"""
        payload = {
            "year": year,
            "summary": summary,
        }
        try:
            with open("harvest_metrics.json", "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
        except Exception as exc:
            logger.error("Failed to write harvest_metrics.json: %s", exc)

    def close(self) -> None:
        """Clean up resources"""
        try:
            if self.db_pool:
                self.db_pool.closeall()
                logger.info("Database pool closed")

            if self.session:

    def close(self):
        """Clean up resources"""
        try:
            if hasattr(self, "db_pool"):
                self.db_pool.closeall()
                logger.info("Database pool closed")

            if hasattr(self, "session"):
 codex/add-improvements-to-meta-historian-agent
                self.session.close()
                logger.info("HTTP session closed")

        except Exception as exc:
            logger.error("Error during cleanup: %s", exc)


# ------------ CLI Entry Point ------------
 codex/implement-database-connection-pooling-739ujd
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Meta-Historian Gazette Harvester")
    parser.add_argument("--year", type=int, default=CONFIG["target_year"], help="Target year to harvest")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=CONFIG["max_workers"],
        help="Concurrent workers for download/processing",
    )
    parser.add_argument(
        "--dry-run",
        default="false",
        help="Dry run mode (no uploads or DB writes). true/false",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point with graceful error handling"""
    args = parse_args()
    CONFIG["target_year"] = args.year
    CONFIG["max_workers"] = args.max_workers
    dry_run = str(args.dry_run).lower() in {"1", "true", "yes"}

    setup_logging(args.year)

    archaeologist = None

    try:
        archaeologist = GazetteArchaeologist(args.year, args.max_workers, dry_run)

def main():
    """Main entry point with graceful error handling"""
    archaeologist = None

    try:
        archaeologist = GazetteArchaeologist()
 codex/add-improvements-to-meta-historian-agent
        archaeologist.harvest_year()
        exit_code = 0

    except KeyboardInterrupt:
        logger.warning("Harvest interrupted by user")
        exit_code = 130

    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
        exit_code = 1

    finally:
        if archaeologist:
            archaeologist.close()

    return exit_code


if __name__ == "__main__":
 codex/implement-database-connection-pooling-739ujd
    raise SystemExit(main())

    import sys

    sys.exit(main())
 codex/add-improvements-to-meta-historian-agent
