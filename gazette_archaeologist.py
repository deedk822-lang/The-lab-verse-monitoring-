#!/usr/bin/env python3
"""
gazette_archaeologist.py
Meta-Historian: Production Gazette Harvester for South African Government Gazettes
Target: 1950 (Apartheid Legislative Cascade)
Deployment: GitHub Actions + Alibaba Cloud OSS + PostgreSQL

Version: 2.0 (Production-Ready)
All critical fixes applied:
- Single __init__/main entry point with CLI args
- Fixed connection pool initialization
- UUID extension creation
- Proper whitespace normalization
- Dry-run support
- Fixed SQL UPDATE statement
- Comprehensive error handling
"""

import os
import re
import json
import logging
import tempfile
import hashlib
import time
import argparse
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import threading

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pdfplumber
import psycopg2
from psycopg2 import pool
from psycopg2.extras import Json, RealDictCursor

# Alibaba Cloud OSS support
try:
    import oss2
    ALIBABA_OSS_AVAILABLE = True
except ImportError:
    ALIBABA_OSS_AVAILABLE = False
    logging.warning("oss2 not available, falling back to boto3")

# ------------ Logging Setup (Single Implementation) ------------
def setup_logging(target_year: int):
    """Configure structured logging - called once at startup"""
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"

    # File handler
    file_handler = logging.FileHandler(f"harvester_{target_year}.log")
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
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('pdfplumber').setLevel(logging.WARNING)

# ------------ Configuration ------------
def get_config():
    """Get configuration from environment"""
    return {
        "postgres_dsn": os.getenv("DATABASE_URL", "postgresql://historian:pass@localhost:5432/meta_historian"),

        # Connection pooling
        "db_pool_min": int(os.getenv("DB_POOL_MIN", "2")),
        "db_pool_max": int(os.getenv("DB_POOL_MAX", "10")),

        # Storage: 'alibaba' or 'aws'
        "storage_provider": os.getenv("STORAGE_PROVIDER", "alibaba"),
        "bucket_name": os.getenv("BUCKET_NAME", "meta-historian-gazettes"),

        # Alibaba Cloud OSS settings
        "alibaba_access_key": os.getenv("ALIBABA_ACCESS_KEY_ID"),
        "alibaba_secret_key": os.getenv("ALIBABA_ACCESS_KEY_SECRET"),
        "alibaba_endpoint": os.getenv("ALIBABA_ENDPOINT", "https://oss-cn-shanghai.aliyuncs.com"),

        # AWS S3 settings (fallback)
        "aws_access_key": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "s3_endpoint": os.getenv("S3_ENDPOINT"),
        "aws_region": os.getenv("AWS_REGION", "us-east-1"),

        # Rate limiting and concurrency
        "rate_limit_seconds": float(os.getenv("RATE_LIMIT", "2.0")),
        "max_retries": int(os.getenv("MAX_RETRIES", "3")),

        # Processing limits
        "max_full_text_chars": 50000,
        "max_gazette_number": 200,
        "consecutive_404_threshold": 15,
        "batch_size": 10,

        # Timeouts
        "request_timeout": 30,
        "connection_timeout": 10,

        # Base URL
        "base_url": "https://gazettes.africa/gazettes/za",

        # Confidence scoring
        "confidence_level": "VERY_HIGH",
        "min_act_length": 300,
        "min_section_count": 1,
    }

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
                "success_rate": round(self.gazettes_processed / max(1, self.gazettes_discovered) * 100, 2)
            },
            "acts": {
                "extracted": self.acts_extracted,
                "stored": self.acts_stored,
                "updated": self.acts_updated,
                "success_rate": round(self.acts_stored / max(1, self.acts_extracted) * 100, 2)
            },
            "errors": {
                "download": self.download_errors,
                "parse": self.parse_errors,
                "storage": self.storage_errors,
                "database": self.db_errors,
                "total": self.download_errors + self.parse_errors + self.storage_errors + self.db_errors
            }
        }

