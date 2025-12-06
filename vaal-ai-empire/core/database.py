import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
from contextlib import contextmanager
import os

logger = logging.getLogger(__name__)

class Database:
    """SQLite database for persistent client data"""

    def __init__(self, db_path: str = "data/vaal_empire.db"):
        self.db_path = db_path
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
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
                    last_delivery TEXT,
                    metadata TEXT
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
                    pack_data TEXT,
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
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            """)

            # Usage logs table for API tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_name TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    tokens_used INTEGER,
                    cost_usd REAL,
                    timestamp TEXT NOT NULL,
                    client_id TEXT,
                    success INTEGER DEFAULT 1,
                    error_message TEXT
                )
            """)

            # Model usage logs table (FIXED - removed merge conflict)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    location TEXT,
                    task TEXT,
                    tokens_used INTEGER,
                    cost_usd REAL,
                    client_id TEXT,
                    timestamp TEXT NOT NULL,
                    success INTEGER DEFAULT 1,
                    error_message TEXT
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
                    post_ids TEXT,
                    error_message TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            """)

            # Image generation queue
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS image_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    image_url TEXT,
                    generated_at TEXT,
                    cost_usd REAL,
                    error_message TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients(id)
                )
            """)

            # System health tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_check TEXT NOT NULL,
                    response_time_ms REAL,
                    error_message TEXT
                )
            """)

            conn.commit()
            logger.info("Database initialized successfully")

    def add_client(self, client_data: Dict) -> str:
        """Add new client to database with validation"""
        client_id = client_data.get('id', f"vaal_{datetime.now().strftime('%Y%m%d%H%M%S')}")

        # Validate required fields
        required_fields = ['name', 'business_type', 'phone']
        for field in required_fields:
            if field not in client_data:
                raise ValueError(f"Missing required field: {field}")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Store any additional metadata as JSON
            metadata = {k: v for k, v in client_data.items()
                       if k not in ['id', 'name', 'business_type', 'phone', 'email',
                                    'language', 'subscription_type', 'subscription_amount']}

            cursor.execute("""
                INSERT INTO clients (id, name, business_type, phone, email, language,
                                   subscription_type, subscription_amount, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_id,
                client_data['name'],
                client_data['business_type'],
                client_data['phone'],
                client_data.get('email'),
                client_data.get('language', 'afrikaans'),
                client_data.get('subscription_type', 'social_media'),
                client_data.get('subscription_amount', 600.0),
                datetime.now().isoformat(),
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()

        logger.info(f"Added client: {client_data['name']} ({client_id})")
        return client_id

    def get_client(self, client_id: str) -> Optional[Dict]:
        """Get single client by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
            row = cursor.fetchone()
            if row:
                client = dict(row)
                if client.get('metadata'):
                    client['metadata'] = json.loads(client['metadata'])
                return client
            return None

    def get_active_clients(self) -> List[Dict]:
        """Get all active clients"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clients WHERE active = 1")
            clients = [dict(row) for row in cursor.fetchall()]

            # Parse metadata
            for client in clients:
                if client.get('metadata'):
                    client['metadata'] = json.loads(client['metadata'])

            return clients

    def update_client(self, client_id: str, updates: Dict) -> bool:
        """Update client information"""
        if not updates:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            set_clauses = []
            values = []
            for key, value in updates.items():
                if key not in ['id', 'created_at']:  # Don't allow updating these
                    set_clauses.append(f"{key} = ?")
                    values.append(value)

            if not set_clauses:
                return False

            values.append(client_id)
            query = f"UPDATE clients SET {', '.join(set_clauses)} WHERE id = ?"

            cursor.execute(query, values)
            conn.commit()

            return cursor.rowcount > 0

    def log_revenue(self, client_id: str, amount: float, service_type: str,
                    payment_method: str = "WhatsApp", status: str = "pending") -> int:
        """Log revenue transaction"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO revenue (client_id, amount, service_type, payment_date,
                                   payment_method, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (client_id, amount, service_type, datetime.now().isoformat(),
                  payment_method, status))

            revenue_id = cursor.lastrowid
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{revenue_id:04d}"

            cursor.execute("UPDATE revenue SET invoice_number = ? WHERE id = ?",
                         (invoice_number, revenue_id))
            conn.commit()

        logger.info(f"Logged revenue: R{amount} from {client_id} - {invoice_number}")
        return revenue_id

    def update_payment_status(self, invoice_number: str, status: str) -> bool:
        """Update payment status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE revenue SET status = ? WHERE invoice_number = ?
            """, (status, invoice_number))
            conn.commit()
            return cursor.rowcount > 0

    def log_api_usage(self, api_name: str, operation: str, tokens_used: int = 0,
                      cost_usd: float = 0.0, client_id: str = None,
                      success: bool = True, error_message: str = None) -> int:
        """Log API usage for cost tracking"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO usage_logs (api_name, operation, tokens_used, cost_usd,
                                       timestamp, client_id, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (api_name, operation, tokens_used, cost_usd, datetime.now().isoformat(),
                  client_id, 1 if success else 0, error_message))
            conn.commit()
            return cursor.lastrowid

    def log_model_usage(self, model_id: str, location: str, task: str,
                       tokens_used: int = 0, cost_usd: float = 0.0,
                       client_id: str = None, success: bool = True,
                       error_message: str = None) -> int:
        """Log model usage for monitoring"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO model_usage_logs (model_id, location, task, tokens_used,
                                             cost_usd, client_id, timestamp, success,
                                             error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (model_id, location, task, tokens_used, cost_usd, client_id,
                  datetime.now().isoformat(), 1 if success else 0, error_message))
            conn.commit()
            return cursor.lastrowid

    def get_revenue_summary(self, days: int = 30) -> Dict:
        """Get revenue summary for last N days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT client_id) as client_count,
                    SUM(amount) as total_revenue,
                    AVG(amount) as avg_revenue,
                    service_type,
                    status
                FROM revenue
                WHERE date(payment_date) >= date('now', '-' || ? || ' days')
                GROUP BY service_type, status
            """, (days,))
            results = cursor.fetchall()

        summary = {
            "total_revenue": 0,
            "paid_revenue": 0,
            "pending_revenue": 0,
            "client_count": 0,
            "by_service": {}
        }

        for row in results:
            summary["total_revenue"] += row['total_revenue'] or 0
            if row['status'] == 'paid':
                summary["paid_revenue"] += row['total_revenue'] or 0
            elif row['status'] == 'pending':
                summary["pending_revenue"] += row['total_revenue'] or 0

            service = row['service_type']
            if service not in summary["by_service"]:
                summary["by_service"][service] = {
                    "revenue": 0,
                    "avg": 0,
                    "count": 0
                }

            summary["by_service"][service]["revenue"] += row['total_revenue'] or 0
            summary["by_service"][service]["avg"] = row['avg_revenue'] or 0
            summary["by_service"][service]["count"] += row['client_count'] or 0

        # Get unique client count
        cursor.execute("""
            SELECT COUNT(DISTINCT client_id) as total_clients
            FROM revenue
            WHERE date(payment_date) >= date('now', '-' || ? || ' days')
        """, (days,))
        summary["client_count"] = cursor.fetchone()['total_clients']

        return summary

    def get_cost_summary(self, days: int = 30) -> Dict:
        """Get API and model cost summary"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # API costs
            cursor.execute("""
                SELECT api_name, SUM(cost_usd) as total_cost, COUNT(*) as call_count
                FROM usage_logs
                WHERE date(timestamp) >= date('now', '-' || ? || ' days')
                GROUP BY api_name
            """, (days,))
            api_costs = {row['api_name']: {
                'cost': row['total_cost'] or 0,
                'calls': row['call_count']
            } for row in cursor.fetchall()}

            # Model costs
            cursor.execute("""
                SELECT model_id, SUM(cost_usd) as total_cost, COUNT(*) as usage_count,
                       SUM(tokens_used) as total_tokens
                FROM model_usage_logs
                WHERE date(timestamp) >= date('now', '-' || ? || ' days')
                GROUP BY model_id
            """, (days,))
            model_costs = {row['model_id']: {
                'cost': row['total_cost'] or 0,
                'uses': row['usage_count'],
                'tokens': row['total_tokens'] or 0
            } for row in cursor.fetchall()}

        return {
            "api_costs": api_costs,
            "model_costs": model_costs,
            "total_cost": sum(c['cost'] for c in api_costs.values()) +
                         sum(c['cost'] for c in model_costs.values())
        }

    def save_content_pack(self, client_id: str, pack_data: Dict,
                         posts_count: int, images_count: int,
                         cost_usd: float) -> int:
        """Save generated content pack"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO content_packs (client_id, generated_at, posts_count,
                                          images_count, cost_usd, pack_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (client_id, datetime.now().isoformat(), posts_count, images_count,
                  cost_usd, json.dumps(pack_data)))
            conn.commit()
            return cursor.lastrowid

    def health_check(self) -> bool:
        """Check database health"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False