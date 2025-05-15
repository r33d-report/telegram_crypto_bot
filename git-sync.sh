#!/bin/bash

# Auto Git Sync Script
echo "🔄 Syncing with GitHub..."

# Add changes
git add .

# Commit with timestamp
git commit -m "🔁 Auto-sync $(date)" || echo "✅ Nothing to commit."

# Pull latest changes before pushing
git pull origin main --rebase

# Push changes
git push origin main