# ------------ Data Models ------------
@dataclass
class ParsedAct:
    """Structured extraction matching the Meta-Historian statute schema"""
    act_number: str
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

        config = get_config()
        if len(self.full_text) < config["min_act_length"]:
            errors.append(f"Full text too short ({len(self.full_text)} chars)")

        if len(self.sections) < config["min_section_count"]:
            errors.append(f"Insufficient sections ({len(self.sections)})")

        if not self.assent_date:
            errors.append("Missing assent_date")

        return len(errors) == 0, errors

    def to_db_record(self) -> Dict[str, Any]:
        """Convert to database insertion format"""
        config = get_config()
        return {
            "act_number": self.act_number,
            "short_title": self.short_title[:255],
            "long_title": self.long_title[:1000] if self.long_title else None,
            "assent_date": self.assent_date,
            "commencement_date": self.commencement_date,
            "era": self.era,
            "preamble": self.preamble[:5000] if self.preamble else None,
            "objects_clause": Json(self._extract_objects()),
            "full_text": self.full_text[:config["max_full_text_chars"]],
            "sections": Json(self.sections),
            "confidence_level": config["confidence_level"],
            "confidence_probability": self._calculate_confidence(),
            "is_anchor": True,
            "anchor_type": "legislative",
            "source_gazette_id": self.source_gazette_id,
            "source_url": self.source_url,
            "semantic_embedding": None,
            "triggered_by_events": None,
            "triggered_by_studies": None,
            "submitted_by": "gazette_archaeologist_v2",
            "verification_status": "verified" if self.field_confidence.get("overall") == "HIGH" else "pending"
        }

    def _calculate_confidence(self) -> float:
        """Calculate numerical confidence score"""
        scores = {"HIGH": 0.95, "MODERATE": 0.75, "LOW": 0.50}
        weights = {
            "act_number": 0.3,
            "long_title": 0.2,
            "sections": 0.3,
            "preamble": 0.1,
            "overall": 0.1
        }

        total_score = 0.0
        for field, weight in weights.items():
            level = self.field_confidence.get(field, "LOW")
            total_score += scores.get(level, 0.5) * weight

        return round(min(0.98, total_score), 3)

    def _extract_objects(self) -> Dict[str, Any]:
        """Extract legislative purpose from long title"""
        if not self.long_title:
            return {}

        lt = self.long_title.lower()
        patterns = [
            r'(?:to provide for|to make provision for)\s*(.+?)(?:;|\.|$)',
            r'(?:to amend|to consolidate|to repeal)\s*(.+?)(?:;|\.|$)',
            r'(?:for the regulation of|to regulate)\s*(.+?)(?:;|\.|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, lt)
            if match:
                return {
                    "purpose": match.group(1).strip()[:500],
                    "extracted_from": "long_title",
                    "confidence": "HIGH"
                }

        first_sent = re.split(r'[.;]', self.long_title)[0]
        return {
            "purpose": first_sent.strip()[:500],
            "extracted_from": "first_sentence",
            "confidence": "LOW"
        }


# ------------ Main Harvester (Single Implementation) ------------
class GazetteArchaeologist:
    """
    Production gazette harvester with connection pooling and concurrent processing.
    Single entry point with CLI args support.
    """

    def __init__(self, year: int, max_workers: int = 3, dry_run: bool = False):
        """
        Initialize the Gazette Archaeologist.

        Args:
            year: Target year to harvest
            max_workers: Number of concurrent workers
            dry_run: If True, skip actual uploads
        """
        self.year = year
        self.max_workers = max_workers
        self.dry_run = dry_run
        self.config = get_config()

        self.logger = logging.getLogger(self.__class__.__name__)
        self.metrics = HarvestMetrics()
        self.session = self._create_session()
        self.storage = self._init_storage()
        self.db_pool = self._init_db_pool()
        self._ensure_tables()
        self._lock = threading.Lock()

        # Rate limiting
        self._last_request_time = 0
        self._rate_limiter_lock = threading.Lock()

        self.logger.info(f"Gazette Archaeologist initialized for year {year}")
        self.logger.info(f"Configuration: {max_workers} workers, dry_run={dry_run}")

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.config["max_retries"],
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update({
            "User-Agent": "Meta-Historian/2.0 (Academic Research; github.com/meta-historian)",
            "Accept": "application/pdf, text/html"
        })

        return session

    def _init_storage(self):
        """Initialize Alibaba Cloud OSS or AWS S3"""
        if self.dry_run:
            self.logger.info("DRY RUN: Storage initialization skipped")
            return {"type": "dry_run", "client": None}

        provider = self.config["storage_provider"]

        if provider == "alibaba" and ALIBABA_OSS_AVAILABLE:
            if not all([self.config["alibaba_access_key"], self.config["alibaba_secret_key"]]):
                raise ValueError("Alibaba credentials not configured")

            auth = oss2.Auth(
                self.config["alibaba_access_key"],
                self.config["alibaba_secret_key"]
            )
            bucket = oss2.Bucket(
                auth,
                self.config["alibaba_endpoint"],
                self.config["bucket_name"]
            )

            try:
                bucket.get_bucket_info()
                self.logger.info(f"Connected to Alibaba Cloud OSS: {self.config['bucket_name']}")
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Alibaba OSS: {e}")

            return {"type": "alibaba", "client": bucket}
        else:
            import boto3

            kwargs = {"region_name": self.config["aws_region"]}

            if self.config["s3_endpoint"]:
                kwargs["endpoint_url"] = self.config["s3_endpoint"]

            if self.config["aws_access_key"]:
                kwargs["aws_access_key_id"] = self.config["aws_access_key"]
                kwargs["aws_secret_access_key"] = self.config["aws_secret_key"]

            client = boto3.client("s3", **kwargs)

            try:
                client.head_bucket(Bucket=self.config["bucket_name"])
                self.logger.info(f"Connected to S3: {self.config['bucket_name']}")
            except Exception as e:
                raise ConnectionError(f"Failed to connect to S3: {e}")

            return {"type": "s3", "client": client}

    def _init_db_pool(self) -> pool.ThreadedConnectionPool:
        """
        Initialize PostgreSQL connection pool with health check.
        Fixed: Use local conn_pool variable before assigning to self.db_pool
        """
        max_retries = 5

        for attempt in range(max_retries):
            try:
                conn_pool = psycopg2.pool.ThreadedConnectionPool(
                    self.config["db_pool_min"],
                    self.config["db_pool_max"],
                    self.config["postgres_dsn"],
                    connect_timeout=self.config["connection_timeout"]
                )

                # Test connection using the local conn_pool
                conn = None
                try:
                    conn = conn_pool.getconn()
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1")
                finally:
                    if conn:
                        conn_pool.putconn(conn)

                self.logger.info(
                    f"Database pool initialized ({self.config['db_pool_min']}-{self.config['db_pool_max']} connections)"
                )
                return conn_pool

            except Exception as e:
                self.logger.warning(f"DB pool init attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise RuntimeError(f"Failed to initialize database pool after {max_retries} attempts")

    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections from pool"""
        conn = None
        try:
            conn = self.db_pool.getconn()
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _ensure_tables(self):
        """
        Ensure ingestion_manifest and statutes tables exist.
        Fixed: Create uuid-ossp extension before using uuid_generate_v4()
        """
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                # CRITICAL FIX: Ensure uuid-ossp extension exists
                cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

                # Ingestion tracking for idempotency
                cur.execute("""
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
                """)

                # Ensure statutes table (now uuid_generate_v4 will work)
                cur.execute("""
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
                """)

                conn.commit()

    def _rate_limit(self):
        """Thread-safe rate limiting"""
        with self._rate_limiter_lock:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.config["rate_limit_seconds"]:
                time.sleep(self.config["rate_limit_seconds"] - elapsed)
            self._last_request_time = time.time()

    def _manifest_exists(self, gazette_id: str) -> bool:
        """Check if gazette already processed successfully"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM ingestion_manifest WHERE gazette_id = %s AND status = 'done'",
                    (gazette_id,)
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
        error: str = None,
        acts_count: int = 0
    ):
        """Upsert manifest record"""
        with self._get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
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
                """, (gazette_id, year, number, oss_key, sha256, url, status, error, acts_count))

                conn.commit()

    def harvest_year(self):
        """Main entry: Harvest all gazettes for target year with concurrent processing"""
        self.logger.info(f"🚀 Starting archaeological excavation of year {self.year}")

        if not self._health_check():
            raise RuntimeError("Health check failed, aborting harvest")

        # Discover gazettes
        gazette_numbers = self._discover_gazettes(self.year)
        self.metrics.gazettes_discovered = len(gazette_numbers)
        self.logger.info(f"📚 Discovered {len(gazette_numbers)} gazettes for {self.year}")

        # Process concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._process_gazette, self.year, num): num
                for num in gazette_numbers
            }

            for future in as_completed(futures):
                num = futures[future]
                try:
                    future.result()
                except Exception as e:
                    self.logger.exception(f"💥 Fatal error processing {self.year}/{num}: {e}")
                    with self._lock:
                        self.metrics.gazettes_failed += 1

        self.metrics.end_time = datetime.now()

        # Final summary
        summary = self.metrics.summary()
        self.logger.info(f"✅ Harvest complete for {self.year}")
        self.logger.info(f"Summary: {json.dumps(summary, indent=2)}")

        # Save metrics
        self._save_metrics(self.year, summary)

    def _health_check(self) -> bool:
        """Verify all systems operational before starting"""
        self.logger.info("Running health checks...")

        checks = {"database": False, "storage": False, "network": False}

        # Database check
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM ingestion_manifest")
                    count = cur.fetchone()[0]
                    self.logger.info(f"✓ Database: {count} manifests in database")
                    checks["database"] = True
        except Exception as e:
            self.logger.error(f"✗ Database check failed: {e}")

        # Storage check (skip in dry-run)
        if self.dry_run:
            self.logger.info("✓ Storage: Skipped (dry-run mode)")
            checks["storage"] = True
        else:
            try:
                if self.storage["type"] == "alibaba":
                    self.storage["client"].get_bucket_info()
                elif self.storage["type"] == "s3":
                    self.storage["client"].head_bucket(Bucket=self.config["bucket_name"])

                self.logger.info(f"✓ Storage: Connected to {self.storage['type']}")
                checks["storage"] = True
            except Exception as e:
                self.logger.error(f"✗ Storage check failed: {e}")

        # Network check
        try:
            response = self.session.head(self.config["base_url"], timeout=10)
            self.logger.info(f"✓ Network: Gazette source accessible (status {response.status_code})")
            checks["network"] = True
        except Exception as e:
            self.logger.error(f"✗ Network check failed: {e}")

        all_ok = all(checks.values())
        if all_ok:
            self.logger.info("✓ All health checks passed")
        else:
            self.logger.error(f"✗ Health checks failed: {checks}")

        return all_ok

    def _discover_gazettes(self, year: int) -> List[int]:
        """Discover available gazette numbers by probing"""
        found = []
        consecutive_404 = 0
        max_probe = self.config["max_gazette_number"]

        self.logger.info(f"Discovering gazettes for {year} (max {max_probe})...")

        for n in range(1, max_probe + 1):
            url = f"{self.config['base_url']}/{year}/{n}.pdf"

            try:
                self._rate_limit()
                resp = self.session.head(url, allow_redirects=True, timeout=10)

                if resp.status_code == 200:
                    found.append(n)
                    consecutive_404 = 0
                    self.logger.debug(f"Found: {year}/{n}")
                else:
                    consecutive_404 += 1

            except requests.RequestException as e:
                self.logger.debug(f"Request failed for {year}/{n}: {e}")
                consecutive_404 += 1

            if consecutive_404 >= self.config["consecutive_404_threshold"]:
                self.logger.info(f"Stopping discovery after {consecutive_404} consecutive misses at gazette {n}")
                break

            if n % 20 == 0:
                self.logger.info(f"Discovery progress: {n}/{max_probe} checked, {len(found)} found")

        return sorted(found)

    def _upload_to_storage(self, key: str, data: bytes, metadata: Dict) -> bool:
        """
        Upload to Alibaba OSS or S3 with error handling.
        Fixed: Respect dry-run mode
        """
        # DRY RUN GUARD
        if self.dry_run:
            self.logger.info(f"DRY RUN: Would upload {key} ({len(data)} bytes)")
            return True

        try:
            if self.storage["type"] == "alibaba":
                bucket = self.storage["client"]
                headers = {f"x-oss-meta-{k}": str(v)[:1024] for k, v in metadata.items()}
                bucket.put_object(key, data, headers=headers)
            else:
                # S3/MinIO
                self.storage["client"].put_object(
                    Bucket=self.config["bucket_name"],
                    Key=key,
                    Body=data,
                    ContentType="application/pdf",
                    Metadata={k: str(v)[:1024] for k, v in metadata.items()}
                )

            self.logger.debug(f"Uploaded to storage: {key}")
            return True

        except Exception as e:
            self.logger.error(f"Storage upload failed for {key}: {e}")
            with self._lock:
                self.metrics.storage_errors += 1
            return False

    def _process_gazette(self, year: int, gazette_num: int):
        """Process single gazette: download, store, parse, ingest"""
        url = f"{self.config['base_url']}/{year}/{gazette_num}.pdf"
        gazette_id = f"ZA_Gazette_{year}_{gazette_num:04d}"
        oss_key = f"gazettes/{year}/{gazette_num:04d}.pdf"

        # Idempotency check
        if self._manifest_exists(gazette_id):
            self.logger.info(f"⏩ Skipping {gazette_id} (already processed)")
            with self._lock:
                self.metrics.gazettes_skipped += 1
            return

        self.logger.info(f"📥 Processing {gazette_id}")
        self._update_manifest(gazette_id, year, gazette_num, oss_key, "", url, "processing")

        # Download
        try:
            self._rate_limit()
            resp = self.session.get(url, timeout=self.config["request_timeout"])
            resp.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"❌ Download failed for {gazette_id}: {e}")
            self._update_manifest(gazette_id, year, gazette_num, oss_key, "", url, "failed", str(e))
            with self._lock:
                self.metrics.download_errors += 1
                self.metrics.gazettes_failed += 1
            return

        pdf_bytes = resp.content

        # Validate PDF
        if not pdf_bytes.startswith(b'%PDF'):
            error_msg = "Invalid PDF magic bytes"
            self.logger.error(f"❌ {error_msg} for {gazette_id}")
            self._update_manifest(gazette_id, year, gazette_num, oss_key, "", url, "failed", error_msg)
            with self._lock:
                self.metrics.download_errors += 1
                self.metrics.gazettes_failed += 1
            return

        # Checksum
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()

        # Upload to OSS/S3 (respects dry-run)
        metadata = {
            "gazette-id": gazette_id,
            "source-url": url,
            "harvest-date": datetime.now().isoformat(),
            "content-sha256": sha256,
            "year": str(year),
            "number": str(gazette_num)
        }

        if not self._upload_to_storage(oss_key, pdf_bytes, metadata):
            self._update_manifest(gazette_id, year, gazette_num, oss_key, sha256, url, "failed", "Upload failed")
            with self._lock:
                self.metrics.gazettes_failed += 1
            return

        # Parse Acts
        try:
            acts = self._extract_acts(pdf_bytes, year, gazette_num)
            self.logger.info(f"📜 Extracted {len(acts)} acts from {gazette_id}")

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
                    self.logger.warning(f"Invalid act {act.act_number}: {errors}")

            # Batch store acts
            stored_count, updated_count = self._batch_store_acts(valid_acts)

            with self._lock:
                self.metrics.acts_stored += stored_count
                self.metrics.acts_updated += updated_count
                self.metrics.gazettes_processed += 1

            self._update_manifest(
                gazette_id, year, gazette_num, oss_key, sha256, url,
                "done", None, len(valid_acts)
            )

            self.logger.info(f"✅ Stored {stored_count} new + {updated_count} updated acts from {gazette_id}")

        except Exception as e:
            self.logger.exception(f"💥 Parsing failed for {gazette_id}: {e}")
            self._update_manifest(gazette_id, year, gazette_num, oss_key, sha256, url, "failed", str(e))
            with self._lock:
                self.metrics.parse_errors += 1
                self.metrics.gazettes_failed += 1

    def _extract_acts(self, pdf_bytes: bytes, year: int, gazette_num: int) -> List[ParsedAct]:
        """Extract individual Acts from PDF with improved error handling"""
        acts = []
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_bytes)
                temp_path = tmp.name

            with pdfplumber.open(temp_path) as pdf:
                pages_text = []
                for i, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text() or ""
                        pages_text.append(f"---PAGE {i+1}---\n{text}")
                    except Exception as e:
                        self.logger.warning(f"Failed to extract page {i+1}: {e}")
                        pages_text.append(f"---PAGE {i+1}---\n[EXTRACTION FAILED]")

                full_text = "\n".join(pages_text)

                act_blocks = self._split_into_acts(full_text, year)
                self.logger.debug(f"Found {len(act_blocks)} act blocks")

                for i, block in enumerate(act_blocks):
                    try:
                        act = self._parse_act_block(block, year, gazette_num)
                        if act:
                            acts.append(act)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse act block {i+1}: {e}")
                        continue

        except Exception as e:
            self.logger.error(f"PDF extraction failed: {e}")
            raise

        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    self.logger.warning(f"Failed to delete temp file {temp_path}: {e}")

        return acts

    def _split_into_acts(self, text: str, year: int) -> List[str]:
        """Split gazette text into individual Act blocks using regex"""
        header_pattern = re.compile(
            r'(?:^|\n)(?:(?:ACT|Act)\s*[Nn]?[Oo]?\.?\s*(\d+)\s*(?:of|,|/)\s*(\d{4})|'
            r'No\.?\s*(\d+)\s*/\s*(\d{4}))',
            re.IGNORECASE
        )

        matches = list(header_pattern.finditer(text))
        blocks = []

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block = text[start:end].strip()

            if len(block) > self.config["min_act_length"] and str(year) in block[:200]:
                blocks.append(block)
            elif len(block) > 1000:
                blocks.append(block)

        return blocks

    def _parse_act_block(self, block: str, year: int, gazette_num: int) -> Optional[ParsedAct]:
        """
        Parse single Act block into structured data.
        Fixed: Preserve newlines in whitespace normalization
        """
        # FIXED: Normalize only horizontal whitespace, preserve newlines
        # Replace unicode non-breaking spaces and other horizontal whitespace
        text = re.sub(r'[\u00A0\u2002\u2003\t]', ' ', block)
        # Normalize multiple spaces (but not newlines)
        text = re.sub(r'[^\S\n]+', ' ', text)

        lines = text.split('\n')

        if not lines:
            return None

        # Extract Act Number
        act_num = None
        first_lines = ' '.join(lines[:5])
        m = re.search(r'(?:Act|ACT|No\.?)\s*\.?\s*(\d+)\s*(?:of|,|/)\s*(\d{4})', first_lines, re.IGNORECASE)
        if m:
            act_num = m.group(1)
            act_year = m.group(2)
        else:
            return None

        act_number = f"Act {act_num} of {act_year}"

        # Extract Long Title (with newlines preserved)
        long_title = ""
        enacting_match = re.search(
            r'(?:BE IT ENACTED|To provide for|To amend|To consolidate|To repeal).*?(?=\n\s*1\.|\n\s*ARRANGEMENT|\n\s*WHEREAS|\Z)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if enacting_match:
            long_title = enacting_match.group(0).strip()[:1000]

        # Extract Preamble
        preamble = ""
        whereas_match = re.search(
            r'(WHEREAS|PREAMBLE).*?(?=\n\s*BE IT ENACTED|\n\s*NOW THEREFORE|\n\s*1\.)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if whereas_match:
            preamble = whereas_match.group(0).strip()[:5000]

        # Extract Sections
        sections = {}
        sec_pattern = re.compile(
            r'\n\s*(\d+[A-Z]?)\.?\s+([^\n]{10,500}?)(?=\n\s*\d+[A-Z]?\.?\s+|\Z)',
            re.DOTALL
        )

        for match in sec_pattern.finditer(text):
            sec_num = match.group(1)
            sec_text = match.group(2).strip()

            title_match = re.match(r'^([^\.\n]{5,200})', sec_text)
            title = title_match.group(1) if title_match else f"Section {sec_num}"

            sections[f"s{sec_num}"] = {
                "title": title[:200],
                "text": sec_text[:2000]
            }

        # Extract assent date
        assent_date = date(year, 1, 1)
        date_patterns = [
            r'assented to[^\d]*(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s*,?\s*(\d{4})',
            r'(\d{1,2})(?:st|nd|rd|th)?\s+day\s+of\s+(\w+)\s*,?\s*(\d{4})',
        ]

        for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE)
            if date_match:
                try:
                    from dateutil import parser
                    date_str = f"{date_match.group(1)} {date_match.group(2)} {date_match.group(3)}"
                    assent_date = parser.parse(date_str).date()
                    break
                except Exception as e:
                    self.logger.debug(f"Date parsing failed: {e}")

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
            "sections": "HIGH" if len(sections) >= self.config["min_section_count"] else "LOW",
            "overall": "HIGH" if all([
                act_num,
                len(long_title) > 50,
                len(sections) >= self.config["min_section_count"]
            ]) else "MODERATE"
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
            full_text=text[:self.config["max_full_text_chars"]],
            era=era,
            page_range=(0, 0),
            source_gazette_id="",
            source_url="",
            pdf_oss_key="",
            pdf_sha256="",
            field_confidence=field_confidence
        )

    def _derive_short_title(self, long_title: str, full_text: str, act_num: str, year: int) -> str:
        """Derive short title from content with better heuristics"""
        lt = (long_title or "").lower()
        ft = full_text[:3000].lower()

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
            "bantu authorities": "Bantu Authorities Act"
        }

        for key, title in known_acts.items():
            if key in lt or key in ft:
                return title

        short_match = re.search(
            r'(?:short title|this act may be cited).*?(?:as\s+)?["\']?([^"\'\n.]{5,100})["\']?',
            full_text,
            re.IGNORECASE
        )
        if short_match:
            return short_match.group(1).strip()[:100]

        if "to amend" in lt:
            target_match = re.search(r'to amend\s+(?:the\s+)?([^,;.]{5,80})', lt, re.IGNORECASE)
            if target_match:
                return f"{target_match.group(1).strip()} Amendment Act"

        return f"Act No. {act_num} of {year}"

    def _batch_store_acts(self, acts: List[ParsedAct]) -> Tuple[int, int]:
        """
        Store multiple acts efficiently using batch operations.
        Fixed: Removed duplicate confidence_probability in UPDATE

        Returns:
            Tuple of (stored_count, updated_count)
        """
        if not acts:
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
                            (act.act_number,)
                        )
                        existing = cur.fetchone()

                        if existing:
                            # FIXED: Removed duplicate confidence_probability line
                            cur.execute("""
                                UPDATE statutes 
                                SET belief_state = %s,
                                    transaction_time = CURRENT_TIMESTAMP,
                                    long_title = COALESCE(%s, long_title),
                                    preamble = COALESCE(%s, preamble),
                                    sections = COALESCE(%s::jsonb, sections),
                                    full_text = COALESCE(%s, full_text)
                                WHERE act_number = %s
                            """, (
                                f"revised_{datetime.now().isoformat()}",
                                record['long_title'],
                                record['preamble'],
                                Json(record['sections']),
                                record['full_text'],
                                act.act_number
                            ))
                            updated += 1
                        else:
                            # Insert new
                            columns = ', '.join(record.keys())
                            placeholders = ', '.join(['%s'] * len(record))

                            cur.execute(f"""
                                INSERT INTO statutes ({columns})
                                VALUES ({placeholders})
                            """, list(record.values()))
                            stored += 1

                conn.commit()

        except Exception as e:
            self.logger.error(f"Batch store failed: {e}")
            with self._lock:
                self.metrics.db_errors += 1
            raise

        return stored, updated

    def _save_metrics(self, year: int, summary: Dict):
        """Save harvest metrics to database and JSON file"""
        # Save to database
        try:
            with self._get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
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
                    """)

                    cur.execute("""
                        INSERT INTO harvest_metrics 
                        (harvest_year, duration_seconds, gazettes_discovered, gazettes_processed,
                         gazettes_failed, acts_extracted, acts_stored, error_count, summary)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        year,
                        summary['duration_seconds'],
                        summary['gazettes']['discovered'],
                        summary['gazettes']['processed'],
                        summary['gazettes']['failed'],
                        summary['acts']['extracted'],
                        summary['acts']['stored'],
                        summary['errors']['total'],
                        Json(summary)
                    ))

                    conn.commit()
                    self.logger.info("Metrics saved to database")

        except Exception as e:
            self.logger.error(f"Failed to save metrics to database: {e}")

        # Save to JSON file
        try:
            with open(f"harvest_metrics_{year}.json", "w") as f:
                json.dump(summary, f, indent=2)
            self.logger.info(f"Metrics saved to harvest_metrics_{year}.json")
        except Exception as e:
            self.logger.error(f"Failed to save metrics to JSON: {e}")

    def close(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'db_pool'):
                self.db_pool.closeall()
                self.logger.info("Database pool closed")

            if hasattr(self, 'session'):
                self.session.close()
                self.logger.info("HTTP session closed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# ------------ CLI Entry Point (Single Implementation) ------------
def main():
    """
    Main entry point with CLI argument parsing.
    Single implementation with proper arg handling.
    """
    parser = argparse.ArgumentParser(
        description="Meta-Historian Gazette Archaeologist - Harvest South African Government Gazettes"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=int(os.getenv("TARGET_YEAR", "1950")),
        help="Target year to harvest (default: from TARGET_YEAR env or 1950)"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=int(os.getenv("MAX_WORKERS", "3")),
        help="Number of concurrent workers (default: from MAX_WORKERS env or 3)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=os.getenv("DRY_RUN", "").lower() == "true",
        help="Dry run mode - skip uploads (default: from DRY_RUN env or false)"
    )

    args = parser.parse_args()

    # Setup logging with target year
    setup_logging(args.year)

    archaeologist = None
    exit_code = 0

    try:
        # Single constructor call with parsed args
        archaeologist = GazetteArchaeologist(
            year=args.year,
            max_workers=args.max_workers,
            dry_run=args.dry_run
        )
        archaeologist.harvest_year()

    except KeyboardInterrupt:
        logging.getLogger(__name__).warning("Harvest interrupted by user")
        exit_code = 130

    except Exception as e:
        logging.getLogger(__name__).exception(f"Fatal error: {e}")
        exit_code = 1

    finally:
        if archaeologist:
            archaeologist.close()

    return exit_code


if __name__ == "__main__":
    import sys
    sys.exit(main())
