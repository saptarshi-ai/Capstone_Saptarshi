"""
SQLite Experiment Tracking.
Logs every eval run and individual test case results to data/db/eval_runs.db.
"""
from __future__ import annotations
import csv
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


_DDL = """
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  REAL,
    config      TEXT,   -- JSON
    notes       TEXT
);

CREATE TABLE IF NOT EXISTS eval_cases (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER REFERENCES runs(id),
    query_id    TEXT,
    query       TEXT,
    response    TEXT,
    ideal       TEXT,
    judge_score REAL,
    latency_s   REAL,
    extra       TEXT    -- JSON for any additional fields
);
"""


class ExperimentTracker:
    def __init__(self, db_path: str = "data/db/eval_runs.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.executescript(_DDL)
        self._conn.commit()

    def log_run(self, config: Dict[str, Any], notes: str = "") -> int:
        """Insert a new run record. Returns run_id."""
        cur = self._conn.execute(
            "INSERT INTO runs (created_at, config, notes) VALUES (?, ?, ?)",
            (time.time(), json.dumps(config), notes),
        )
        self._conn.commit()
        return cur.lastrowid

    def log_evaluation_case(
        self,
        run_id: int,
        query_id: str,
        query: str,
        response: str,
        ideal: str,
        judge_score: float,
        latency_s: float = 0.0,
        extra: Optional[Dict] = None,
    ) -> None:
        self._conn.execute(
            """INSERT INTO eval_cases
               (run_id, query_id, query, response, ideal, judge_score, latency_s, extra)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id, query_id, query, response, ideal,
                judge_score, latency_s, json.dumps(extra or {}),
            ),
        )
        self._conn.commit()

    def get_run_summary(self, run_id: int) -> Dict[str, Any]:
        cur = self._conn.execute(
            """SELECT AVG(judge_score), AVG(latency_s), COUNT(*)
               FROM eval_cases WHERE run_id = ?""",
            (run_id,),
        )
        avg_score, avg_latency, count = cur.fetchone()
        return {
            "run_id": run_id,
            "avg_judge_score": round(avg_score or 0, 3),
            "avg_latency_s": round(avg_latency or 0, 3),
            "case_count": count,
        }

    def export_to_csv(self, output_path: str = "data/db/eval_export.csv") -> str:
        rows = self._conn.execute(
            "SELECT * FROM eval_cases ORDER BY run_id, id"
        ).fetchall()
        cols = [d[0] for d in self._conn.execute(
            "SELECT * FROM eval_cases LIMIT 0"
        ).description or []]
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        return output_path

    def close(self):
        self._conn.close()
