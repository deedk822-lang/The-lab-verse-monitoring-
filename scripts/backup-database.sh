#!/bin/bash
# S10: Automated Database Backup

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/pr_fix_agent_${TIMESTAMP}.sql.gz"

echo "Starting database backup..."
pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$PGDATABASE" | gzip > "$BACKUP_FILE"

echo "Backup completed: $BACKUP_FILE"

# Retention: Remove backups older than BACKUP_RETENTION_DAYS
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +"$BACKUP_RETENTION_DAYS" -delete
echo "Cleanup of old backups completed."
