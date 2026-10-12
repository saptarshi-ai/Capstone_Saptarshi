"""
Standard Evaluation Runner.
Loads golden set, runs RAG pipeline, scores with LLM judge, prints summary.

Usage:
    python scripts/run_eval.py
    python scripts/run_eval.py --golden data/golden_set.jsonl --top-k 5
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eval.golden import load_golden_set, run_evaluation, aggregate_metrics
from src.eval.judge import LLMJudge
from src.rag.chunking import chunk_by_characters
from src.rag.legacy_embeddings import get_default_embedder
from src.rag.legacy_vector_store import ChromaDBStore
from src.rag.legacy_retriever import DenseRetriever
from src.rag.legacy_generator import LLMGenerator
from src.pipeline.run_tracker import ExperimentTracker


def build_pipeline(top_k: int = 5):
    embedder = get_default_embedder()
    store = ChromaDBStore(collection_name="capstone_rag", persist_dir="data/db")
    retriever = DenseRetriever(vector_store=store, embedder=embedder)
    generator = LLMGenerator(model="gpt-4o")

    def pipeline(query: str) -> dict:
        retrieved = retriever.retrieve(query, top_k=top_k)
        result = generator.generate_answer(query, retrieved)
        context = "\n\n".join(c["text"] for c in retrieved)
        return {"answer": result["answer"], "sources": result["sources"], "context": context}

    return pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", default="data/golden_set.jsonl")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", default="data/db/eval_results.json")
    args = parser.parse_args()

    print(f"Loading golden set: {args.golden}")
    dataset = load_golden_set(args.golden)
    print(f"  {len(dataset)} test cases")

    pipeline = build_pipeline(top_k=args.top_k)
    judge = LLMJudge()
    tracker = ExperimentTracker()
    run_id = tracker.log_run({"top_k": args.top_k, "model": "gpt-4o"}, notes="run_eval.py")

    print("\nRunning evaluation...")
    results = run_evaluation(dataset, pipeline, judge=judge, verbose=True)

    for r in results:
        tracker.log_evaluation_case(
            run_id=run_id,
            query_id=r["id"], query=r["query"], response=r["answer"],
            ideal=r["ideal"], judge_score=r["composite"], latency_s=r["latency_s"],
        )

    metrics = aggregate_metrics(results)
    print("\n── SUMMARY ─────────────────────────────────")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps({"metrics": metrics, "results": results}, indent=2))
    print(f"\nResults saved to: {args.output}")

    # KPI gate
    faith = metrics.get("faithfulness_mean", 0)
    rel = metrics.get("relevance_mean", 0)
    p95 = metrics.get("latency_p95_s", 99)
    print("\n── KPI GATE ─────────────────────────────────")
    print(f"  Faithfulness ≥ 0.85: {'✅' if faith >= 0.85 else '❌'} ({faith})")
    print(f"  Relevance    ≥ 0.80: {'✅' if rel >= 0.80 else '❌'} ({rel})")
    print(f"  Latency p95  ≤ 4.0s: {'✅' if p95 <= 4.0 else '❌'} ({p95}s)")


if __name__ == "__main__":
    main()
