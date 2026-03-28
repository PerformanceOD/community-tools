#!/usr/bin/env python3
"""
Salience Memory System — CLI
Usage:
    python3 cli.py seed              # Index all files across repos
    python3 cli.py score             # Show top salience scores
    python3 cli.py generate          # Generate SALIENCE-CONTEXT.md
    python3 cli.py recall <path>     # Record a file was recalled
    python3 cli.py boost <path>      # Manually boost a file's authority
    python3 cli.py decay             # Apply time-based decay
    python3 cli.py stats             # Show database statistics
    python3 cli.py reset             # Delete database and start fresh
"""

import sys
import os
import json

# Ensure we can import from this directory
sys.path.insert(0, os.path.dirname(__file__))

from db import (
    init_db, record_recall, boost_chunk, compute_salience,
    get_stats, get_cross_agent_boosts, DB_PATH
)


def cmd_seed():
    from seed import main as seed_main
    seed_main()


def cmd_score(limit=25):
    scores = compute_salience()
    if not scores:
        print("No chunks registered. Run: python3 cli.py seed")
        return

    print(f"\nTop {limit} by salience score:\n")
    print(f"{'Rank':<5} {'Score':<8} {'Recalls':<9} {'Auth':<6} {'Source':<15} {'File'}")
    print("-" * 100)
    for i, s in enumerate(scores[:limit], 1):
        path = s["file_path"]
        home = os.path.expanduser("~")
        path = path.replace(home, "~").replace("~/Documents/GitHub/", "")
        if len(path) > 50:
            path = "..." + path[-47:]
        print(f"{i:<5} {s['salience']:<8.4f} {s['recall_count']:<9} {s['authority']:<6.2f} {s['source_type']:<15} {path}")


def cmd_recall(path):
    # Expand to absolute path if relative
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    record_recall(path, agent_id="claude-code")
    print(f"Recorded recall: {path}")


def cmd_boost(path, amount=0.2):
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    boost_chunk(path, amount)
    print(f"Boosted authority by {amount}: {path}")


def cmd_decay():
    """Apply decay by recomputing scores (decay is inherent in the recency calculation)."""
    scores = compute_salience()
    decayed = [s for s in scores if s["recency"] < 0.3 and s["recall_count"] > 0]
    print(f"Computed salience for {len(scores)} chunks")
    print(f"  {len(decayed)} chunks have decayed recency (< 0.3)")
    if decayed:
        print(f"\n  Fading chunks:")
        for s in decayed[:10]:
            path = s["file_path"].replace(os.path.expanduser("~"), "~")
            print(f"    {s['salience']:.4f} | recency {s['recency']:.3f} | {path}")


def cmd_generate():
    from generate_context import main as gen_main
    gen_main()


def cmd_stats():
    stats = get_stats()
    print(f"\nSalience Database: {DB_PATH}")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Total recalls: {stats['total_recalls']}")
    print(f"\n  By source type:")
    for src, info in sorted(stats["chunks_by_source"].items(), key=lambda x: x[1]["count"], reverse=True):
        print(f"    {src:<15} {info['count']:>4} files  (avg authority: {info['avg_authority']})")
    print(f"\n  By repo:")
    for repo, count in sorted(stats["chunks_by_repo"].items(), key=lambda x: x[1], reverse=True):
        print(f"    {repo:<20} {count:>4} files")
    if stats["top_recalled"]:
        print(f"\n  Most recalled:")
        for t in stats["top_recalled"][:5]:
            path = t["file"].replace(os.path.expanduser("~"), "~")
            print(f"    {t['recalls']:>4} recalls | auth {t['authority']:.2f} | {path}")


def cmd_reset():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Deleted {DB_PATH}")
    else:
        print("No database to delete.")
    print("Run 'python3 cli.py seed' to rebuild.")


def cmd_cross():
    boosts = get_cross_agent_boosts()
    if not boosts:
        print("No cross-agent signals yet.")
        return
    print("\nCross-Agent Signals (recalled by 2+ agents):\n")
    for row in boosts:
        path = row["chunk_id"].replace(os.path.expanduser("~"), "~")
        print(f"  {row['agent_spread']} agents, {row['total_recalls']} recalls: {path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "seed":
        cmd_seed()
    elif cmd == "score":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 25
        cmd_score(limit)
    elif cmd == "recall":
        if len(sys.argv) < 3:
            print("Usage: cli.py recall <file_path>")
            return
        cmd_recall(sys.argv[2])
    elif cmd == "boost":
        if len(sys.argv) < 3:
            print("Usage: cli.py boost <file_path> [amount]")
            return
        amount = float(sys.argv[3]) if len(sys.argv) > 3 else 0.2
        cmd_boost(sys.argv[2], amount)
    elif cmd == "decay":
        cmd_decay()
    elif cmd == "generate":
        cmd_generate()
    elif cmd == "stats":
        cmd_stats()
    elif cmd == "reset":
        cmd_reset()
    elif cmd == "cross":
        cmd_cross()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
