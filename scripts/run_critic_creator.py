"""
W5 Step 5 — Critic-creator refinement loop.

Takes one golden entry and runs N rounds of critic-creator iteration,
patching the system prompt each round based on the critic's worst-flaw
feedback. Stops early if quality_score >= threshold.

Usage
-----
  python scripts/run_critic_creator.py --golden-id g015
  python scripts/run_critic_creator.py --golden-id g015 --max-rounds 3 --threshold 3.5
  python scripts/run_critic_creator.py --golden-id g015 --output docs/critic-creator-trace.md

What it does
------------
1. Loads the specified golden entry from data/golden_set.jsonl
2. Loads the starting prompt from data/prompt-v1.txt
3. Runs run_critic_creator_loop() for up to --max-rounds rounds
4. Saves a Markdown trace to --output showing each round's:
   - Current prompt
   - Generated answer
   - Flaw identified
   - Prompt patch applied
   - Quality score
5. Prints final summary to stdout
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from openai import OpenAI
from config.settings import Settings
from src.eval.golden import load_golden_set
from src.eval.critic_creator import run_critic_creator_loop

settings = Settings()

GOLDEN_PATH = ROOT / "data" / "golden_set.jsonl"
DEFAULT_PROMPT_PATH = ROOT / "data" / "prompt-v1.txt"


def _build_trace_md(golden_id: str, question: str, ideal: str, result: dict) -> str:
    lines = [
        f"# Critic-Creator Trace — {golden_id}",
        "",
        f"**Question:** {question}",
        f"**Golden ID:** {golden_id}",
        f"**Rounds run:** {result['rounds_run']}",
        f"**Early stop:** {result['early_stop']}",
        f"**Final quality score:** {result['final_score']:.1f} / 4.0",
        "",
        "---",
        "",
        "## Ideal answer (reference)",
        "",
        ideal,
        "",
        "---",
        "",
    ]

    for i, round_info in enumerate(result["history"], start=1):
        lines += [
            f"## Round {i}",
            "",
            f"**Quality score:** {round_info['quality_score']:.1f}",
            "",
            "### Prompt used",
            "",
            "```",
            round_info["prompt_used"],
            "```",
            "",
            "### Generated answer",
            "",
            round_info["answer"],
            "",
            f"**Flaw identified:** {round_info['flaw']}",
            "",
            f"**Prompt patch:** {round_info['prompt_patch']}",
            "",
            "---",
            "",
        ]

    lines += [
        "## Final prompt (after all patches)",
        "",
        "```",
        result["final_prompt"],
        "```",
        "",
        "## Final answer",
        "",
        result["final_answer"],
        "",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Run critic-creator refinement loop")
    parser.add_argument("--golden-id", default="g015", help="ID of golden entry to refine")
    parser.add_argument("--creator-model", default="gpt-4o-mini")
    parser.add_argument("--critic-model", default="gpt-4o")
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=3.5)
    parser.add_argument("--starting-prompt", default=str(DEFAULT_PROMPT_PATH))
    parser.add_argument("--output", default="docs/critic-creator-trace.md")
    args = parser.parse_args()

    entries = load_golden_set(GOLDEN_PATH)
    entry = next((e for e in entries if e["id"] == args.golden_id), None)
    if entry is None:
        print(f"ERROR: golden_id '{args.golden_id}' not found in {GOLDEN_PATH}")
        sys.exit(1)

    question = entry["question"]
    ideal = entry["ideal_answer"]
    starting_prompt = Path(args.starting_prompt).read_text(encoding="utf-8").strip()

    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

    print(f"\n{'='*60}")
    print(f"Critic-Creator loop — {args.golden_id}")
    print(f"Q: {question[:80]}...")
    print(f"Max rounds: {args.max_rounds}  Threshold: {args.threshold}")
    print(f"{'='*60}\n")

    result = run_critic_creator_loop(
        question=question,
        ideal_answer=ideal,
        starting_prompt=starting_prompt,
        creator_model=args.creator_model,
        critic_model=args.critic_model,
        rounds=args.max_rounds,
        quality_threshold=args.threshold,
        client=client,
    )

    trace_md = _build_trace_md(args.golden_id, question, ideal, result)
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(trace_md, encoding="utf-8")

    print(f"Rounds run    : {result['rounds_run']}")
    print(f"Early stop    : {result['early_stop']}")
    print(f"Final score   : {result['final_score']:.1f}")
    print(f"Trace saved to: {output_path}")


if __name__ == "__main__":
    main()
