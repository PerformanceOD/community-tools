"""
Salience Memory System — Database Layer
Tracks recall frequency, recency, authority, and context relevance for memory chunks.
All state lives in a single SQLite file. Delete salience.db to reset everything.
"""

import sqlite3
import os
import math
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(__file__), "salience.db")

# Authority defaults by source type
AUTHORITY_DEFAULTS = {
    "feedback": 0.9,      # Eric corrections — highest signal
    "decision": 0.85,     # Codified choices
    "core": 0.8,          # soul.md, offer.md, audience.md, voice.md
    "agent_notes": 0.7,   # Agent learned from experience
    "domain": 0.6,        # Knowledge base — important but broad
    "research": 0.5,      # Investigation
    "memory_daily": 0.3,  # Ephemeral session context
    "conversation": 0.2,  # Raw chunks
    "unknown": 0.4,       # Unclassified
}

# Source type detection rules (path pattern → source_type)
SOURCE_RULES = [
    ("FEEDBACK-LOG", "feedback"),
    ("feedback_", "feedback"),
    ("decisions/", "decision"),
    ("reference/core/", "core"),
    ("agent_notes", "agent_notes"),
    ("reference/domain/", "domain"),
    ("reference/proof/", "domain"),
    ("reference/brand/", "domain"),
    ("research/", "research"),
    ("memory/2", "memory_daily"),  # memory/2026-03-28.md pattern
    ("MEMORY.md", "core"),
    ("CLAUDE.md", "core"),
    (".jsonl", "conversation"),
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            source_type TEXT DEFAULT 'unknown',
            authority REAL DEFAULT 0.4,
            recall_count INTEGER DEFAULT 0,
            last_recalled TEXT,
            first_stored TEXT DEFAULT (datetime('now')),
            manual_boost REAL DEFAULT 0.0,
            repo TEXT DEFAULT 'unknown'
        );

        CREATE TABLE IF NOT EXISTS recall_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chunk_id TEXT NOT NULL,
            agent_id TEXT DEFAULT 'claude-code',
            recalled_at TEXT DEFAULT (datetime('now')),
            context_query TEXT,
            acted_on INTEGER DEFAULT 0,
            FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
        );

        CREATE TABLE IF NOT EXISTS agent_scores (
            chunk_id TEXT,
            agent_id TEXT,
            recall_count INTEGER DEFAULT 0,
            last_recalled TEXT,
            PRIMARY KEY (chunk_id, agent_id)
        );

        CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_type);
        CREATE INDEX IF NOT EXISTS idx_chunks_authority ON chunks(authority);
        CREATE INDEX IF NOT EXISTS idx_recall_log_chunk ON recall_log(chunk_id);
        CREATE INDEX IF NOT EXISTS idx_agent_scores_agent ON agent_scores(agent_id);
    """)
    conn.commit()
    conn.close()


def classify_source(file_path: str) -> str:
    """Determine source type from file path."""
    for pattern, source_type in SOURCE_RULES:
        if pattern in file_path:
            return source_type
    return "unknown"


def detect_repo(file_path: str) -> str:
    """Detect which repo a file belongs to."""
    if "iva_eyecare" in file_path or "iva-eyecare" in file_path:
        return "iva_eyecare"
    elif "iva-aesthetics" in file_path or "iva_aesthetics" in file_path:
        return "iva-aesthetics"
    elif "performance-od" in file_path:
        return "performance-od"
    elif ".claude/" in file_path:
        return "claude-memory"
    return "unknown"


def register_chunk(file_path: str, authority: float = None):
    """Register a file/chunk in the salience database."""
    conn = get_conn()
    source_type = classify_source(file_path)
    if authority is None:
        authority = AUTHORITY_DEFAULTS.get(source_type, 0.4)
    repo = detect_repo(file_path)
    chunk_id = file_path  # Use file path as chunk ID for file-level tracking

    conn.execute("""
        INSERT INTO chunks (chunk_id, file_path, source_type, authority, repo, first_stored)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(chunk_id) DO UPDATE SET
            source_type = excluded.source_type,
            authority = CASE WHEN chunks.manual_boost > 0 THEN chunks.authority ELSE excluded.authority END,
            repo = excluded.repo
    """, (chunk_id, file_path, source_type, authority, repo))
    conn.commit()
    conn.close()


def record_recall(chunk_id: str, agent_id: str = "claude-code", context_query: str = None, acted_on: bool = False):
    """Record that a chunk was recalled."""
    conn = get_conn()
    now = datetime.now().isoformat()

    # Update chunk recall stats
    conn.execute("""
        UPDATE chunks SET recall_count = recall_count + 1, last_recalled = ? WHERE chunk_id = ?
    """, (now, chunk_id))

    # Log the recall event
    conn.execute("""
        INSERT INTO recall_log (chunk_id, agent_id, recalled_at, context_query, acted_on)
        VALUES (?, ?, ?, ?, ?)
    """, (chunk_id, agent_id, now, context_query, 1 if acted_on else 0))

    # Update per-agent scores
    conn.execute("""
        INSERT INTO agent_scores (chunk_id, agent_id, recall_count, last_recalled)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(chunk_id, agent_id) DO UPDATE SET
            recall_count = agent_scores.recall_count + 1,
            last_recalled = excluded.last_recalled
    """, (chunk_id, agent_id, now))

    conn.commit()
    conn.close()


def boost_chunk(chunk_id: str, boost: float = 0.2):
    """Manually boost a chunk's authority (Eric says 'this is important')."""
    conn = get_conn()
    conn.execute("""
        UPDATE chunks SET
            authority = MIN(1.0, authority + ?),
            manual_boost = manual_boost + ?
        WHERE chunk_id = ?
    """, (boost, boost, chunk_id))
    conn.commit()
    conn.close()


