"""
A/B Pairwise Comparison.
Compares two prompting strategies (e.g. structured vs CoT) on the golden set.

Usage: python scripts/run_pairwise.py
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eval.golden import load_golden_set
from src.eval.pairwise import PairwiseJudge
from scripts.run_eval import build_pipeline


def main():
    dataset = load_golden_set()
    pipeline_a = build_pipeline(top_k=5)   # System A: top-k=5
    pipeline_b = build_pipeline(top_k=3)   # System B: top-k=3 (leaner retrieval)
    judge = PairwiseJudge()

    wins = {"A": 0, "B": 0, "tie": 0}
    for case in dataset:
        q = case["question"]
        a_out = pipeline_a(q)["answer"]
        b_out = pipeline_b(q)["answer"]
        result = judge.compare(q, a_out, b_out)
        wins[result["winner"]] += 1
        print(f"  [{case['id']}] winner={result['winner']} consistent={result.get('consistent')}")

    print(f"\nFinal: A={wins['A']} B={wins['B']} tie={wins['tie']}")


if __name__ == "__main__":
    main()
