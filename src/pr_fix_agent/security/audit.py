from __future__ import annotations

import json
import logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from pr_fix_agent.core.config import Settings, get_settings


class AuditLogger:
    """
    Append-only audit logger for compliance (SOC 2, GDPR).

    FIXED:
    - Prevents duplicate handlers
    - Disables propagation to avoid root logger interference
    - Thread-safe singleton pattern
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Get logger
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # ✅ FIX: Disable propagation to prevent root logger interference
        self.logger.propagate = False

        # ✅ FIX: Check for existing handlers to prevent duplicates
        existing_handler = None
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                # Check if it's the same file
                if hasattr(handler, 'baseFilename') and \
                   handler.baseFilename == str(self.log_path.resolve()):
                    existing_handler = handler
                    break

        # ✅ FIX: Only add handler if it doesn't exist
        if existing_handler is None:
            # Create append-only file handler
            handler = logging.FileHandler(
                self.log_path,
                mode='a',  # Append only (immutable)
                encoding='utf-8',
            )
            handler.setFormatter(logging.Formatter('%(message)s'))

            self.logger.addHandler(handler)
        else:
            # Handler already exists, no need to add
            pass

    def log_event(
        self,
        event_type: str,
        actor_id: str,
        actor_ip: str,
        resource: str,
        action: str,
        result: str,
        request_id: str,
        metadata: dict[str, any] | None = None,
    ) -> None:
        """
        Log audit event (immutable).

        Args:
            event_type: Type of event (user_created, role_changed, etc.)
            actor_id: User ID performing the action
            actor_ip: IP address of the actor
            resource: Resource being accessed
            action: Action being performed
            result: Result of the action (success/failure)
            request_id: Correlation ID for tracing
            metadata: Additional context
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "actor_id": actor_id,
            "actor_ip": actor_ip,
            "resource": resource,
            "action": action,
            "result": result,
            "request_id": request_id,
            "metadata": metadata or {},
        }

        # Write as single JSON line (append-only, immutable)
        self.logger.info(json.dumps(event))

    def __del__(self):
        """Cleanup: Close handlers on deletion."""
        # Close all file handlers
        for handler in self.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                self.logger.removeHandler(handler)


@lru_cache
def get_audit_logger() -> AuditLogger:
    """
    Get cached audit logger instance (thread-safe singleton).

    ✅ FIX: Using lru_cache ensures only one instance is created
    """
    settings = get_settings()
    return AuditLogger(settings.audit_log_path)