def compute_salience(decay_lambda: float = 0.05):
    """
    Compute salience scores for all chunks.
    SALIENCE = (frequency × 0.3) + (recency × 0.25) + (authority × 0.25) + (context_match × 0.2)
    context_match is deferred to retrieval time (vector similarity handles it).
    So static salience = frequency_norm × 0.375 + recency × 0.3125 + authority × 0.3125
    (re-normalized to sum to 1.0 without context_match)
    """
    conn = get_conn()
    chunks = conn.execute("SELECT * FROM chunks").fetchall()

    if not chunks:
        conn.close()
        return []

    # Normalize frequency (0-1 scale based on max)
    max_recall = max(c["recall_count"] for c in chunks) or 1

    results = []
    now = datetime.now()

    for chunk in chunks:
        # Frequency score (0-1)
        freq_score = chunk["recall_count"] / max_recall

        # Recency score (exponential decay)
        if chunk["last_recalled"]:
            try:
                last = datetime.fromisoformat(chunk["last_recalled"])
                days_ago = (now - last).total_seconds() / 86400
                recency_score = math.exp(-decay_lambda * days_ago)
            except (ValueError, TypeError):
                recency_score = 0.0
        else:
            # Never recalled — use first_stored with heavy penalty
            try:
                first = datetime.fromisoformat(chunk["first_stored"])
                days_ago = (now - first).total_seconds() / 86400
                recency_score = math.exp(-decay_lambda * days_ago) * 0.3  # 70% penalty
            except (ValueError, TypeError):
                recency_score = 0.0

        # Authority score (already 0-1)
        authority_score = chunk["authority"]

        # Composite (without context_match — that's applied at retrieval time)
        salience = (freq_score * 0.375) + (recency_score * 0.3125) + (authority_score * 0.3125)

        results.append({
            "chunk_id": chunk["chunk_id"],
            "file_path": chunk["file_path"],
            "source_type": chunk["source_type"],
            "repo": chunk["repo"],
            "recall_count": chunk["recall_count"],
            "authority": authority_score,
            "frequency": freq_score,
            "recency": recency_score,
            "salience": round(salience, 4),
        })

    conn.close()
    results.sort(key=lambda x: x["salience"], reverse=True)
    return results


def get_cross_agent_boosts():
    """Find chunks recalled by multiple agents — cross-domain signal."""
    conn = get_conn()
    results = conn.execute("""
        SELECT chunk_id,
               SUM(recall_count) as total_recalls,
               COUNT(DISTINCT agent_id) as agent_spread
        FROM agent_scores
        GROUP BY chunk_id
        HAVING agent_spread >= 2
        ORDER BY agent_spread DESC, total_recalls DESC
    """).fetchall()
    conn.close()
    return results


def get_stats():
    """Get summary statistics."""
    conn = get_conn()
    stats = {
        "total_chunks": conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
        "total_recalls": conn.execute("SELECT SUM(recall_count) FROM chunks").fetchone()[0] or 0,
        "chunks_by_source": {},
        "chunks_by_repo": {},
        "top_recalled": [],
    }

    for row in conn.execute("SELECT source_type, COUNT(*), AVG(authority) FROM chunks GROUP BY source_type"):
        stats["chunks_by_source"][row[0]] = {"count": row[1], "avg_authority": round(row[2], 3)}

    for row in conn.execute("SELECT repo, COUNT(*) FROM chunks GROUP BY repo"):
        stats["chunks_by_repo"][row[0]] = row[1]

    stats["top_recalled"] = [
        {"file": r["file_path"], "recalls": r["recall_count"], "authority": r["authority"]}
        for r in conn.execute("SELECT file_path, recall_count, authority FROM chunks ORDER BY recall_count DESC LIMIT 10")
    ]

    conn.close()
    return stats
