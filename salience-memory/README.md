# Salience Memory

A memory scoring system for AI agents and Claude Code that tracks what knowledge actually gets used. Frequently-accessed files surface first. Unused knowledge fades naturally but never deletes.

> Built at IVA (Integrated Vision & Aesthetics). Part of the PerformanceOD / Open Source OD / OSOD community tools.

## The Problem

AI agents treat all memory equally. A file you reference 50 times a month scores the same as something stored once and never touched again. Context windows fill up with low-value content while high-value knowledge gets buried.

## How It Works

Every file in your repos gets a **salience score** based on four factors:

| Factor | Weight | What It Measures |
|--------|--------|------------------|
| **Frequency** | 37.5% | How often is this file recalled/read? |
| **Recency** | 31.25% | When was it last used? (exponential decay, ~14-day half-life) |
| **Authority** | 31.25% | Source type weight — corrections > decisions > reference > research |
| **Domain relevance** | Per-agent | Each agent gets files from their domain boosted |

The system generates a `SALIENCE-CONTEXT.md` file that your AI loads at session start — the most important stuff is always in context.

## What You Need

- Python 3.8+
- One or more git repos with markdown knowledge files
- Optional: SSH access to a remote machine running OpenClaw agents
- Optional: cron for automatic updates

## Install

```bash
# From your business repo root:
bash community-tools/salience-memory/install.sh
```

The install script will:
1. Ask for your repo paths
2. Create `scripts/salience/` in your repo
3. Index all your files
4. Generate your first SALIENCE-CONTEXT.md
5. Optionally set up cron and post-commit hooks

## Commands

```bash
cd scripts/salience

python3 cli.py seed              # Index all files across repos
python3 cli.py score             # Show top salience scores
python3 cli.py score 50          # Show top 50
python3 cli.py recall <path>     # Record a file was used
python3 cli.py boost <path>      # Mark something as important
python3 cli.py decay             # Show what's fading
python3 cli.py generate          # Regenerate SALIENCE-CONTEXT.md
python3 cli.py stats             # Database overview
python3 cli.py cross             # Cross-agent signals
python3 cli.py reset             # Start fresh
```

Full sync (track + seed + generate + deploy):
```bash
bash scripts/salience/sync.sh
```

## How Scoring Works

**Authority defaults** (adjustable):

| Source Type | Default | Why |
|------------|---------|-----|
| Feedback/corrections | 0.9 | You cared enough to correct — highest signal |
| Decisions | 0.85 | Codified choices |
| Core reference | 0.8 | Foundational files (soul, offer, audience, voice) |
| Agent notes | 0.7 | Agent learned from experience |
| Domain knowledge | 0.6 | Important but broad |
| Research | 0.5 | May or may not lead to action |
| Daily logs | 0.3 | Session-specific context |
| Conversations | 0.2 | Raw bulk |

**Recency decay:** Half-life of ~14 days. A file not recalled in a month scores 0.22 recency. In 3 months: 0.01. If re-recalled, it snaps back up immediately.

**Cross-agent boost:** If multiple agents recall the same file, it gets a 1.2x-1.5x multiplier. Cross-domain importance is a strong signal.

## Multi-Agent Deployment

If you run OpenClaw agents, each agent gets a domain-filtered `SALIENCE-CONTEXT.md`:
- Clinical agents see clinical files boosted
- Marketing agents see marketing files boosted
- Universal files (corrections, core) go to everyone

Configure agent domains in `deploy_iris.py` → `AGENT_DOMAINS` dict.

## Uninstall

```bash
# Remove the database
python3 scripts/salience/cli.py reset

# Remove the scripts
rm -rf scripts/salience/

# Remove generated context
rm -f .claude/projects/*/memory/SALIENCE-CONTEXT.md

# Remove cron (if added)
crontab -l | grep -v salience | crontab -

# Remove post-commit hook (if added)
rm -f .git/hooks/post-commit
```

Zero impact on your repos, memory, or agents. Everything else stays exactly as it was.

## Origin

Concept: **SpazTaz** (GitHub: spastasm) — described frequency-based memory scoring modeled on human neurology at an Alex Finn Vibe Code Academy bootcamp (March 2026). Another community member added the relevance/authority weighting idea.

Implementation: Built at IVA by Eric Bang + Claude Code. Adds authority scoring, exponential decay, cross-agent signals, and domain-filtered deployment on top of the original frequency concept.
