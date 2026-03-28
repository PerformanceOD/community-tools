"""
Salience Memory System — Seed Script
Scans all repos and Claude Code memory to register chunks with initial authority scores.
Run once to initialize, then re-run anytime to pick up new files.
"""

import os
import glob
from db import init_db, register_chunk, get_stats

# All repos to scan
REPOS = {
    "performance-od": os.path.expanduser("~/Documents/GitHub/performance-od"),
    "iva_eyecare": os.path.expanduser("~/Documents/GitHub/iva_eyecare"),
    "iva-aesthetics": os.path.expanduser("~/Documents/GitHub/iva-aesthetics"),
}

# Claude Code memory
CLAUDE_MEMORY = os.path.expanduser(
    "~/.claude/projects/-Users-ericr-bang-Documents-GitHub-performance-od/memory"
)

# File patterns to index
PATTERNS = [
    "reference/**/*.md",
    "research/**/*.md",
    "decisions/**/*.md",
    "CLAUDE.md",
    "content/**/*.md",
]

MEMORY_PATTERNS = [
    "*.md",
]

# Skip patterns
SKIP = [
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
]


def should_skip(path: str) -> bool:
    return any(s in path for s in SKIP)


def scan_repo(repo_name: str, repo_path: str):
    """Scan a repo for indexable files."""
    count = 0
    for pattern in PATTERNS:
        full_pattern = os.path.join(repo_path, pattern)
        for filepath in glob.glob(full_pattern, recursive=True):
            if should_skip(filepath):
                continue
            register_chunk(filepath)
            count += 1
    return count


def scan_claude_memory(memory_path: str):
    """Scan Claude Code memory files."""
    count = 0
    if not os.path.exists(memory_path):
        return 0
    for pattern in MEMORY_PATTERNS:
        full_pattern = os.path.join(memory_path, pattern)
        for filepath in glob.glob(full_pattern, recursive=True):
            if should_skip(filepath):
                continue
            register_chunk(filepath)
            count += 1
    return count


def main():
    print("Initializing salience database...")
    init_db()

    total = 0
    for repo_name, repo_path in REPOS.items():
        if os.path.exists(repo_path):
            count = scan_repo(repo_name, repo_path)
            print(f"  {repo_name}: {count} files indexed")
            total += count
        else:
            print(f"  {repo_name}: NOT FOUND at {repo_path}")

    memory_count = scan_claude_memory(CLAUDE_MEMORY)
    print(f"  claude-memory: {memory_count} files indexed")
    total += memory_count

    print(f"\nTotal: {total} files registered")

    # Show stats
    stats = get_stats()
    print(f"\nDatabase stats:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  By source type:")
    for src, info in sorted(stats["chunks_by_source"].items()):
        print(f"    {src}: {info['count']} files (avg authority: {info['avg_authority']})")
    print(f"  By repo:")
    for repo, count in sorted(stats["chunks_by_repo"].items()):
        print(f"    {repo}: {count} files")


if __name__ == "__main__":
    main()
