"""
Golden Set Evaluation.
Loads the JSONL benchmark, runs the RAG pipeline, scores with the judge.
"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List

from src.eval.judge import LLMJudge


def load_golden_set(filepath: str = "data/golden_set.jsonl") -> List[Dict[str, Any]]:
    """
    Parses the JSONL golden set.
    Each line: {id, question, ideal_answer, notes, level}
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Golden set not found: {filepath}")
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("//"):
            rows.append(json.loads(line))
    return rows


def run_evaluation(
    golden_dataset: List[Dict[str, Any]],
    rag_pipeline: Callable[[str], Dict[str, Any]],
    judge: LLMJudge | None = None,
    verbose: bool = True,
) -> List[Dict[str, Any]]:
    """
    Runs full benchmark against golden set.
    
    Args:
        golden_dataset: Output of load_golden_set().
        rag_pipeline: Callable that takes query str and returns
                      {answer: str, sources: List[str], context: str}.
        judge: LLMJudge instance. Defaults to new LLMJudge().
    Returns:
        List of result dicts with scores per case.
    """
    if judge is None:
        judge = LLMJudge()

    results = []
    for case in golden_dataset:
        qid = case["id"]
        query = case["question"]
        ideal = case.get("ideal_answer", "")

        t0 = time.perf_counter()
        pipeline_out = rag_pipeline(query)
        latency = time.perf_counter() - t0

        answer = pipeline_out.get("answer", "")
        context = pipeline_out.get("context", "\n".join(pipeline_out.get("sources", [])))

        scores = judge.evaluate(
            query=query,
            context=context,
            generated_answer=answer,
            expected_answer=ideal,
        )

        result = {
            "id": qid,
            "level": case.get("level", "unknown"),
            "query": query,
            "ideal": ideal,
            "answer": answer,
            "latency_s": round(latency, 3),
            **scores,
        }
        results.append(result)

        if verbose:
            print(f"  [{qid}] faithfulness={scores['faithfulness']:.2f} relevance={scores['relevance']:.2f} latency={latency:.2f}s")

    return results


def aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Computes average faithfulness, relevance, composite, latency.
    Also breaks down by level (happy_path / hard_path / edge_path).
    """
    if not results:
        return {}
    n = len(results)
    agg = {
        "n": n,
        "faithfulness_mean": round(sum(r["faithfulness"] for r in results) / n, 3),
        "relevance_mean": round(sum(r["relevance"] for r in results) / n, 3),
        "composite_mean": round(sum(r["composite"] for r in results) / n, 3),
        "latency_mean_s": round(sum(r["latency_s"] for r in results) / n, 3),
        "latency_p95_s": round(sorted(r["latency_s"] for r in results)[int(n * 0.95)], 3),
    }
    # Per-level breakdown
    levels = {r["level"] for r in results}
    for lvl in levels:
        subset = [r for r in results if r["level"] == lvl]
        agg[f"faithfulness_{lvl}"] = round(sum(r["faithfulness"] for r in subset) / len(subset), 3)
    return agg
