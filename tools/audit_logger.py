import os
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess

logger = logging.getLogger(__name__)

# ============================================================
# AUDIT LOGGER
# ============================================================

class AuditLogger:
    """Comprehensive audit logging for all operations"""

    def __init__(self):
        self.log_dir = Path('.jules/logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.audit_file = self.log_dir / 'audit.jsonl'
        self.task_dir = self.log_dir / 'tasks'
        self.task_dir.mkdir(exist_ok=True)

        logger.info("✓ Audit Logger initialized")

    async def log_task_start(self, context: Dict):
        """Log task initiation"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'task_start',
            'task_id': context['task_id'],
            'intent': context['intent'],
            'requester': context.get('requester', 'unknown')
        }

        await self._write_audit_entry(entry)
        await self._write_task_log(context['task_id'], 'start', context)

    async def log_task_complete(self, context: Dict):
        """Log task completion"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'task_complete',
            'task_id': context['task_id'],
            'outcome': context.get('outcome', {}),
            'confidence': context.get('confidence'),
            'files_changed': context.get('files_changed'),
            'duration_seconds': context.get('duration_seconds')
        }

        await self._write_audit_entry(entry)
        await self._write_task_log(context['task_id'], 'complete', context)

    async def log_task_error(self, context: Dict, error: Exception):
        """Log task error"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'task_error',
            'task_id': context['task_id'],
            'error': str(error),
            'error_type': type(error).__name__
        }

        await self._write_audit_entry(entry)
        await self._write_task_log(context['task_id'], 'error', {
            **context,
            'error': str(error)
        })

    async def log_security_rejection(self, task_id: str, security_result: Dict):
        """Log security-based rejection"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'security_rejection',
            'task_id': task_id,
            'critical_issues': len(security_result.get('critical_issues', []))
        }

        await self._write_audit_entry(entry)

    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Retrieve task information from audit log"""
        task_file = self.task_dir / f"{task_id}.json"

        if task_file.exists():
            return json.loads(task_file.read_text())

        return None

    async def _write_audit_entry(self, entry: Dict):
        """Write entry to audit log"""
        try:
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit entry: {str(e)}")

    async def _write_task_log(self, task_id: str, event: str, data: Dict):
        """Write detailed task log"""
        try:
            task_file = self.task_dir / f"{task_id}.json"

            if task_file.exists():
                task_data = json.loads(task_file.read_text())
            else:
                task_data = {'task_id': task_id, 'events': []}

            task_data['events'].append({
                'timestamp': datetime.now().isoformat(),
                'event': event,
                'data': data
            })

            task_file.write_text(json.dumps(task_data, indent=2))

        except Exception as e:
            logger.error(f"Failed to write task log: {str(e)}")
