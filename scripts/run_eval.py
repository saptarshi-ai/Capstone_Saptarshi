"""
W5 Step 3 — Eval runner (baseline eval against golden set).

Usage
-----
  python scripts/run_eval.py                          # run all 20 entries
  python scripts/run_eval.py --label my-run-001      # custom label
  python scripts/run_eval.py --limit 5               # quick smoke test
  python scripts/run_eval.py --candidate-model gpt-4o-mini

What it does
------------
1. Loads data/golden_set.jsonl
2. For each entry, generates a candidate answer by calling the /ask endpoint
   (or directly calling the LLM if the API is not running — see --no-api flag)
3. Calls judge_one() to score the candidate against the ideal answer
4. Writes every result to data/answers.db → eval_runs table
5. Prints a summary table at the end

The eval_run_label ties all rows in one run together so you can compare runs.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running from the repo root: python scripts/run_eval.py
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from openai import OpenAI
from config.settings import Settings
from src.eval.golden import load_golden_set
from src.eval.judge import judge_one
from src.pipeline.store import ensure_schema, insert_eval_run, summarise_eval_run

settings = Settings()

DB_PATH = ROOT / "data" / "answers.db"
GOLDEN_PATH = ROOT / "data" / "golden_set.jsonl"


def generate_candidate(client: OpenAI, question: str, model: str) -> str:
    """
    Generate a candidate answer for evaluation.

    In a full RAG system this would call /ask. For W5 baseline eval
    we use the LLM directly with a minimal system prompt — this gives us
    a pre-RAG baseline to measure against once retrieval is wired up.
    """
    system_prompt = (
        "You are a Corporate Finance and Revenue Policy assistant. "
        "Answer the question based on standard accounting principles (IFRS/GAAP). "
        "Be concise. If the question is outside your scope, say so politely."
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.0,
        max_tokens=600,
    )
    return resp.choices[0].message.content.strip()


def run_eval(
    label: str,
    candidate_model: str = "gpt-4o-mini",
    judge_model: str = "gpt-4o",
    limit: int | None = None,
) -> dict:
    ensure_schema(DB_PATH)
    entries = load_golden_set(GOLDEN_PATH)
    if limit:
        entries = entries[:limit]

    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

    print(f"\n{'='*60}")
    print(f"Eval run: {label}")
    print(f"Entries : {len(entries)}")
    print(f"Models  : candidate={candidate_model}  judge={judge_model}")
    print(f"{'='*60}\n")

    results = []
    for i, entry in enumerate(entries, start=1):
        gid = entry["id"]
        question = entry["question"]
        ideal = entry["ideal_answer"]
        bucket = entry["bucket"]

        print(f"[{i:02}/{len(entries):02}] {gid} ({bucket})")
        print(f"  Q: {question[:80]}...")

        try:
            candidate = generate_candidate(client, question, candidate_model)
        except Exception as exc:
            print(f"  ⚠ candidate generation failed: {exc}")
            candidate = "[ERROR: generation failed]"

        try:
            score = judge_one(question, candidate, ideal, judge_model=judge_model)
        except Exception as exc:
            print(f"  ⚠ judge failed: {exc}")
            results.append({"id": gid, "error": str(exc)})
            continue

        row_id = insert_eval_run(
            DB_PATH,
            golden_id=gid,
            question=question,
            candidate_answer=candidate,
            ideal_answer=ideal,
            candidate_model=candidate_model,
            judge_model=judge_model,
            accuracy=score.accuracy,
            groundedness=score.groundedness,
            format=score.format,
            reasoning=score.reasoning,
            eval_run_label=label,
        )
        results.append({
            "id": gid,
            "bucket": bucket,
            "accuracy": score.accuracy,
            "groundedness": score.groundedness,
            "format": score.format,
            "row_id": row_id,
        })
        print(f"  → acc={score.accuracy} grd={score.groundedness} fmt={score.format}  (db row {row_id})")

    summary = summarise_eval_run(DB_PATH, label)
    print(f"\n{'='*60}")
    print(f"Summary for label='{label}'")
    print(f"  n              : {summary.get('n')}")
    print(f"  avg accuracy   : {summary.get('avg_accuracy', 0):.2f}")
    print(f"  avg groundedness: {summary.get('avg_groundedness', 0):.2f}")
    print(f"  avg format     : {summary.get('avg_format', 0):.2f}")
    print(f"  avg overall    : {summary.get('avg_overall', 0):.2f}")
    print(f"{'='*60}\n")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Run W5 baseline eval")
    parser.add_argument(
        "--label",
        default=f"baseline-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
        help="Label for this eval run (ties rows together in eval_runs table)",
    )
    parser.add_argument(
        "--candidate-model",
        default="gpt-4o-mini",
        help="Model used to generate candidate answers",
    )
    parser.add_argument(
        "--judge-model",
        default="gpt-4o",
        help="Model used as LLM judge",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process first N entries (for quick testing)",
    )
    args = parser.parse_args()

    run_eval(
        label=args.label,
        candidate_model=args.candidate_model,
        judge_model=args.judge_model,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
