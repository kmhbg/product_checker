#!/bin/bash
# Backup script för produktbilder och status
DATE=$(date +%Y%m%d)
BACKUP_DIR="/path/to/backups"

# Backup produktbilder
tar -czf $BACKUP_DIR/product_images_$DATE.tar.gz /path/to/production/images

# Backup status.json
cp /path/to/production/images/status.json $BACKUP_DIR/status_$DATE.json 