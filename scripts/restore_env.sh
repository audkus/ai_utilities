#!/bin/bash
# Restore .env from backup

BACKUP_DIR="$HOME/.env_backups"
PROJECT_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
ENV_FILE="$PROJECT_ROOT/.env"

echo "📋 Available .env backups:"
ls -la "$BACKUP_DIR"/.env_backup_* 2>/dev/null | nl

if [ $? -ne 0 ]; then
    echo "❌ No backups found in $BACKUP_DIR"
    exit 1
fi

echo ""
read -p "Enter backup number to restore (or 'q' to quit): " choice

if [[ "$choice" == "q" ]]; then
    echo "👋 Cancelled"
    exit 0
fi

if [[ "$choice" =~ ^[0-9]+$ ]]; then
    backup_file=$(ls -t "$BACKUP_DIR"/.env_backup_* | sed -n "${choice}p")
    if [ -n "$backup_file" ] && [ -f "$backup_file" ]; then
        cp "$backup_file" "$ENV_FILE"
        echo "✅ Restored .env from: $backup_file"
        echo "🔒 Permissions set to read/write for owner only"
        chmod 600 "$ENV_FILE"
    else
        echo "❌ Invalid backup number: $choice"
        exit 1
    fi
else
    echo "❌ Invalid input. Please enter a number."
    exit 1
fi
