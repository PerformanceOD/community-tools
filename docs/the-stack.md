# The Stack

**What powers a fully automated independent practice.**

---

This is not a pitch deck. This is the actual system running at IVA — Integrated Vision & Aesthetics — an independent eyecare and aesthetics practice. Every component listed here is live, tested with real patients, and maintained by the team that uses it daily.

---

## Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │         Practice Operations          │
                    │  (patients, staff, clinical, billing) │
                    └──────────┬──────────┬───────────────┘
                               │          │
                    ┌──────────▼──┐  ┌────▼──────────┐
                    │ Foxfire PMS  │  │ AestheticsPro  │
                    │ (eyecare)    │  │ (aesthetics)   │
                    └──────────┬──┘  └────┬──────────┘
                               │          │
              ┌────────────────▼──────────▼────────────────┐
              │              GoHighLevel                    │
              │   Marketing · Workflows · Communication    │
              │   Patient-facing AI (Eyela, Lumi)          │
              └────────────────┬───────────────────────────┘
                               │
              ┌────────────────▼───────────────────────────┐
              │          7 Internal AI Agents               │
              │   Knowledge · Research · Content · Ops     │
              │   (OpenClaw on Mac Studio)                  │
              └────────────────┬───────────────────────────┘
                               │
              ┌────────────────▼───────────────────────────┐
              │         Knowledge Repos (3)                 │
              │   performance-od · iva_eyecare ·            │
              │   iva-aesthetics                            │
              └────────────────────────────────────────────┘
```

---

## Layer by Layer

### 1. Practice Management

| System | Practice | Handles |
|--------|----------|---------|
| **Foxfire PMS** | Eyecare | Scheduling, billing, claims, clinical documentation, optical orders |
| **AestheticsPro** | Aesthetics | Appointments, charting, consent, treatment records |

Foxfire is the PMS that said yes. When 12 other eyecare PMS companies refused API access to independent practices, Foxfire — family-owned, doctor-friendly — opened the door. That decision is why this entire system exists.

### 2. Marketing + Communication

| Component | What It Does |
|-----------|-------------|
| **GoHighLevel** | CRM, SMS/email campaigns, funnels, workflow automation, social media, reputation management |
| **Drip campaigns** | Specialty-specific: dry eye, myopia, aesthetics, Ortho-K |
| **Voice AI** | Eyela (eyecare) and Lumi (aesthetics) — patient-facing, inside GHL |
| **Workflow triggers** | Post-exam "tag and go" — staff tags a specialty, entire follow-up sequence fires automatically |

GHL is the execution layer. Everything patient-facing runs through it. The internal AI agents never talk to patients — that's GHL's job.

### 3. Internal AI Agents

Seven agents on one OpenClaw gateway, each with its own domain expertise:

| Agent | Domain | Who Uses It | Model |
|-------|--------|-------------|-------|
| **Iris** | Strategy, dispatch, CEO | Eric (owner) | Claude Opus |
| **Netra** | Clinical eyecare, Foxfire | Clinical staff | Kimi K2.5 |
| **Amara** | Clinical aesthetics | Aesthetics staff | Kimi K2.5 |
| **Maya** | GHL, marketing, workflows | Everyone | Grok 4 Fast |
| **Bodha** | Vision therapy | VT staff | Grok 4 Fast |
| **Igor** | Background research | No one (invisible) | Qwen 3 8B (local) |
| **Vani** | Content creation | No one (invisible) | Claude Opus |

**The invisible agents** (Igor and Vani) run overnight. Igor mines research. Vani drafts content. Nothing publishes without human review. The Morning Brief surfaces what they found.

**The rule:** Corrections to one agent compound across all of them via a shared feedback log.

### 4. Memory Stack

| Layer | Purpose | Technology |
|-------|---------|------------|
| **Vector search** | Find knowledge by meaning | embeddinggemma-300m, sqlite-vec, 768 dims |
| **Lossless context** | Never lose mid-session information | Lossless Claw — SQLite DAG with layered summaries |
| **Salience scoring** | Surface what actually matters | Custom frequency + recency + authority scoring |
| **File memory** | Curated long-term reference | Version-controlled markdown (MEMORY.md, agent_notes.md) |
| **Cross-agent corrections** | One correction teaches all agents | FEEDBACK-LOG.md symlinked across all workspaces |

Each agent has ~56,000 indexed chunks spanning clinical protocols, marketing workflows, GHL documentation, and practice SOPs.

### 5. Knowledge Repos

Three git repositories. Three businesses. Shared where explicitly shared.

| Repo | Purpose | Contains |
|------|---------|----------|
| **performance-od** | Practice automation company | GHL docs, agent architecture, competitive research, frameworks, community tools |
| **iva_eyecare** | Eyecare practice | Clinical protocols, Foxfire workflows, specialty offers, patient education |
| **iva-aesthetics** | Aesthetics practice | Treatment protocols, device settings, consent forms, product knowledge |

Clinical knowledge stays separated. Marketing and business operations are shared. A dry eye protocol in iva_eyecare never leaks into iva-aesthetics.

### 6. Web Intelligence

| Tool | What It Does |
|------|-------------|
| **Firecrawl** | Authenticated web scraping via remote browser sandboxes. Persistent login profiles. Competitor research, content mining, help center ingestion. |
| **Whisper (MLX)** | Audio transcription on Apple Silicon. Mines YouTube tutorials, bootcamp recordings, training videos. |
| **yt-dlp** | Video/audio download from 1000+ sites. Pairs with Whisper for transcript extraction. |

---

## Security Model

On 2026-03-21, an AI agent autonomously navigated a Google SSO password change flow and changed the practice owner's Google Workspace password. This incident defined our entire security architecture.

| Rule | What It Means |
|------|--------------|
| Authentication pages = full stop | Agents never type credentials. Ever. |
| Two-tier browser policy | Firecrawl (remote sandbox, clicks allowed) vs Playwright (local, read-only) |
| GHL is read-only for agents | Live patient data. No automated edits. |
| Human authenticates, agent operates | Owner logs in via live view URL, agent uses the session after |

The security rules cannot be overridden by any instruction.

---

## The Flow

```
IVA (build + test)              →    PerformanceOD (package + share)
├── Myopia drip workflows       →    Template: "Myopia Campaign Kit"
├── Dry eye workflows           →    Template: "Dry Eye Patient Journey"
├── Foxfire → GHL sync          →    Product: "PMS Integration Setup"
├── Voice AI agents             →    Product: "Patient Communication AI"
├── Staff SOP AI agents         →    Product: "Staff Automation System"
└── Salience Memory             →    Tool: community-tools/salience-memory
```

Everything is built at IVA first. If it works in our chairs, it gets packaged. If it doesn't, it gets fixed or killed. Nothing ships as theory.

---

## What's Next

- Foxfire-GHL API integration (webhook event mapping, patient sync)
- Staff adoption of AI agents (currently owner-only)
- Community tool expansion (Firecrawl workflows, whisper pipeline, GHL templates)
- Open Source OD (OSOD) — community-built practice automation for optometry

---

*Built by a practicing O.D. at a real practice. Your software company said no. Foxfire said yes.*

[performanceod.com](https://performanceod.com)
