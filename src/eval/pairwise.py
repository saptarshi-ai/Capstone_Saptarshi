"""
W5 Step 4 — Pairwise comparison with position-flip debiasing.

Pairwise evaluation picks the BETTER answer between two candidates (A vs B)
for the same question. The known bias: LLMs prefer whichever response appears
first. We defeat this by running the same judge twice with positions flipped
and only declaring a winner when both flips agree.

Result codes
------------
  "A"   — A wins in both orderings
  "B"   — B wins in both orderings
  "tie" — models disagree across orderings (or explicit tie in both)

Usage
-----
  from src.eval.pairwise import compare_pair, batch_compare
  result = compare_pair(question, answer_a, answer_b, label_a="zero-shot", label_b="few-shot")
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from openai import OpenAI
from config.settings import Settings

settings = Settings()

PAIRWISE_SYSTEM_PROMPT = """You are an expert evaluator for a Corporate Finance and Revenue Policy Q&A assistant.
You will be shown a question and two candidate answers (A and B).
Pick the BETTER answer — more accurate, better grounded in finance policy, and clearer for a finance professional.
If neither is clearly better, call it a tie.

Respond ONLY with a JSON object with two keys:
  "winner": "A" | "B" | "tie"
  "reason": one sentence explaining the key difference

Example: {"winner": "A", "reason": "A correctly cites IFRS 16 while B omits the lease liability treatment."}
"""


def _ask_judge(
    client: OpenAI,
    question: str,
    first: str,
    second: str,
    model: str,
) -> tuple[str, str]:
    """
    Ask the judge to pick between first and second.
    Returns (winner_position, reason) where winner_position is "first", "second", or "tie".
    """
    user_msg = f"""Question: {question}

Answer A:
{first}

Answer B:
{second}

Which answer is better for a finance professional? Respond with JSON only."""

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": PAIRWISE_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        max_tokens=200,
        response_format={"type": "json_object"},
    )

    raw = resp.choices[0].message.content.strip()
    parsed = json.loads(raw)
    winner = parsed.get("winner", "tie").strip().upper()
    reason = parsed.get("reason", "")

    if winner == "A":
        return "first", reason
    elif winner == "B":
        return "second", reason
    else:
        return "tie", reason


def compare_pair(
    question: str,
    answer_a: str,
    answer_b: str,
    label_a: str = "A",
    label_b: str = "B",
    judge_model: str = "gpt-4o",
) -> dict:
    """
    Compare two answers with position-flip debiasing.

    Runs the judge twice:
      Round 1: A is presented first, B second
      Round 2: B is presented first, A second  ← flipped

    Declares a winner only when both rounds agree.

    Returns
    -------
    dict with keys:
      winner       : label_a | label_b | "tie"
      round1       : "first" | "second" | "tie"
      round2       : "first" | "second" | "tie"
      reason_r1    : judge reasoning for round 1
      reason_r2    : judge reasoning for round 2
      position_bias: True if rounds disagree
    """
    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

    # Round 1: A first, B second
    r1_winner, r1_reason = _ask_judge(client, question, answer_a, answer_b, judge_model)

    # Round 2: B first, A second (flipped)
    r2_winner_from_flip, r2_reason = _ask_judge(client, question, answer_b, answer_a, judge_model)

    # In round 2, "first" means B won (since B was presented first after the flip)
    # Convert to consistent A/B framing:
    if r2_winner_from_flip == "first":
        r2_winner = "second"   # B was first → "first" in round 2 = B → A perspective: B wins → "second" from A's view
    elif r2_winner_from_flip == "second":
        r2_winner = "first"    # A was second in round 2 → A wins
    else:
        r2_winner = "tie"

    # Resolve final winner
    position_bias = r1_winner != r2_winner

    if r1_winner == r2_winner == "first":
        winner = label_a
    elif r1_winner == r2_winner == "second":
        winner = label_b
    else:
        winner = "tie"  # Disagree across orderings → inconclusive

    return {
        "question_snippet": question[:80] + "..." if len(question) > 80 else question,
        "winner": winner,
        "round1": r1_winner,   # "first"=A, "second"=B, "tie"
        "round2": r2_winner,   # same scale after flip correction
        "reason_r1": r1_reason,
        "reason_r2": r2_reason,
        "position_bias": position_bias,
        "label_a": label_a,
        "label_b": label_b,
    }


def batch_compare(
    questions: list[str],
    answers_a: list[str],
    answers_b: list[str],
    label_a: str = "prompt-v1",
    label_b: str = "prompt-v2",
    judge_model: str = "gpt-4o",
) -> dict:
    """
    Run pairwise comparison across a batch of (question, answer_a, answer_b) triples.

    Returns a summary with win rates and per-question results.
    """
    assert len(questions) == len(answers_a) == len(answers_b), "All lists must be same length"

    results = []
    wins = {label_a: 0, label_b: 0, "tie": 0}

    for i, (q, a, b) in enumerate(zip(questions, answers_a, answers_b)):
        print(f"  pairwise [{i+1}/{len(questions)}] ...", end=" ", flush=True)
        result = compare_pair(q, a, b, label_a=label_a, label_b=label_b, judge_model=judge_model)
        results.append(result)
        wins[result["winner"]] += 1
        bias_flag = " ⚠ position bias" if result["position_bias"] else ""
        print(f"winner={result['winner']}{bias_flag}")

    n = len(results)
    return {
        "n": n,
        "wins": wins,
        "win_rate_a": wins[label_a] / n,
        "win_rate_b": wins[label_b] / n,
        "tie_rate": wins["tie"] / n,
        "position_bias_count": sum(1 for r in results if r["position_bias"]),
        "results": results,
    }


if __name__ == "__main__":
    # Quick demo with two synthetic answers for the first golden entry
    q = "What is the difference between cash-basis and accrual-basis accounting?"
    a_good = (
        "Under accrual accounting, revenue is recognised when earned, not when cash is received. "
        "Under cash-basis, revenue is recognised on receipt of cash. "
        "GAAP/IFRS require accrual for most companies above minimum revenue thresholds."
    )
    a_weak = "Cash basis means you record money when you get it. Accrual is more complicated."

    result = compare_pair(q, a_good, a_weak, label_a="good", label_b="weak")
    print(f"\nWinner: {result['winner']}")
    print(f"Position bias: {result['position_bias']}")
    print(f"Round 1 reason: {result['reason_r1']}")
    print(f"Round 2 reason: {result['reason_r2']}")
