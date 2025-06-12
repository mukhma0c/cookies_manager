#!/bin/bash
# Cookie Manager Backup Script
# Creates a backup of the database and static files

# Configuration
BACKUP_DIR="/path/to/backups"
APP_DIR="/path/to/cookiemgr"
DB_FILE="$APP_DIR/instance/db.sqlite3"
STATIC_DIR="$APP_DIR/static"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="cookiemgr_backup_$DATE"

# Ensure backup directory exists
mkdir -p $BACKUP_DIR

# Create backup directory for this run
CURRENT_BACKUP="$BACKUP_DIR/$BACKUP_NAME"
mkdir -p $CURRENT_BACKUP

# Backup database
echo "Backing up database..."
if [ -f "$DB_FILE" ]; then
    sqlite3 $DB_FILE ".backup '$CURRENT_BACKUP/db.sqlite3'"
    echo "Database backup complete."
else
    echo "Error: Database file not found at $DB_FILE"
    exit 1
fi

# Backup static files (images, etc)
echo "Backing up static files..."
if [ -d "$STATIC_DIR" ]; then
    cp -r $STATIC_DIR $CURRENT_BACKUP/
    echo "Static files backup complete."
else
    echo "Warning: Static directory not found at $STATIC_DIR"
fi

# Create a single archive
echo "Creating archive..."
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C $BACKUP_DIR $BACKUP_NAME
rm -rf $CURRENT_BACKUP

# Keep only the 10 most recent backups
echo "Cleaning up old backups..."
ls -t $BACKUP_DIR/*.tar.gz | tail -n +11 | xargs -r rm

echo "Backup completed: $BACKUP_DIR/$BACKUP_NAME.tar.gz"

# Optional: Copy to another location (like cloud storage)
# rclone copy "$BACKUP_DIR/$BACKUP_NAME.tar.gz" remote:cookiemgr-backups/
