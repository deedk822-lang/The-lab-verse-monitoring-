"""
S5: Immutable Audit Logging for Compliance
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from pr_fix_agent.core.config import get_settings


class AuditLogger:
    """
    Append-only audit logger for compliance.
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(
            self.log_path,
            mode="a",
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))

        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

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
        self.logger.info(json.dumps(event))


@lru_cache
def get_audit_logger() -> AuditLogger:
    """Get cached audit logger instance."""
    settings = get_settings()
    return AuditLogger(settings.audit_log_path)
