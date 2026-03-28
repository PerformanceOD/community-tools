#!/usr/bin/env python3
"""
Salience Memory System — Auto Tracker
Parses Claude Code session logs and Iris JSONL conversation logs
to automatically record file recalls. Run at end of session or via cron.

Usage:
    python3 track.py                    # Track all sources
    python3 track.py --cc-only          # Claude Code sessions only
    python3 track.py --iris-only        # Iris agent logs only
"""

import json
import os
import sys
import glob
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from db import init_db, record_recall, register_chunk, classify_source, get_conn

# State file to track what we've already processed
STATE_FILE = os.path.join(os.path.dirname(__file__), ".track_state.json")

# Claude Code session logs
CC_PROJECT_DIR = os.path.expanduser(
    "~/.claude/projects/-Users-ericr-bang-Documents-GitHub-performance-od"
)

# Iris agent session logs (via SSH)
IRIS_HOST = "iris@iriss-mac-studio"
IRIS_AGENTS = {
    "iris": "main",
    "netra": "eyecare",
    "amara": "aesthetics",
    "maya": "softmkt",
    "bodha": "vt",
    "igor": "igor",
    "vani": "vani",
}

# Paths worth tracking (files that contribute to knowledge)
TRACKABLE_PATTERNS = [
    "/reference/",
    "/research/",
    "/decisions/",
    "/memory/",
    "CLAUDE.md",
    "MEMORY.md",
    "agent_notes.md",
    "FEEDBACK-LOG.md",
    "SHARED-RULES.md",
    "/domain/",
    "/core/",
    "/proof/",
    "/offers/",
    "/ops/",
]

# Paths to ignore
IGNORE_PATTERNS = [
    "/tmp/",
    "node_modules",
    "__pycache__",
    ".git/",
    "/scripts/salience/",  # Don't track ourselves
    ".jsonl",  # Don't track log files
    "/sessions/",
]


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"cc_last_processed": {}, "iris_last_processed": {}}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def is_trackable(path: str) -> bool:
    """Should we track recalls of this file?"""
    if any(p in path for p in IGNORE_PATTERNS):
        return False
    if any(p in path for p in TRACKABLE_PATTERNS):
        return True
    return False


def track_claude_code_sessions(state: dict) -> int:
    """Parse Claude Code JSONL session logs for Read/Grep tool calls."""
    if not os.path.exists(CC_PROJECT_DIR):
        print("  Claude Code project dir not found")
        return 0

    jsonl_files = sorted(glob.glob(os.path.join(CC_PROJECT_DIR, "*.jsonl")))
    processed = state.get("cc_last_processed", {})
    total_recalls = 0

    for jsonl_path in jsonl_files:
        filename = os.path.basename(jsonl_path)
        file_size = os.path.getsize(jsonl_path)

        # Skip if already fully processed (same size = no new data)
        if processed.get(filename) == file_size:
            continue

        last_offset = processed.get(filename, 0) if isinstance(processed.get(filename), int) else 0
        recalls_this_file = 0

        try:
            with open(jsonl_path) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("type") != "assistant":
                            continue

                        content = entry.get("message", {}).get("content", [])
                        if not isinstance(content, list):
                            continue

                        for c in content:
                            if not isinstance(c, dict) or c.get("type") != "tool_use":
                                continue

                            name = c.get("name", "")
                            inp = c.get("input", {})

                            # Extract file paths from different tool types
                            paths = []
                            if name == "Read" and "file_path" in inp:
                                paths.append(inp["file_path"])
                            elif name == "Grep" and "path" in inp:
                                paths.append(inp["path"])
                            elif name == "Glob" and "path" in inp:
                                paths.append(inp["path"])

                            for path in paths:
                                if is_trackable(path) and os.path.isfile(path):
                                    # Register if new
                                    register_chunk(path)
                                    record_recall(path, agent_id="claude-code")
                                    recalls_this_file += 1

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"  Error reading {filename}: {e}")
            continue

        processed[filename] = file_size
        total_recalls += recalls_this_file

        if recalls_this_file > 0:
            print(f"  CC session {filename[:12]}...: {recalls_this_file} recalls")

    state["cc_last_processed"] = processed
    return total_recalls


