# Why Your AI Agent Forgets What Matters

**The memory problem no one talks about.**

---

You build an AI agent. You feed it your knowledge base. It indexes everything — 50,000 chunks of documentation, SOPs, research notes, conversation history. It can find anything by semantic similarity.

But it treats everything equally. A procedure you reference daily scores the same as a research note from January you never looked at again. Your agent's context fills up with technically-relevant-but-practically-useless content while the stuff you actually need gets buried.

Sound familiar?

---

## How Human Memory Actually Works

Your brain doesn't store memories equally. Neural pathways that get used frequently become stronger — literally easier for your brain to activate. The pathway to "how to drive a car" is a superhighway. The pathway to "that random fact from a documentary three years ago" is an overgrown trail.

The key insight: **nothing gets deleted.** The memory is still there. It's just harder to reach because the pathway weakened from disuse.

AI memory systems don't work this way. They store everything flat. Vector similarity is the only retrieval signal. There's no "this gets used constantly" vs "this has never been touched."

---

## The Salience Score

We built a scoring system that works like neural pathways:

```
SALIENCE = frequency + recency + authority + domain relevance
```

| Factor | What It Measures | Weight |
|--------|-----------------|--------|
| **Frequency** | How often is this recalled? | 37.5% |
| **Recency** | When was it last used? | 31.25% |
| **Authority** | How important is this source type? | 31.25% |
| **Domain** | Is this relevant to this specific agent? | Per-agent |

### Frequency

Simple counter. Every time your agent reads a file, the count goes up. Files read 50 times in a month clearly matter more than files read once.

### Recency

Exponential decay with a ~14-day half-life. A file used yesterday scores 0.95. A file not touched in a month scores 0.22. Three months: 0.01.

Nothing gets deleted. If you recall it again, it snaps right back up. Just like your brain — that random fact comes flooding back when someone mentions it.

### Authority

Not all knowledge sources are created equal. A correction from the owner is worth more than a random research note:

| Source | Authority | Why |
|--------|-----------|-----|
| Owner corrections | 0.9 | You cared enough to correct the agent |
| Codified decisions | 0.85 | Settled choices with rationale |
| Core reference files | 0.8 | Mission, offer, audience, voice |
| Domain knowledge | 0.6 | Important but broad |
| Research | 0.5 | May or may not lead to action |
| Conversation chunks | 0.2 | Raw bulk |

### Domain Relevance

If you run multiple agents, each one gets a filtered view. Your operations agent doesn't need clinical files clogging its context. Your clinical agent doesn't need marketing workflows. Each agent sees its domain files boosted, everything else available but not prioritized.

---

## What Changes

**Before salience:** Agent searches "workflow" → gets 10 results ranked by vector similarity. A rarely-used doc chunk scores the same as the workflow pattern you correct agents about weekly.

**After salience:** Same search → the correction you've reinforced 12 times (0.9 authority, high frequency) surfaces first. The untouched doc chunk drops to position 8.

Over time, the system learns what your operations actually use. The important stuff stands out. The rest fades to background — still searchable, never deleted, just not wasting your context window.

---

## The Cross-Agent Signal

If you run multiple agents across different domains, there's a bonus: cross-agent recall tracking.

When your operations agent AND your domain agent both recall the same fact, that's a signal. It means the information crosses domain boundaries — it's structurally important to your business, not just one department.

Chunks recalled by 3+ agents get a 1.5x boost. Two agents: 1.2x. This surfaces the connective tissue of your operations — the facts that hold everything together.

---

## How It's Built

The entire system is a SQLite database + a few Python scripts:

```
scripts/salience/
├── db.py               # Database + scoring formula
├── seed.py             # Index files across repos
├── track.py            # Parse session logs for recalls
├── generate_context.py # Write SALIENCE-CONTEXT.md
├── deploy_iris.py      # Push to all agents (domain-filtered)
├── cli.py              # Manual operations
├── sync.sh             # Run everything
└── salience.db         # The database
```

It runs alongside your existing memory system — doesn't replace anything. Vector search still finds candidates. Salience re-ranks them by real-world usage. Lossless Claw still preserves everything. Salience just tells you what to look at first.

Syncs automatically: every 30 minutes via cron + on every git commit via post-commit hook. Each agent gets a domain-filtered `SALIENCE-CONTEXT.md` at session start.

**To undo:** Delete the folder. That's it. Zero impact on anything else.

---

## Origin

This concept came from [SpazTaz](https://github.com/spastasm) during an [Alex Finn](https://x.com/alexfinndev) Vibe Code Academy bootcamp (March 2026). He described building a frequency-based memory scoring system modeled on human neurology — the more a memory pathway is used, the stronger it becomes.

Another community member added the idea of user-dictated relevance weighting — not just frequency, but human judgment about what matters.

We combined both ideas, added recency decay, authority scoring, and cross-agent signals, and built it as a portable tool that works with Claude Code and OpenClaw.

---

## Try It

```bash
git clone https://github.com/PerformanceOD/community-tools.git
cd your-repo
bash path/to/community-tools/salience-memory/install.sh
```

One command to install. One command to undo.

---

*Build it. Run it. Break it. Fix it. Share it.*
