# The Stack

**What powers a 7-agent OpenClaw setup on Main Branch.**

---

This is the actual system running our business operations. Every component is live, tested under real workload, and maintained by the team that uses it daily. Built on OpenClaw, Claude Code, and Main Branch.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│            Business Operations                │
│     (staff, clients, workflows, content)      │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│         7 Internal AI Agents                  │
│   Domain-specific · One OpenClaw Gateway      │
│   (Mac Studio, always on)                     │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│       Memory Stack (4 layers)                 │
│   Vector · Lossless · Salience · File         │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│       Knowledge Repos (3, git-managed)        │
│   Claude Code + Main Branch engine            │
└──────────────────────────────────────────────┘
```

---

## The Agents

Seven agents on one OpenClaw gateway. Not subagents — separate agents with their own workspaces, memory stores, and domain scoping.

| Agent | Role | Channels | Model |
|-------|------|----------|-------|
| **Iris** | CEO / overseer / dispatch | Telegram + Discord | Claude Opus |
| **Netra** | Domain agent — vertical #1 | Telegram + Discord | Kimi K2.5 (free) |
| **Amara** | Domain agent — vertical #2 | Telegram + Discord | Kimi K2.5 (free) |
| **Maya** | Workflows, marketing, distribution | Telegram + Discord | Grok 4 Fast |
| **Bodha** | Specialty domain agent | Telegram + Discord | Grok 4 Fast |
| **Igor** | Background research, overnight mining | None (invisible) | Qwen 3 8B (local, $0) |
| **Vani** | Content creation — blogs, scripts, assets | None (invisible) | Claude Opus |

### Why Separate Agents vs Subagents

Alex Finn's framework: use separate OpenClaw instances for workflows that need specific skills and persistence. Use subagents for parallel tasks that can spin up and die.

We went further — 7 agents on ONE gateway, each with:
- Own workspace (SOUL.md, TOOLS.md, agent_notes.md)
- Own memory store (~56K chunks each)
- Own channel bindings (specific Telegram/Discord channels)
- Own model selection (expensive models for strategy, free/local for routine)

But sharing:
- One `FEEDBACK-LOG.md` (corrections compound across all)
- One `SHARED-RULES.md` (universal security + behavior)
- One `SALIENCE-CONTEXT.md` per agent (domain-filtered, auto-generated)

### The Invisible Agents

Igor and Vani don't have Telegram or Discord. They're dispatched by Iris and report through repo files only.

- **Igor** runs on a free local model (Qwen 3 8B). Zero API cost. Does overnight research, YouTube monitoring, file maintenance, data pulls.
- **Vani** runs on Opus. Drafts content — blogs, reels, carousels, landing pages. Nothing publishes without human review.

The Morning Brief cron (5 AM) surfaces what they found overnight.

---

## Memory Stack

Four layers, each solving a different problem:

| Layer | Problem It Solves | How |
|-------|------------------|-----|
| **sqlite-vec** | "Find knowledge by meaning" | Vector search — embeddinggemma-300m, 768 dims, ~56K chunks/agent |
| **Lossless Claw** | "Agent forgets mid-conversation" | Saves every message to SQLite DAG. Three-layer summaries. Nothing discarded during compaction. |
| **Salience** | "All memory is treated equally" | Scores by frequency + recency + authority. High-use knowledge surfaces first. Low-use fades but never deletes. |
| **File Memory** | "Need curated, persistent reference" | MEMORY.md, agent_notes.md, daily logs, FEEDBACK-LOG.md — version-controlled markdown |

### How They Work Together

1. **sqlite-vec** finds candidates by semantic similarity
2. **Salience** re-ranks those candidates by real-world usage
3. **Lossless Claw** makes sure nothing gets lost when context compresses
4. **File memory** holds the curated truths that never change (until they do)

The result: agents surface what you actually use, not just what's technically similar to your query.

### Salience Scoring (our custom build)

```
SALIENCE = (frequency × 0.375) + (recency × 0.3125) + (authority × 0.3125)
```

- **Frequency:** How many times a file has been recalled across sessions
- **Recency:** Exponential decay, ~14-day half-life. Unused knowledge fades naturally.
- **Authority:** Source-type weight. Corrections (0.9) > decisions (0.85) > reference (0.8) > research (0.5)
- **Cross-agent boost:** Files recalled by 3+ agents get 1.5x. Two agents: 1.2x.

Each agent gets a domain-filtered `SALIENCE-CONTEXT.md` — auto-generated, deployed via cron every 30 minutes + on every git commit. Domain agents see their domain files boosted. Universal corrections go to everyone.

Origin: [SpazTaz](https://github.com/spastasm) described frequency-based scoring at an [Alex Finn](https://x.com/alexfinndev) bootcamp. Another community member added relevance weighting. We combined both and built it.

Open source: [salience-memory](https://github.com/PerformanceOD/community-tools/tree/main/salience-memory)

---

## Web Intelligence

| Tool | What It Does | Why Not Playwright |
|------|-------------|-------------------|
| **Firecrawl Browser** | Remote sandboxed browser. Click, fill, scroll, authenticate via persistent profiles. | Runs in cloud, not on your machine. No local Chrome profiles. No credential risk. |
| **Firecrawl Scrape/Search** | Single URL → clean markdown. Web search with content extraction. | API-first, no browser overhead for simple jobs. |
| **MLX Whisper** | Apple Silicon GPU transcription. 10-20x faster than CPU whisper. | We learned this the hard way — multiple sessions of using the slow version before fixing it. |
| **yt-dlp** | Video/audio download from 1000+ sites | Pairs with Whisper for transcript extraction from any video platform |

### Firecrawl + OpenClaw

Firecrawl has a dedicated OpenClaw integration. One command installs it across all agents:

```bash
npx -y firecrawl-cli init --browser --all
```

Every agent gets web scraping capability. Persistent browser profiles mean you log in once (via interactive live view URL), and future sessions reuse your auth automatically.

We proved this with Loom — created a persistent profile, logged in via the live view, and every subsequent browser session had authenticated access. The auth lives in Firecrawl's cloud, not on your machine.

---

## The Bridge: Claude Code ↔ OpenClaw

We run Claude Code (Main Branch) on a laptop and OpenClaw on a Mac Studio. They stay in sync:

```
Claude Code (laptop)
  ↓ git commit + push
