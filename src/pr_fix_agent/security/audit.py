"""
Immutable Audit Logger - Global Production Standard (S5)
FIXED: No duplicate handlers, thread-safe, append-only
"""

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger()

class AuditLogger:
    """
    Append-only audit logger for compliance (SOC 2, GDPR).

    Features:
    - ✅ Immutable (append-only)
    - ✅ No duplicate handlers
    - ✅ Thread-safe singleton
    - ✅ JSON format
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, log_path: Optional[Path] = None):
        with cls._lock:
            if cls._instance is None:
                if log_path is None:
                    log_path = Path("logs/audit.log")
                cls._instance = super(AuditLogger, cls).__new__(cls)
                cls._instance._init_logger(log_path)
            return cls._instance

    def _init_logger(self, log_path: Path):
        """Initialize the logger with proper handlers."""
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("audit_trail")
        self.logger.setLevel(logging.INFO)

        # ✅ FIX: Disable propagation to root to prevent duplicates
        self.logger.propagate = False

        # ✅ FIX: Only add handler if it doesn't exist
        if not self.logger.handlers:
            handler = logging.FileHandler(
                self.log_path,
                mode='a',  # Append only
                encoding='utf-8'
            )
            # Simple formatter for raw JSON lines
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)

        logger.info("audit_logger_initialized", path=str(log_path))

    def log_event(
        self,
        event_type: str,
        actor_id: str,
        actor_ip: str,
        resource: str,
        action: str,
        result: str,
        request_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log an audit event (immutable).

        Args:
            event_type: Type of event (e.g., 'access_control')
            actor_id: ID of the user or system
            actor_ip: IP address of the actor
            resource: Resource being accessed
            action: Action performed (e.g., 'read', 'write')
            result: Result of action ('success', 'failure')
            request_id: Correlation ID for the request
            metadata: Additional contextual data
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "actor_id": actor_id,
            "actor_ip": actor_ip,
            "resource": resource,
            "action": action,
            "result": result,
            "request_id": request_id,
            "metadata": metadata or {},
        }

        # Write as single JSON line (append-only)
        self.logger.info(json.dumps(event))


def get_audit_logger(log_path: Optional[Path] = None) -> AuditLogger:
    """Helper to get the singleton audit logger."""
    return AuditLogger(log_path)
