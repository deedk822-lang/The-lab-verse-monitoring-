#!/bin/bash
# ============================================================================
# VAAL AI Empire - Database Backup Script
# ============================================================================

set -e

# Configuration
BACKUP_DIR="/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/vaal_backup_${DATE}.sql.gz"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

echo "[$(date)] Starting backup..."

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Perform backup
echo "[$(date)] Creating backup: ${BACKUP_FILE}"
pg_dump -Fc -Z 9 | gzip > "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo "[$(date)] Backup completed successfully"
    
    # Calculate backup size
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "[$(date)] Backup size: ${BACKUP_SIZE}"
    
    # Remove old backups
    echo "[$(date)] Cleaning up backups older than ${RETENTION_DAYS} days..."
    find "${BACKUP_DIR}" -name "vaal_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
    
    # Count remaining backups
    BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}"/vaal_backup_*.sql.gz 2>/dev/null | wc -l)
    echo "[$(date)] Total backups: ${BACKUP_COUNT}"
    
    echo "[$(date)] Backup process completed"
    exit 0
else
    echo "[$(date)] ERROR: Backup failed!"
    exit 1
fi
