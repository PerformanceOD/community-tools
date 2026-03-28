#!/bin/bash
# Salience Memory — Portable Installer
# Run from your business repo root: bash community-tools/salience-memory/install.sh

set -e

echo "=== Salience Memory Installer ==="
echo ""

# Detect repo root
REPO_ROOT="$(pwd)"
if [ ! -d "$REPO_ROOT/.git" ]; then
    echo "Error: Run this from your git repo root."
    exit 1
fi
echo "Repo: $REPO_ROOT"

# Create scripts directory
SALIENCE_DIR="$REPO_ROOT/scripts/salience"
mkdir -p "$SALIENCE_DIR"

# Copy source files
TOOL_DIR="$(cd "$(dirname "$0")" && pwd)"
for f in db.py seed.py track.py generate_context.py deploy_iris.py cli.py sync.sh .gitignore; do
    if [ -f "$TOOL_DIR/src/$f" ]; then
        cp "$TOOL_DIR/src/$f" "$SALIENCE_DIR/"
    elif [ -f "$REPO_ROOT/scripts/salience/$f" ]; then
        echo "  $f already exists, keeping yours"
    else
        echo "  Warning: $f not found in package"
    fi
done
chmod +x "$SALIENCE_DIR/sync.sh" 2>/dev/null

echo ""
echo "Source files installed to scripts/salience/"

# Configure repos to scan
echo ""
echo "Which repos should salience track? Enter absolute paths, one per line."
echo "Press Enter on empty line when done."
echo "(Default: current repo only)"
echo ""

REPOS=""
while true; do
    read -p "Repo path (or Enter to finish): " repo_path
    if [ -z "$repo_path" ]; then
        break
    fi
    if [ -d "$repo_path" ]; then
        REPOS="$REPOS|$repo_path"
    else
        echo "  Path not found: $repo_path"
    fi
done

if [ -z "$REPOS" ]; then
    REPOS="$REPO_ROOT"
fi

echo ""
echo "Tracked repos: $REPOS"

# Initialize database
echo ""
echo "Initializing database..."
cd "$SALIENCE_DIR"
python3 -c "from db import init_db; init_db()"
python3 seed.py

# Generate first context file
echo ""
echo "Generating initial SALIENCE-CONTEXT.md..."
python3 generate_context.py 2>/dev/null && echo "  Done" || echo "  Skipped (configure output path in generate_context.py)"

# Optional: post-commit hook
echo ""
read -p "Add post-commit hook? (syncs on every commit) [y/N]: " add_hook
if [ "$add_hook" = "y" ] || [ "$add_hook" = "Y" ]; then
    HOOK_PATH="$REPO_ROOT/.git/hooks/post-commit"
    if [ -f "$HOOK_PATH" ]; then
        echo "  post-commit hook already exists — appending salience sync"
        echo "" >> "$HOOK_PATH"
        echo "# Salience sync" >> "$HOOK_PATH"
        echo "(cd $SALIENCE_DIR && /bin/bash sync.sh >> /tmp/salience-sync.log 2>&1) &" >> "$HOOK_PATH"
    else
        cat > "$HOOK_PATH" << HOOKEOF
#!/bin/bash
# Salience sync — runs after every commit
(cd $SALIENCE_DIR && /bin/bash sync.sh >> /tmp/salience-sync.log 2>&1) &
HOOKEOF
        chmod +x "$HOOK_PATH"
    fi
    echo "  Post-commit hook installed"
fi

# Optional: cron
echo ""
read -p "Add cron job? (syncs every 30 min) [y/N]: " add_cron
if [ "$add_cron" = "y" ] || [ "$add_cron" = "Y" ]; then
    CRON_LINE="*/30 * * * * cd $SALIENCE_DIR && /bin/bash sync.sh >> /tmp/salience-sync.log 2>&1"
    (crontab -l 2>/dev/null | grep -v salience; echo "$CRON_LINE") | crontab -
    echo "  Cron job added (every 30 min)"
fi

echo ""
echo "=== Salience Memory installed ==="
echo ""
echo "Commands:"
echo "  cd scripts/salience && python3 cli.py score    # See rankings"
echo "  bash scripts/salience/sync.sh                  # Manual sync"
echo "  python3 scripts/salience/cli.py reset           # Start over"
echo ""
echo "To uninstall: rm -rf scripts/salience/ && crontab -l | grep -v salience | crontab -"
