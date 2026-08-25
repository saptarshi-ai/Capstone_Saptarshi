"""
SQLite persistence layer for the cohort RAG pipeline.

Tables
------
answers    — stores every /ask_batched response (W4 contract)
eval_runs  — stores every LLM-judge evaluation result (W5 contract)

Public API
----------
ensure_schema(db_path)          — idempotent: creates tables if not exist
insert_answer(db_path, **fields) — log one /ask response
insert_eval_run(db_path, **fields) — log one judge evaluation
fetch_eval_runs(db_path, label) — return all eval rows for a given label
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_DDL_ANSWERS = """
CREATE TABLE IF NOT EXISTS answers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    question        TEXT    NOT NULL,
    content         TEXT    NOT NULL,
    model           TEXT    NOT NULL,
    cost_usd        REAL    NOT NULL DEFAULT 0.0,
    retries         INTEGER NOT NULL DEFAULT 0,
    confidence      REAL,
    sources         TEXT,           -- JSON array serialised as string
    schema_version  TEXT    NOT NULL DEFAULT 'v1',
    created_at      TEXT    NOT NULL
);
"""

_DDL_EVAL_RUNS = """
CREATE TABLE IF NOT EXISTS eval_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    golden_id       TEXT    NOT NULL,
    question        TEXT    NOT NULL,
    candidate_answer TEXT   NOT NULL,
    ideal_answer    TEXT    NOT NULL,
    candidate_model TEXT    NOT NULL,
    judge_model     TEXT    NOT NULL,
    accuracy        INTEGER NOT NULL,
    groundedness    INTEGER NOT NULL,
    format          INTEGER NOT NULL,
    reasoning       TEXT    NOT NULL,
    eval_run_label  TEXT    NOT NULL,
    created_at      TEXT    NOT NULL
);
"""


def _connect(db_path: str | Path) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(db_path: str | Path) -> None:
    """Idempotent. Creates tables if they don't exist."""
    with _connect(db_path) as conn:
        conn.execute(_DDL_ANSWERS)
        conn.execute(_DDL_EVAL_RUNS)
        conn.commit()
    print(f"[store] schema OK → {db_path}")


# ---------------------------------------------------------------------------
# answers table
# ---------------------------------------------------------------------------

def insert_answer(
    db_path: str | Path,
    *,
    question: str,
    content: str,
    model: str,
    cost_usd: float = 0.0,
    retries: int = 0,
    confidence: float | None = None,
    sources: str | None = None,
    schema_version: str = "v1",
) -> int:
    """Insert one /ask response. Returns the new row id."""
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO answers
              (question, content, model, cost_usd, retries, confidence, sources, schema_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (question, content, model, cost_usd, retries, confidence, sources, schema_version, created_at),
        )
        conn.commit()
        return cur.lastrowid


# ---------------------------------------------------------------------------
# eval_runs table
# ---------------------------------------------------------------------------

def insert_eval_run(
    db_path: str | Path,
    *,
    golden_id: str,
    question: str,
    candidate_answer: str,
    ideal_answer: str,
    candidate_model: str,
    judge_model: str,
    accuracy: int,
    groundedness: int,
    format: int,
    reasoning: str,
    eval_run_label: str,
) -> int:
    """Insert one judge evaluation result. Returns the new row id."""
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO eval_runs
              (golden_id, question, candidate_answer, ideal_answer,
               candidate_model, judge_model,
               accuracy, groundedness, format, reasoning,
               eval_run_label, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                golden_id, question, candidate_answer, ideal_answer,
                candidate_model, judge_model,
                accuracy, groundedness, format, reasoning,
                eval_run_label, created_at,
            ),
        )
        conn.commit()
        return cur.lastrowid


def fetch_eval_runs(db_path: str | Path, eval_run_label: str) -> list[dict[str, Any]]:
    """Return all rows for the given eval_run_label as dicts."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM eval_runs WHERE eval_run_label = ? ORDER BY id",
            (eval_run_label,),
        ).fetchall()
    return [dict(r) for r in rows]


def summarise_eval_run(db_path: str | Path, eval_run_label: str) -> dict[str, Any]:
    """Return avg scores and row count for a given label."""
    with _connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*)        AS n,
                AVG(accuracy)   AS avg_accuracy,
                AVG(groundedness) AS avg_groundedness,
                AVG(format)     AS avg_format,
                AVG((accuracy + groundedness + format) / 3.0) AS avg_overall
            FROM eval_runs
            WHERE eval_run_label = ?
            """,
            (eval_run_label,),
        ).fetchone()
    return dict(row) if row else {}


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    ensure_schema(path)
    rid = insert_eval_run(
        path,
        golden_id="g001",
        question="Test question?",
        candidate_answer="Test candidate.",
        ideal_answer="Test ideal.",
        candidate_model="gpt-4o-mini",
        judge_model="gpt-4o",
        accuracy=3, groundedness=3, format=3,
        reasoning="acc: ok | grd: ok | fmt: ok",
        eval_run_label="smoke-test",
    )
    print(f"inserted eval_run id={rid}")
    summary = summarise_eval_run(path, "smoke-test")
    print(f"summary: {summary}")
    os.unlink(path)
    print("smoke test passed")
