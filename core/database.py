import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
import os

logger = logging.getLogger(__name__)

class Database:
    """SQLite database for persistent client data"""

    def __init__(self, db_path: str = "data/vaal_empire.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()

    def init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
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
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)

        conn.commit()
        conn.close()

    def schedule_post_pack(self, client_id: str, posts: List[Dict]):
        """Schedule a batch of posts in a single transaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        posts_to_schedule = [
            (client_id, post['content'], post['platforms'], post['scheduled_time'])
            for post in posts
        ]

        cursor.executemany("""
            INSERT INTO post_queue (client_id, content, platforms, scheduled_time)
            VALUES (?, ?, ?, ?)
        """, posts_to_schedule)

        conn.commit()
        conn.close()
        logger.info(f"Scheduled {len(posts)} posts for client {client_id}")

    def add_client(self, client_data: Dict) -> str:
        """Add new client to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        client_id = client_data.get('id', f"vaal_{datetime.now().strftime('%Y%m%d%H%M%S')}")

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
        conn.close()
        logger.info(f"Added client: {client_data['name']} ({client_id})")
        return client_id

    def get_active_clients(self) -> List[Dict]:
        """Get all active clients"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM clients WHERE active = 1")
        clients = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return clients

    def log_revenue(self, client_id: str, amount: float, service_type: str, payment_method: str = "WhatsApp") -> int:
        """Log revenue transaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO revenue (client_id, amount, service_type, payment_date, payment_method)
            VALUES (?, ?, ?, ?, ?)
        """, (client_id, amount, service_type, datetime.now().isoformat(), payment_method))

        revenue_id = cursor.lastrowid
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{revenue_id}"

        cursor.execute("UPDATE revenue SET invoice_number = ? WHERE id = ?", (invoice_number, revenue_id))

        conn.commit()
        conn.close()

        logger.info(f"Logged revenue: R{amount} from {client_id}")
        return invoice_number

    def get_revenue_summary(self, days: int = 30) -> Dict:
        """Get revenue summary for last N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get total distinct clients and revenue
        cursor.execute("""
            SELECT
                COUNT(DISTINCT client_id),
                SUM(amount)
            FROM revenue
            WHERE date(payment_date) >= date('now', '-' || ? || ' days')
        """, (days,))
        client_count, total_revenue = cursor.fetchone()

        # Get revenue by service type
        cursor.execute("""
            SELECT
                service_type,
                SUM(amount) as total_revenue,
                AVG(amount) as avg_revenue
            FROM revenue
            WHERE date(payment_date) >= date('now', '-' || ? || ' days')
            GROUP BY service_type
        """, (days,))

        results = cursor.fetchall()
        conn.close()

        summary = {
            "total_revenue": total_revenue or 0,
            "client_count": client_count or 0,
            "by_service": {r[0]: {"revenue": r[1], "avg": r[2]} for r in results}
        }

        return summary

    def get_client_by_id(self, client_id: str) -> Optional[Dict]:
        """Get a single client by their ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client = cursor.fetchone()

        conn.close()
        return dict(client) if client else None

    def update_client_to_active(self, client_id: str, subscription_amount: float):
        """Update a client's status to active"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE clients
            SET active = 1, subscription_type = 'social_media', subscription_amount = ?
            WHERE id = ?
        """, (subscription_amount, client_id))

        conn.commit()
        conn.close()

    def schedule_post(self, client_id: str, content: str, platforms: str, scheduled_time: str):
        """Add a post to the scheduling queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO post_queue (client_id, content, platforms, scheduled_time)
            VALUES (?, ?, ?, ?)
        """, (client_id, content, platforms, scheduled_time))

        conn.commit()
        conn.close()

    def get_due_posts(self) -> List[Dict]:
        """Get posts that are due to be published"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM post_queue
            WHERE posted = 0
            AND datetime(scheduled_time) <= datetime('now')
            ORDER BY scheduled_time
            LIMIT 50
        """)

        posts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return posts

    def mark_post_as_posted(self, post_id: int):
        """Mark a post as published"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE post_queue
            SET posted = 1, posted_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), post_id))

        conn.commit()
        conn.close()