def track_iris_agents(state: dict) -> int:
    """Parse Iris OpenClaw JSONL logs for memory_recall and file reads."""
    processed = state.get("iris_last_processed", {})
    total_recalls = 0

    for agent_name, agent_dir in IRIS_AGENTS.items():
        # Get list of session files from Iris
        try:
            result = subprocess.run(
                ["ssh", IRIS_HOST,
                 f"ls -1 ~/.openclaw/agents/{agent_dir}/sessions/*.jsonl 2>/dev/null | tail -5"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                continue

            session_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

        except (subprocess.TimeoutExpired, Exception):
            print(f"  {agent_name}: SSH failed")
            continue

        for remote_path in session_files:
            filename = os.path.basename(remote_path)
            state_key = f"{agent_name}:{filename}"

            # Get file size to check if already processed
            try:
                size_result = subprocess.run(
                    ["ssh", IRIS_HOST, f"stat -f%z '{remote_path}' 2>/dev/null"],
                    capture_output=True, text=True, timeout=5
                )
                remote_size = int(size_result.stdout.strip()) if size_result.returncode == 0 else 0
            except:
                continue

            if processed.get(state_key) == remote_size:
                continue

            # Read the JSONL from Iris
            try:
                cat_result = subprocess.run(
                    ["ssh", IRIS_HOST, f"cat '{remote_path}'"],
                    capture_output=True, text=True, timeout=30
                )
                if cat_result.returncode != 0:
                    continue
            except subprocess.TimeoutExpired:
                print(f"  {agent_name}/{filename}: timeout reading")
                continue

            recalls_this = 0
            for line in cat_result.stdout.split("\n"):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)

                    # Look for memory_recall tool calls
                    content = entry.get("message", {}).get("content", [])
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "tool_use":
                                name = c.get("name", "")
                                if "memory" in name.lower() or "recall" in name.lower():
                                    # Memory recall — track query
                                    inp = c.get("input", {})
                                    query = inp.get("query", inp.get("search", ""))
                                    if query:
                                        # We can't map to exact chunks here, but we log the recall
                                        pass

                    # Look for exec calls that read files (cat, repo-search.sh results)
                    if isinstance(content, str) and "/Users/iris/" in content:
                        # Extract file paths from output
                        for word in content.split():
                            if word.startswith("/Users/iris/") and word.endswith(".md"):
                                # Map Iris paths to local paths
                                local_path = word.replace(
                                    "/Users/iris/performance-od",
                                    os.path.expanduser("~/Documents/GitHub/performance-od")
                                ).replace(
                                    "/Users/iris/iva_eyecare",
                                    os.path.expanduser("~/Documents/GitHub/iva_eyecare")
                                ).replace(
                                    "/Users/iris/iva-aesthetics",
                                    os.path.expanduser("~/Documents/GitHub/iva-aesthetics")
                                )
                                if is_trackable(local_path):
                                    register_chunk(local_path)
                                    record_recall(local_path, agent_id=agent_name)
                                    recalls_this += 1

                except json.JSONDecodeError:
                    continue

            processed[state_key] = remote_size
            total_recalls += recalls_this

            if recalls_this > 0:
                print(f"  {agent_name}/{filename[:12]}...: {recalls_this} recalls")

    state["iris_last_processed"] = processed
    return total_recalls


def main():
    init_db()
    state = load_state()
    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"

    print(f"[salience track] {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    cc_recalls = 0
    iris_recalls = 0

    if mode in ("--all", "--cc-only"):
        print("Scanning Claude Code sessions...")
        cc_recalls = track_claude_code_sessions(state)

    if mode in ("--all", "--iris-only"):
        print("Scanning Iris agent logs...")
        iris_recalls = track_iris_agents(state)

    save_state(state)

    total = cc_recalls + iris_recalls
    if total > 0:
        print(f"\nRecorded {total} recalls (CC: {cc_recalls}, Iris: {iris_recalls})")
    else:
        print("\nNo new recalls found.")


if __name__ == "__main__":
    main()
