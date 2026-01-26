import sqlite3
import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class Database:
    """
    Minimal SQLite database for tracking API usage, revenue, and content packs.
    """

    def __init__(self, db_path: str = "data/vaal_ai.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # API Usage table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT,
                    endpoint TEXT,
                    tokens INTEGER DEFAULT 0,
                    cost_usd REAL DEFAULT 0.0,
                    success INTEGER,
                    error_message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            # Content Packs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS content_packs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT,
                    pack_data TEXT,
                    posts_count INTEGER,
                    images_count INTEGER,
                    cost_usd REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            # Clients table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    business_type TEXT,
                    status TEXT DEFAULT 'active'
                )
            """
            )
            conn.commit()

    def log_api_usage(
        self,
        provider: str,
        endpoint: str,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO api_usage (provider, endpoint, tokens, cost_usd, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (provider, endpoint, tokens_used, cost_usd, 1 if success else 0, error_message),
            )
            conn.commit()

    def save_content_pack(self, client_id: str, pack_data: Dict, posts_count: int, images_count: int, cost_usd: float):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO content_packs (client_id, pack_data, posts_count, images_count, cost_usd)
                VALUES (?, ?, ?, ?, ?)
            """,
                (client_id, json.dumps(pack_data), posts_count, images_count, cost_usd),
            )
            conn.commit()

    def get_revenue_summary(self, days: int = 30) -> Dict[str, Any]:
        # Minimal stub for RevenueAnomalyDetector
        # In a real system, this would query a billing/revenue table
        return {"total_revenue": 5000.0, "client_count": len(self.get_active_clients())}  # Placeholder

    def get_active_clients(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE status = 'active'")
            return [dict(row) for row in cursor.fetchall()]
