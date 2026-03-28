#!/bin/bash
# Salience sync — tracks recalls, recomputes scores, deploys to agents
# Run manually: bash scripts/salience/sync.sh
# Or via cron: every 30 min, end of session, etc.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Salience Sync $(date '+%Y-%m-%d %H:%M') ==="

# 1. Track new recalls from all sessions
echo ""
python3 track.py

# 2. Pick up any new files
echo ""
echo "Checking for new files..."
python3 seed.py 2>&1 | grep -E "^  |^Total"

# 3. Regenerate context for Claude Code
echo ""
python3 generate_context.py 2>&1

# 4. Deploy to Iris agents
echo ""
python3 deploy_iris.py 2>&1

echo ""
echo "=== Salience sync complete ==="
