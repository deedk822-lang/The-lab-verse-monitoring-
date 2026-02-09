"""
Bi-Temporal Database Store
Handles Valid Time vs Transaction Time queries

Improvements:
- Connection pooling for better performance
- Comprehensive error handling and recovery
- Transaction management
- Query optimization
- Better type safety
- Audit logging
"""

import json
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor


@dataclass
class QueryOptions:
    """Options for temporal queries"""
    limit: Optional[int] = None
    offset: Optional[int] = 0
    order_by: Optional[str] = None
    include_deleted: bool = False


class BiTemporalStoreError(Exception):
    """Base exception for BiTemporalStore errors"""


class ConnectionError(BiTemporalStoreError):
    """Database connection errors"""


class QueryError(BiTemporalStoreError):
    """Query execution errors"""


class ValidationError(BiTemporalStoreError):
    """Data validation errors"""


class BiTemporalStore:
    """
    Handles Valid Time vs Transaction Time queries.

    Valid Time: When the fact was true in the real world
    Transaction Time: When the fact was recorded in the database
    """

    # Configuration
    MIN_POOL_SIZE = 2
    MAX_POOL_SIZE = 20
    CONNECTION_TIMEOUT = 30

    def __init__(self, dsn: str, min_pool_size: int = MIN_POOL_SIZE,
                 max_pool_size: int = MAX_POOL_SIZE):
        """
        Initialize bi-temporal store with connection pooling.

        Args:
            dsn: Database connection string
            min_pool_size: Minimum connections in pool
            max_pool_size: Maximum connections in pool
        """
        self.dsn = dsn
        self.logger = logging.getLogger(self.__class__.__name__)

        try:
            self._init_pool(min_pool_size, max_pool_size)
            self.logger.info(f"Connection pool initialized ({min_pool_size}-{max_pool_size} connections)")
        except Exception as e:
            self.logger.error(f"Failed to initialize connection pool: {e}")
            raise ConnectionError(f"Database initialization failed: {e}") from e

    def _init_pool(self, min_conn: int, max_conn: int) -> None:
        """Initialize connection pool"""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                min_conn,
                max_conn,
                self.dsn,
                connect_timeout=self.CONNECTION_TIMEOUT
            )
        except psycopg2.Error as e:
            raise ConnectionError(f"Failed to create connection pool: {e}") from e

    @contextmanager
    def _get_cursor(self, commit: bool = True):
        """
        Context manager for database cursors with automatic connection management.

        Args:
            commit: Whether to commit on success
        """
        conn = None
        cursor = None
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            yield cursor

            if commit:
                conn.commit()

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise QueryError(f"Query failed: {e}") from e

        except Exception:
            if conn:
                conn.rollback()
            raise

        finally:
            if cursor:
                cursor.close()
            if conn:
                self.connection_pool.putconn(conn)

    def insert_event(
        self,
        valid_from: date,
        valid_to: Optional[date],
        domain: str,
        province: str,
        event_type: str,
        description: str,
        confidence_level: str,
        confidence_prob: float,
        is_anchor: bool = False,
        raw_data: Optional[Dict] = None,
        source_documents: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> str:
        """
        Insert event with automatic transaction time stamping.

        Args:
            valid_from: When the event started (valid time)
            valid_to: When the event ended (None for ongoing)
            domain: Domain code (POL, ECO, etc.)
            province: Province code
            event_type: Type of event
            description: Event description
            confidence_level: Categorical confidence
            confidence_prob: Numerical confidence (0-1)
            is_anchor: Whether this is an immutable anchor
            raw_data: Additional structured data
            source_documents: List of source document IDs
            created_by: User/system that created the event

        Returns:
            UUID of created event

        Raises:
            ValidationError: If input validation fails
            QueryError: If insertion fails
        """
        # Validate inputs
        self._validate_event_inputs(
            valid_from, valid_to, domain, confidence_level, confidence_prob
        )

        with self._get_cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO historical_ledger
                    (valid_from, valid_to, domain_id, province_code, event_type,
                     description, confidence_level, confidence_probability,
                     is_anchor, raw_data, source_documents, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING event_id
                """, (
                    valid_from, valid_to, domain, province, event_type,
                    description, confidence_level, confidence_prob, is_anchor,
                    json.dumps(raw_data) if raw_data else None,
                    source_documents,
                    created_by or 'system'
                ))

                result = cur.fetchone()
                event_id = str(result['event_id'])

                self.logger.info(f"Inserted event {event_id} for {domain}/{province} on {valid_from}")
                return event_id

            except psycopg2.IntegrityError as e:
                raise ValidationError(f"Data integrity violation: {e}") from e
            except Exception as e:
                raise QueryError(f"Insert failed: {e}") from e

    def query_as_of(
        self,
        query_date: date,
        belief_state: str = "current",
        domain: Optional[str] = None,
        province: Optional[str] = None,
        options: Optional[QueryOptions] = None
    ) -> List[Dict]:
        """
        Query what the system believed at a specific transaction time.

        This is the key bi-temporal feature: "What did we believe about 1985 in 2003?"

        Args:
            query_date: The valid time to query (when events occurred)
            belief_state: The transaction time view (when we knew about them)
            domain: Optional domain filter
            province: Optional province filter
            options: Query options (limit, offset, etc.)

        Returns:
            List of events matching the temporal criteria
        """
        options = options or QueryOptions()

        # Build dynamic query
        query_parts = ["""
            SELECT
                event_id,
                valid_from,
                valid_to,
                domain_id,
                province_code,
                event_type,
                description,
                confidence_level,
                confidence_probability,
                is_anchor,
                raw_data,
                transaction_time,
                belief_state,
                source_documents,
                created_by
            FROM historical_ledger
            WHERE valid_from <= %s
            AND (valid_to IS NULL OR valid_to > %s)
            AND belief_state = %s
        """]

        params = [query_date, query_date, belief_state]

        # Add optional filters
        if domain:
            query_parts.append(" AND domain_id = %s")
            params.append(domain)

        if province:
            query_parts.append(" AND province_code = %s")
            params.append(province)

        # Add ordering
        if options.order_by:
            query_parts.append(f" ORDER BY {options.order_by}")
        else:
            query_parts.append(" ORDER BY valid_from DESC, transaction_time DESC")

        # Add pagination
        if options.limit:
            query_parts.append(" LIMIT %s")
            params.append(options.limit)

        if options.offset:
            query_parts.append(" OFFSET %s")
            params.append(options.offset)

        query = " ".join(query_parts)

        with self._get_cursor(commit=False) as cur:
            try:
                cur.execute(query, params)
                results = [dict(row) for row in cur.fetchall()]

                self.logger.debug(
                    f"Query returned {len(results)} events for {query_date} "
                    f"(belief: {belief_state}, domain: {domain})"
                )

                return results

            except Exception as e:
                raise QueryError(f"Query execution failed: {e}") from e

    def belief_revision(
        self,
        event_id: str,
        new_data: Dict[str, Any],
        revision_reason: str,
        user: str
    ) -> None:
        """
        Update belief while preserving audit trail.

        This implements the bi-temporal pattern by:
        1. Logging the revision in the audit trail
        2. Updating the event with a new belief state
        3. Preserving the transaction time history

        Args:
            event_id: UUID of event to revise
            new_data: Dictionary of fields to update
            revision_reason: Why the revision is being made
            user: User making the revision
        """
        with self._get_cursor() as cur:
            try:
                # Get current state
                cur.execute(
                    "SELECT * FROM historical_ledger WHERE event_id = %s",
                    (event_id,)
                )
                old_record = cur.fetchone()

                if not old_record:
                    raise ValidationError(f"Event {event_id} not found")

                # Log revision in audit trail
                cur.execute("""
                    INSERT INTO belief_revisions
                    (event_id, previous_belief, new_belief, revision_reason, revised_by)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING revision_id
                """, (
                    event_id,
                    json.dumps(dict(old_record)),
                    json.dumps(new_data),
                    revision_reason,
                    user
                ))

                revision_id = cur.fetchone()['revision_id']

                # Build update query dynamically
                update_fields = []
                update_values = []

                # Handle standard fields
                field_mapping = {
                    'description': 'description',
                    'confidence_level': 'confidence_level',
                    'confidence_probability': 'confidence_probability',
                    'raw_data': 'raw_data'
                }

                for key, db_field in field_mapping.items():
                    if key in new_data:
                        update_fields.append(f"{db_field} = %s")
                        value = new_data[key]
                        if key == 'raw_data' and isinstance(value, dict):
                            value = json.dumps(value)
                        update_values.append(value)

                # Always update belief state and transaction time
                belief_state = f"revised_{datetime.now().isoformat()}"
                update_fields.extend([
                    "belief_state = %s",
                    "transaction_time = CURRENT_TIMESTAMP"
                ])
                update_values.append(belief_state)

                # Add event_id for WHERE clause
                update_values.append(event_id)

                # Execute update
                update_query = f"""
                    UPDATE historical_ledger
                    SET {', '.join(update_fields)}
                    WHERE event_id = %s
                """

                cur.execute(update_query, update_values)

                self.logger.info(
                    f"Revised event {event_id} (revision_id: {revision_id})"
                )

            except Exception as e:
                raise QueryError(f"Belief revision failed: {e}") from e

    def get_revision_history(self, event_id: str) -> List[Dict]:
        """
        Get complete revision history for an event.

        Args:
            event_id: UUID of event

        Returns:
            List of revisions ordered by time
        """
        with self._get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT
                    revision_id,
                    previous_belief,
                    new_belief,
                    revision_reason,
                    revised_by,
                    revised_at
                FROM belief_revisions
                WHERE event_id = %s
                ORDER BY revised_at DESC
            """, (event_id,))

            return [dict(row) for row in cur.fetchall()]

    def query_confidence_distribution(
        self,
        domain: Optional[str] = None,
        year_range: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Get confidence level distribution across events.

        Useful for identifying data quality issues.
        """
        query = """
            SELECT
                confidence_level,
                COUNT(*) as count,
                AVG(confidence_probability) as avg_prob,
                MIN(confidence_probability) as min_prob,
                MAX(confidence_probability) as max_prob
            FROM historical_ledger
            WHERE belief_state = 'current'
        """

        params = []

        if domain:
            query += " AND domain_id = %s"
            params.append(domain)

        if year_range:
            query += " AND EXTRACT(YEAR FROM valid_from) BETWEEN %s AND %s"
            params.extend(year_range)

        query += " GROUP BY confidence_level ORDER BY confidence_level"

        with self._get_cursor(commit=False) as cur:
            cur.execute(query, params)
            results = [dict(row) for row in cur.fetchall()]

            total = sum(r['count'] for r in results)

            return {
                'distribution': results,
                'total_events': total,
                'domain': domain,
                'year_range': year_range
            }

    def _validate_event_inputs(
        self,
        valid_from: date,
        valid_to: Optional[date],
        domain: str,
        confidence_level: str,
        confidence_prob: float
    ) -> None:
        """Validate event inputs before insertion"""

        # Validate temporal consistency
        if valid_to and valid_from > valid_to:
            raise ValidationError(
                f"valid_from ({valid_from}) must be <= valid_to ({valid_to})"
            )

        # Validate confidence level
        valid_levels = ['VERY_HIGH', 'HIGH', 'MODERATE', 'LOW', 'VERY_LOW']
        if confidence_level not in valid_levels:
            raise ValidationError(
                f"confidence_level must be one of {valid_levels}, got {confidence_level}"
            )

        # Validate confidence probability
        if not 0.0 <= confidence_prob <= 1.0:
            raise ValidationError(
                f"confidence_prob must be between 0 and 1, got {confidence_prob}"
            )

        # Validate domain
        valid_domains = ['POL', 'ECO', 'DEM', 'INF', 'ENV', 'SOC']
        if domain not in valid_domains:
            raise ValidationError(
                f"domain must be one of {valid_domains}, got {domain}"
            )

    def close(self) -> None:
        """Close all connections in the pool"""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.closeall()
            self.logger.info("Connection pool closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def health_check(self) -> Dict[str, Any]:
        """
        Check database health and return status.

        Returns:
            Dictionary with health status information
        """
        try:
            with self._get_cursor(commit=False) as cur:
                cur.execute("SELECT 1")
                cur.fetchone()

                # Get pool statistics
                pool_info = {
                    'status': 'healthy',
                    'pool_size': len(self.connection_pool._pool),
                    'available_connections': len(self.connection_pool._pool)
                }

                # Get database statistics
                cur.execute("""
                    SELECT
                        COUNT(*) as total_events,
                        COUNT(DISTINCT domain_id) as domains,
                        MIN(valid_from) as earliest_event,
                        MAX(valid_from) as latest_event
                    FROM historical_ledger
                    WHERE belief_state = 'current'
                """)

                stats = dict(cur.fetchone())
                pool_info.update(stats)

                return pool_info

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
