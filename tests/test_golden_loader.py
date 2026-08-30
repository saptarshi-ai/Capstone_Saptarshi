"""Tests for golden set loader."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from src.eval.golden import load_golden_set, aggregate_metrics

def test_load_golden_set():
    rows = load_golden_set("data/golden_set.jsonl")
    assert len(rows) >= 3
    assert all("question" in r for r in rows)
    assert all("ideal_answer" in r for r in rows)

def test_aggregate_metrics_empty():
    result = aggregate_metrics([])
    assert result == {}

def test_aggregate_metrics():
    fake = [
        {"faithfulness": 0.9, "relevance": 0.8, "composite": 0.85, "latency_s": 1.2, "level": "happy_path"},
        {"faithfulness": 0.7, "relevance": 0.6, "composite": 0.65, "latency_s": 2.0, "level": "edge_path"},
    ]
    agg = aggregate_metrics(fake)
    assert agg["faithfulness_mean"] == 0.8
    assert agg["n"] == 2