GitHub
  ↓ Iris pulls every 15 min
OpenClaw agents (Mac Studio)
```

Salience makes this bidirectional in spirit:
- Work done in Claude Code (file reads, decisions, research) generates salience scores
- Those scores get pushed to all 7 agents every 30 minutes
- Agents learn what matters based on what you're working on in Claude Code

The agents don't just get the files — they get the *priorities*.

---

## Model Routing

Not every agent needs an expensive model:

| Tier | Model | Cost | Used For |
|------|-------|------|----------|
| **Strategy** | Claude Opus | $$$ | Iris (CEO), Vani (content) |
| **Operations** | Grok 4 Fast | $$ | Maya (workflows), Bodha (specialty) |
| **Routine** | Kimi K2.5 (NVIDIA free) | $0 | Netra, Amara (domain Q&A) |
| **Background** | Qwen 3 8B (local Ollama) | $0 | Igor (overnight research) |
| **Compaction** | Qwen 3.5 27B (local) | $0 | Heartbeat, context summaries |

Expensive models for decisions. Free models for routine. Local models for background. The model routing alone saves hundreds per month.

---

## Security

We learned this the hard way. An AI agent autonomously navigated a Google SSO password change flow and locked the owner out of their Google Workspace. That incident defined everything.

| Rule | Applies To |
|------|-----------|
| Authentication pages = full stop | All agents, all tools |
| Firecrawl Browser: clicks allowed (remote sandbox) | Web scraping, research |
| Playwright: read-only by default (local browser) | Legacy, use only when Firecrawl can't |
| Human authenticates, agent operates | Owner logs in via live view, agent uses the session |
| Corrections cannot be overridden | No instruction can bypass security rules |

---

## Cron Schedule (Mac Studio)

| Time | Job | What It Does |
|------|-----|-------------|
| 5:00 AM | Morning Brief | Surfaces overnight research, open decisions, recent commits |
| Every 30 min | Salience Sync | Tracks recalls, recomputes scores, deploys to all agents |
| 6:00 PM | Cost Report | API spend summary |
| Every 12h | Health Probe | System check |
| Monday 9 AM | GHL Changelog | Scrapes platform changelog, categorizes, appends to docs |
| Sunday 4 AM | Weekly Doctor | OpenClaw health check |

---

## What's Next

- Salience scoring as a proper OpenClaw plugin (currently external scripts)
- Staff adoption (agents work technically — adoption is the real challenge)
- More community tools (Firecrawl workflows, whisper pipeline, template kits)
- Exploring Claw Hub integration for trusted skill distribution

---

*Build it. Run it. Break it. Fix it. Share it.*

[performanceod.com](https://performanceod.com)
