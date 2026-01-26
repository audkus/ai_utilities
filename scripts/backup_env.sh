#!/bin/bash
# Backup .env file to prevent accidental loss

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
BACKUP_DIR="$HOME/.env_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup .env if it exists
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$BACKUP_DIR/.env_backup_$TIMESTAMP"
    echo "✅ .env backed up to: $BACKUP_DIR/.env_backup_$TIMESTAMP"
    
    # Keep only last 10 backups
    cd "$BACKUP_DIR"
    ls -t .env_backup_* | tail -n +11 | xargs -r rm
    echo "🧹 Cleaned old backups (keeping last 10)"
else
    echo "❌ No .env file found at: $ENV_FILE"
fi

# List current backups
echo ""
echo "📋 Current backups:"
ls -la "$BACKUP_DIR"/.env_backup_* 2>/dev/null || echo "No backups found"
