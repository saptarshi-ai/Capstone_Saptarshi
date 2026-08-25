"""
W4 FastAPI cohort repo — Finance & Revenue Policy RAG pipeline.

Endpoints
---------
GET  /health          — liveness check
POST /ask             — single question → structured Answer (streaming)
POST /ask_batched     — same, but waits for full response + logs to SQLite

Answer model (schema_version='v1')
-----------------------------------
content        str   — the generated answer text
cost_usd       float — estimated API cost in USD
retries        int   — number of retry attempts (0 = first try succeeded)
confidence     float — self-reported confidence 0.0–1.0
sources        list  — retrieved source references (list of strings)
schema_version str   — 'v1' (for stable API contract)

Run with
--------
  uvicorn api.main:app --reload --port 8000
"""

import os
import sys
import time
from pathlib import Path
from typing import AsyncGenerator

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from openai import OpenAI

from config.settings import Settings
from src.pipeline.store import ensure_schema, insert_answer

settings = Settings()

DB_PATH = ROOT / "data" / "answers.db"
ensure_schema(DB_PATH)

app = FastAPI(
    title="Finance & Revenue Policy RAG API",
    version="v1",
    description="W4 cohort repo — structured outputs, cost tracking, SQLite persistence",
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    question: str = Field(..., description="The question to answer")
    model: str = Field(default="gpt-4o-mini", description="LLM model to use")


class Answer(BaseModel):
    content: str
    cost_usd: float = 0.0
    retries: int = 0
    confidence: float | None = None
    sources: list[str] = []
    schema_version: str = "v1"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a Corporate Finance and Revenue Policy assistant. "
    "Answer based on standard accounting principles (IFRS/GAAP/ASC). "
    "Be clear and concise. "
    "If the question is outside finance/accounting policy scope, "
    "say so politely and redirect to the appropriate team. "
    "Do not invent specific dollar thresholds or jurisdiction-specific tax rates."
)

def _get_client() -> OpenAI:
    return OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def _estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """Very rough cost estimate. Update rates as needed."""
    rates = {
        "gpt-4o":      (0.005, 0.015),   # per 1K tokens (in, out)
        "gpt-4o-mini": (0.00015, 0.0006),
    }
    in_rate, out_rate = rates.get(model, (0.001, 0.002))
    return round(
        (prompt_tokens / 1000) * in_rate + (completion_tokens / 1000) * out_rate,
        6,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "schema_version": "v1"}


@app.post("/ask")
def ask(req: AskRequest) -> Answer:
    """
    Synchronous single-question endpoint.
    Returns a structured Answer and logs the result to SQLite.
    """
    client = _get_client()
    retries = 0
    max_retries = 2

    while True:
        try:
            resp = client.chat.completions.create(
                model=req.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": req.question},
                ],
                temperature=0.0,
                max_tokens=600,
            )
            break
        except Exception as exc:
            retries += 1
            if retries > max_retries:
                raise HTTPException(status_code=502, detail=f"LLM error: {exc}")
            time.sleep(1)

    content = resp.choices[0].message.content.strip()
    usage = resp.usage
    cost = _estimate_cost(usage.prompt_tokens, usage.completion_tokens, req.model)

    # Persist to SQLite
    insert_answer(
        DB_PATH,
        question=req.question,
        content=content,
        model=req.model,
        cost_usd=cost,
        retries=retries,
        sources=None,
        schema_version="v1",
    )

    return Answer(
        content=content,
        cost_usd=cost,
        retries=retries,
        sources=[],
        schema_version="v1",
    )


@app.post("/ask_batched")
def ask_batched(req: AskRequest) -> Answer:
    """
    Batched variant — identical contract to /ask.
    In a full RAG system this would call the retrieval pipeline first.
    For W4/W5 it delegates to the same LLM call.
    """
    return ask(req)


@app.get("/metrics")
def metrics() -> dict:
    """Return basic operational metrics (stubbed — extend in W6+)."""
    import sqlite3
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            row = conn.execute(
                "SELECT COUNT(*) as n, AVG(cost_usd) as avg_cost FROM answers"
            ).fetchone()
        return {
            "total_answers": row[0],
            "avg_cost_usd": round(row[1] or 0, 6),
            "schema_version": "v1",
        }
    except Exception as exc:
        return {"error": str(exc)}
