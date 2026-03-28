"""
Salience Memory System — Context Generator
Produces SALIENCE-CONTEXT.md files for Claude Code and Iris agents.
Top-ranked chunks by salience score get surfaced at session start.
"""

import os
from datetime import datetime
from db import compute_salience, get_cross_agent_boosts, get_stats

# Output targets
CLAUDE_CODE_OUTPUT = os.path.expanduser(
    "~/.claude/projects/-Users-ericr-bang-Documents-GitHub-performance-od/memory/SALIENCE-CONTEXT.md"
)

# Iris agent workspaces (for future SSH deployment)
IRIS_WORKSPACES = {
    "iris": "~/.openclaw/workspace/",
    "netra": "~/.openclaw/workspace-eyecare/",
    "amara": "~/.openclaw/workspace-aesthetics/",
    "maya": "~/.openclaw/workspace-softmkt/",
    "bodha": "~/.openclaw/workspace-vt/",
    "igor": "~/.openclaw/workspace-igor/",
    "vani": "~/.openclaw/workspace-vani/",
}

TOP_N = 25  # Number of high-salience items to surface


def shorten_path(path: str) -> str:
    """Make paths readable."""
    home = os.path.expanduser("~")
    path = path.replace(home, "~")
    # Shorten common prefixes
    path = path.replace("~/Documents/GitHub/", "")
    path = path.replace("~/.claude/projects/-Users-ericr-bang-Documents-GitHub-performance-od/memory/", "memory:")
    return path


def generate_claude_code_context():
    """Generate SALIENCE-CONTEXT.md for Claude Code sessions."""
    scores = compute_salience()
    stats = get_stats()
    cross_agent = get_cross_agent_boosts()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# Salience Context (auto-generated {now})",
        "",
        f"Tracked: {stats['total_chunks']} files | Total recalls: {stats['total_recalls']}",
        "",
        "## Highest-Salience Files (load these first when relevant)",
        "",
        "| Rank | File | Source | Score | Recalls | Authority |",
        "|------|------|--------|-------|---------|-----------|",
    ]

    for i, s in enumerate(scores[:TOP_N], 1):
        short = shorten_path(s["file_path"])
        lines.append(
            f"| {i} | {short} | {s['source_type']} | {s['salience']:.3f} | {s['recall_count']} | {s['authority']:.2f} |"
        )

    # Cross-agent section
    if cross_agent:
        lines.extend([
            "",
            "## Cross-Agent Signals (recalled by multiple agents)",
            "",
        ])
        for row in cross_agent[:10]:
            short = shorten_path(row["chunk_id"])
            lines.append(f"- **{short}** — {row['agent_spread']} agents, {row['total_recalls']} total recalls")

    # Decaying section (low salience, previously high)
    low_but_recalled = [s for s in scores if s["recall_count"] > 3 and s["salience"] < 0.2]
    if low_but_recalled:
        lines.extend([
            "",
            "## Decaying (previously active, fading)",
            "",
        ])
        for s in low_but_recalled[:5]:
            short = shorten_path(s["file_path"])
            lines.append(f"- {short} — {s['recall_count']} recalls but salience {s['salience']:.3f}")

    lines.append("")
    return "\n".join(lines)


def write_claude_code():
    """Write context file for Claude Code."""
    content = generate_claude_code_context()
    os.makedirs(os.path.dirname(CLAUDE_CODE_OUTPUT), exist_ok=True)
    with open(CLAUDE_CODE_OUTPUT, "w") as f:
        f.write(content)
    print(f"Wrote {CLAUDE_CODE_OUTPUT}")
    print(f"  ({len(content)} chars, will be loaded at session start)")


def main():
    write_claude_code()
    print("\nTo deploy to Iris agents, run:")
    print("  python3 scripts/salience/deploy_iris.py")


if __name__ == "__main__":
    main()
