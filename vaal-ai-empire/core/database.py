import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    """SQLite database for persistent client data"""

    def __init__(self, db_path: str = "data/vaal_empire.db"):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Clients table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    business_type TEXT NOT NULL,
                    phone TEXT UNIQUE NOT NULL,
                    email TEXT,
                    language TEXT DEFAULT 'afrikaans',
                    subscription_type TEXT,
                    subscription_amount REAL,
                    active INTEGER DEFAULT 1,
                    mailchimp_list_id TEXT,
                    asana_project_id TEXT,
                    created_at TEXT NOT NULL,
                    last_delivery TEXT
                )
            """)

            # Content packs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_packs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    posts_count INTEGER,
                    images_count INTEGER,
                    cost_usd REAL,
                    delivered INTEGER DEFAULT 0,
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            """)

            # Revenue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS revenue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'ZAR',
                    service_type TEXT NOT NULL,
                    payment_date TEXT NOT NULL,
                    payment_method TEXT,
                    invoice_number TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            """)

            # Usage logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_name TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    tokens_used INTEGER,
                    cost_usd REAL,
                    timestamp TEXT NOT NULL,
                    client_id TEXT
                )
            """)

 feat/model-orchestration-architecture
            # Model usage logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    location TEXT,
                    task TEXT,
                    tokens_used INTEGER,
                    cost_usd REAL,
                    client_id TEXT,

            # Social posts queue
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    platforms TEXT NOT NULL,
                    image_url TEXT,
                    scheduled_time TEXT NOT NULL,
                    posted INTEGER DEFAULT 0,
                    posted_at TEXT,
 main
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            """)

            conn.commit()
            logger.info("Database initialized successfully")

    def add_client(self, client_data: Dict) -> str:
        """Add new client to database"""
        client_id = client_data.get('id', f"vaal_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clients (id, name, business_type, phone, email, language,
                                   subscription_type, subscription_amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_id,
                client_data['name'],
                client_data['business_type'],
                client_data['phone'],
                client_data.get('email'),
                client_data.get('language', 'afrikaans'),
                client_data.get('subscription_type', 'social_media'),
                client_data.get('subscription_amount', 600.0),
                datetime.now().isoformat()
            ))
            conn.commit()
        logger.info(f"Added client: {client_data['name']} ({client_id})")
        return client_id

    def get_active_clients(self) -> List[Dict]:
        """Get all active clients"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE active = 1")
            return [dict(row) for row in cursor.fetchall()]

    def log_revenue(self, client_id: str, amount: float, service_type: str, payment_method: str = "WhatsApp") -> int:
        """Log revenue transaction"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO revenue (client_id, amount, service_type, payment_date, payment_method)
                VALUES (?, ?, ?, ?, ?)
            """, (client_id, amount, service_type, datetime.now().isoformat(), payment_method))
            revenue_id = cursor.lastrowid
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{revenue_id}"
            cursor.execute("UPDATE revenue SET invoice_number = ? WHERE id = ?", (invoice_number, revenue_id))
            conn.commit()
        logger.info(f"Logged revenue: R{amount} from {client_id}")
        return revenue_id

    def get_revenue_summary(self, days: int = 30) -> Dict:
        """Get revenue summary for last N days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT client_id) as client_count,
                    SUM(amount) as total_revenue,
                    AVG(amount) as avg_revenue,
                    service_type
                FROM revenue
                WHERE date(payment_date) >= date('now', '-' || ? || ' days')
                GROUP BY service_type
            """, (days,))
            results = cursor.fetchall()

        summary = {
            "total_revenue": sum(r[1] for r in results if r[1] is not None),
            "client_count": sum(r[0] for r in results if r[0] is not None),
            "by_service": {r[3]: {"revenue": r[1], "avg": r[2]} for r in results}
        }
        return summary
