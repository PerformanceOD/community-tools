#!/usr/bin/env python3
"""
Salience Memory System — Deploy to Iris Agents
Pushes salience scores + context files to all 7 OpenClaw agents on Iris.
Each agent gets a filtered view — their domain files ranked highest.

Run after generate_context.py, or standalone:
    python3 deploy_iris.py
"""

import os
import sys
import json
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from db import compute_salience, get_stats, get_cross_agent_boosts, DB_PATH

IRIS_HOST = "iris@iriss-mac-studio"
IRIS_WORKSPACE_ROOT = "/Users/iris/.openclaw"

# Agent → domain mapping (which files are most relevant to each agent)
AGENT_DOMAINS = {
    "iris": {
        "workspace": "workspace",
        "repos": ["performance-od"],
        "boost_paths": ["reference/core/", "reference/domain/ghl-", "reference/domain/agent-",
                        "decisions/", "reference/domain/competitive", "reference/domain/foxfire"],
        "description": "Strategy, dispatch, PerformanceOD — sees everything"
    },
    "netra": {
        "workspace": "workspace-eyecare",
        "repos": ["iva_eyecare"],
        "boost_paths": ["reference/domain/kanski", "reference/domain/eyelid", "reference/offers/",
                        "reference/domain/foxfire"],
        "description": "Clinical eyecare + Foxfire"
    },
    "amara": {
        "workspace": "workspace-aesthetics",
        "repos": ["iva-aesthetics"],
        "boost_paths": ["reference/domain/dermatology", "reference/domain/milady",
                        "reference/ops/"],
        "description": "Clinical aesthetics + AestheticsPro"
    },
    "maya": {
        "workspace": "workspace-softmkt",
        "repos": ["performance-od", "iva_eyecare", "iva-aesthetics"],
        "boost_paths": ["reference/domain/ghl-", "reference/domain/build-guides/",
                        "reference/domain/foxfire", "reference/domain/funnel"],
        "description": "GHL, marketing, workflows — cross-repo"
    },
    "bodha": {
        "workspace": "workspace-vt",
        "repos": ["iva_eyecare"],
        "boost_paths": ["reference/offers/vision-therapy", "reference/domain/sanet"],
        "description": "Vision therapy, Sanet methodology"
    },
    "igor": {
        "workspace": "workspace-igor",
        "repos": ["performance-od"],
        "boost_paths": ["research/", "reference/domain/"],
        "description": "Background research, overnight mining"
    },
    "vani": {
        "workspace": "workspace-vani",
        "repos": ["performance-od", "iva_eyecare", "iva-aesthetics"],
        "boost_paths": ["reference/core/voice", "reference/core/audience",
                        "reference/proof/", "reference/domain/build-guides/",
                        "reference/domain/content-strategy"],
        "description": "Content creation — voice, audience, angles"
    },
}

TOP_N = 20  # Per agent


def shorten_path(path: str) -> str:
    """Make paths readable for agents."""
    path = path.replace("/Users/ericr.bang/Documents/GitHub/", "~/")
    path = path.replace("/Users/ericr.bang/.claude/projects/-Users-ericr-bang-Documents-GitHub-performance-od/memory/", "CC-memory:")
    path = path.replace("/Users/iris/", "~/")
    return path


def is_relevant_to_agent(score_entry: dict, agent_config: dict) -> bool:
    """Check if a file is relevant to this agent's domain."""
    path = score_entry["file_path"]
    # Check repo match
    for repo in agent_config["repos"]:
        if repo in path:
            return True
    # Feedback and core files are relevant to all
    if score_entry["source_type"] in ("feedback", "core"):
        return True
    return False


def domain_boost(score_entry: dict, agent_config: dict) -> float:
    """Boost score for files in agent's domain."""
    path = score_entry["file_path"]
    for boost_path in agent_config["boost_paths"]:
        if boost_path in path:
            return 0.15  # Domain relevance boost
    return 0.0


def generate_agent_context(agent_id: str, agent_config: dict, all_scores: list) -> str:
    """Generate SALIENCE-CONTEXT.md tailored to a specific agent."""
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Filter and re-rank for this agent
    relevant = []
    for s in all_scores:
        if is_relevant_to_agent(s, agent_config):
            boosted_score = s["salience"] + domain_boost(s, agent_config)
            entry = dict(s)
            entry["agent_salience"] = round(min(1.0, boosted_score), 4)
            relevant.append(entry)

    relevant.sort(key=lambda x: x["agent_salience"], reverse=True)

    lines = [
        f"# Salience Context — {agent_id.capitalize()} (auto-generated {now})",
        f"",
        f"Domain: {agent_config['description']}",
        f"Tracked across all repos: {len(all_scores)} files | Relevant to you: {len(relevant)}",
        f"",
        f"## Your Highest-Priority Files",
        f"",
        f"| Rank | File | Score | Recalls | Why |",
        f"|------|------|-------|---------|-----|",
    ]

    for i, s in enumerate(relevant[:TOP_N], 1):
        short = shorten_path(s["file_path"])
        why = s["source_type"]
        if domain_boost(s, agent_config) > 0:
            why += " +domain"
        if s["recall_count"] > 0:
            why += f" +{s['recall_count']}recalls"
        lines.append(f"| {i} | {short} | {s['agent_salience']:.3f} | {s['recall_count']} | {why} |")

    # Cross-agent signals relevant to this agent
    cross = get_cross_agent_boosts()
    if cross:
        relevant_cross = [c for c in cross if is_relevant_to_agent(
            {"file_path": c["chunk_id"], "source_type": "unknown"}, agent_config)]
        if relevant_cross:
            lines.extend(["", "## Cross-Agent Signals", ""])
            for c in relevant_cross[:5]:
                short = shorten_path(c["chunk_id"])
                lines.append(f"- **{short}** — {c['agent_spread']} agents, {c['total_recalls']} recalls")

    lines.extend([
        "",
        f"*Scores reflect Eric's Claude Code session activity. Higher = more important right now.*",
        "",
    ])

    return "\n".join(lines)


def deploy_to_iris():
    """Push salience context files to all Iris agent workspaces."""
    print("Computing salience scores...")
    all_scores = compute_salience()

    if not all_scores:
        print("No scores computed. Run 'python3 cli.py seed' first.")
        return

    stats = get_stats()
    print(f"  {stats['total_chunks']} files tracked, {stats['total_recalls']} total recalls")

    # Generate and deploy for each agent
    success = 0
    for agent_id, config in AGENT_DOMAINS.items():
        context = generate_agent_context(agent_id, config, all_scores)
        workspace_path = f"{IRIS_WORKSPACE_ROOT}/{config['workspace']}"

        # Write to temp file and SCP
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(context)
            tmp_path = f.name

        target = f"{workspace_path}/SALIENCE-CONTEXT.md"
        result = subprocess.run(
            ["scp", tmp_path, f"{IRIS_HOST}:{target}"],
            capture_output=True, text=True
        )
        os.unlink(tmp_path)

        if result.returncode == 0:
            print(f"  {agent_id:<8} → {target}")
            success += 1
        else:
            print(f"  {agent_id:<8} FAILED: {result.stderr.strip()}")

    # Also push the salience DB itself for Iris-side queries
    result = subprocess.run(
        ["scp", DB_PATH, f"{IRIS_HOST}:/Users/iris/.openclaw/workspace/salience.db"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"\n  salience.db → Iris workspace")

    print(f"\nDeployed to {success}/{len(AGENT_DOMAINS)} agents")


def main():
    deploy_to_iris()


if __name__ == "__main__":
    main()
