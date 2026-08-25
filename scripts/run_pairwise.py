"""
W5 Step 4 — Pairwise A/B prompt comparison.

Compares two prompt variants on the full golden set using position-flip
debiased judging. Winner is only declared when both order-A and order-B
rounds agree.

Usage
-----
  python scripts/run_pairwise.py
  python scripts/run_pairwise.py --prompt-v1 data/prompt-v1.txt --prompt-v2 data/prompt-v2.txt
  python scripts/run_pairwise.py --judge-model gpt-4o --output data/pairwise-001-results.json

What it does
------------
1. Loads both prompt files
2. For each golden entry, generates two candidate answers (one per prompt)
3. Calls compare_pair() which runs judge twice with A/B positions swapped
4. Aggregates wins/losses and writes results JSON
5. Prints a leaderboard table
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from openai import OpenAI
from config.settings import Settings
from src.eval.golden import load_golden_set
from src.eval.pairwise import batch_compare

settings = Settings()

GOLDEN_PATH = ROOT / "data" / "golden_set.jsonl"
DEFAULT_PROMPT_V1 = ROOT / "data" / "prompt-v1.txt"
DEFAULT_PROMPT_V2 = ROOT / "data" / "prompt-v2.txt"


def _generate(client: OpenAI, system_prompt: str, question: str, model: str) -> str:
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


def main():
    parser = argparse.ArgumentParser(description="Run pairwise A/B prompt comparison")
    parser.add_argument("--prompt-v1", default=str(DEFAULT_PROMPT_V1))
    parser.add_argument("--prompt-v2", default=str(DEFAULT_PROMPT_V2))
    parser.add_argument("--candidate-model", default="gpt-4o-mini")
    parser.add_argument("--judge-model", default="gpt-4o")
    parser.add_argument("--limit", type=int, default=None, help="Only first N entries")
    parser.add_argument("--output", default="data/pairwise-001-results.json")
    args = parser.parse_args()

    prompt_v1 = Path(args.prompt_v1).read_text(encoding="utf-8").strip()
    prompt_v2 = Path(args.prompt_v2).read_text(encoding="utf-8").strip()

    entries = load_golden_set(GOLDEN_PATH)
    if args.limit:
        entries = entries[: args.limit]

    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

    print(f"\n{'='*60}")
    print(f"Pairwise comparison — {len(entries)} entries")
    print(f"Candidate model : {args.candidate_model}")
    print(f"Judge model     : {args.judge_model}")
    print(f"{'='*60}\n")

    questions, answers_a, answers_b = [], [], []
    for entry in entries:
        q = entry["question"]
        print(f"Generating for {entry['id']} ...")
        a = _generate(client, prompt_v1, q, args.candidate_model)
        b = _generate(client, prompt_v2, q, args.candidate_model)
        questions.append(q)
        answers_a.append(a)
        answers_b.append(b)

    results = batch_compare(
        questions=questions,
        answers_a=answers_a,
        answers_b=answers_b,
        label_a="prompt-v1",
        label_b="prompt-v2",
        judge_model=args.judge_model,
    )

    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    wins = results["wins"]
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"  prompt-v1 wins  : {wins.get('prompt-v1', 0)} ({results['win_rate_a']:.1%})")
    print(f"  prompt-v2 wins  : {wins.get('prompt-v2', 0)} ({results['win_rate_b']:.1%})")
    print(f"  ties            : {results.get('tie_count', 0)} ({results['tie_rate']:.1%})")
    print(f"  position bias   : {results['position_bias_count']} rounds disagreed (flip)")
    print(f"\nResults written to: {output_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
