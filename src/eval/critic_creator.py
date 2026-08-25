"""
W5 Step 5 — Critic-Creator iterative prompt refinement.

Pattern
-------
1. CREATOR  generates an answer using the current system prompt.
2. CRITIC   reviews the answer, identifies the worst specific flaw,
            and proposes a targeted fix to the system prompt.
3. CREATOR  regenerates using the improved prompt.
4. Loop for N rounds or until the critic scores the answer ≥ 3.5 / 4.

This is "prompt engineering in a loop" — the critic drives convergence
without a human in the loop.

Usage
-----
  from src.eval.critic_creator import run_critic_creator_loop
  trace = run_critic_creator_loop(question, ideal_answer, rounds=3)
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from openai import OpenAI
from config.settings import Settings

settings = Settings()

# ---------------------------------------------------------------------------
# Default starting system prompt (same as api/main.py)
# ---------------------------------------------------------------------------

DEFAULT_SYSTEM_PROMPT = (
    "You are a Corporate Finance and Revenue Policy assistant. "
    "Answer based on standard accounting principles (IFRS/GAAP/ASC). "
    "Be concise. If the question is outside your scope, say so politely."
)

# ---------------------------------------------------------------------------
# Critic prompt
# ---------------------------------------------------------------------------

CRITIC_SYSTEM_PROMPT = """You are a strict evaluator for a Corporate Finance and Revenue Policy Q&A assistant.
Your job is to identify the SINGLE most important flaw in the candidate answer compared to the ideal answer,
then propose a targeted one-sentence addition or change to the system prompt that would fix that flaw.

Respond ONLY with JSON:
{
  "flaw": "describe the specific flaw in one sentence",
  "prompt_patch": "the exact text to ADD or CHANGE in the system prompt (one sentence)",
  "quality_score": <float 1.0-4.0>   // 4.0 = matches ideal, 1.0 = completely wrong
}

Be very specific. Do not say "be more detailed" — say WHAT detail is missing.
Example: {"flaw": "Missing the three-condition test for provision recognition", "prompt_patch": "Always state the three recognition criteria (present obligation, probable outflow, reliable estimate) when answering provision questions.", "quality_score": 2.5}
"""


def _create(client: OpenAI, system_prompt: str, question: str, model: str) -> str:
    """Call the creator with the current system prompt."""
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


def _critique(
    client: OpenAI,
    question: str,
    candidate: str,
    ideal: str,
    model: str,
) -> dict:
    """Run the critic. Returns dict with flaw, prompt_patch, quality_score."""
    user_msg = f"""Question: {question}

Ideal Answer:
{ideal}

Candidate Answer:
{candidate}

Identify the single most important flaw and propose a prompt patch."""

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        max_tokens=300,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content.strip()
    return json.loads(raw)


def run_critic_creator_loop(
    question: str,
    ideal_answer: str,
    starting_prompt: str = DEFAULT_SYSTEM_PROMPT,
    creator_model: str = "gpt-4o-mini",
    critic_model: str = "gpt-4o",
    rounds: int = 3,
    quality_threshold: float = 3.5,
    client: OpenAI | None = None,
) -> dict:
    """
    Run the critic-creator loop for one (question, ideal_answer) pair.

    Returns a trace dict with:
      - rounds_run     : how many rounds actually ran
      - early_stop     : True if quality_threshold was reached early
      - final_prompt   : the improved system prompt after all rounds
      - final_answer   : the final candidate answer
      - history        : list of per-round details (prompt_used, answer, flaw, prompt_patch, quality_score)
    """
    if client is None:
        client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

    current_prompt = starting_prompt
    history = []

    print(f"\n{'='*60}")
    print(f"Critic-Creator loop | {rounds} max rounds")
    print(f"Q: {question[:80]}...")
    print(f"{'='*60}")

    final_answer = None
    early_stop = False

    for r in range(1, rounds + 1):
        print(f"\n--- Round {r} ---")

        # CREATOR step
        candidate = _create(client, current_prompt, question, creator_model)
        print(f"[Creator] {candidate[:100]}...")

        # CRITIC step
        critique = _critique(client, question, candidate, ideal_answer, critic_model)
        score = critique.get("quality_score", 0.0)
        flaw = critique.get("flaw", "")
        patch = critique.get("prompt_patch", "")

        print(f"[Critic]  score={score:.1f}  flaw={flaw[:80]}...")
        print(f"[Patch]   {patch[:100]}...")

        history.append({
            "round": r,
            "prompt_used": current_prompt,
            "answer": candidate,
            "flaw": flaw,
            "prompt_patch": patch,
            "quality_score": score,
        })

        final_answer = candidate

        if score >= quality_threshold:
            print(f"\n✓ Quality threshold {quality_threshold} reached at round {r}. Stopping early.")
            early_stop = True
            break

        # Apply patch: append the fix to the current prompt
        if patch:
            current_prompt = current_prompt.rstrip(". ") + " " + patch

    print(f"\n{'='*60}")
    print(f"Completed {len(history)} rounds. Early stop: {early_stop}")
    print(f"Final prompt:\n{current_prompt}")
    print(f"{'='*60}\n")

    return {
        "question": question,
        "ideal_answer": ideal_answer,
        "rounds_run": len(history),
        "early_stop": early_stop,
        "final_prompt": current_prompt,
        "final_answer": final_answer,
        "final_score": history[-1]["quality_score"] if history else 0.0,
        "history": history,
    }


if __name__ == "__main__":
    # Demo: run 2 rounds on a tricky question
    q = "When must a provision be recognised on the balance sheet?"
    ideal = (
        "A provision must be recognised when three conditions are met: "
        "(1) there is a present obligation (legal or constructive) as a result of a past event, "
        "(2) it is probable (more likely than not) that an outflow of resources will be required, "
        "and (3) a reliable estimate of the amount can be made. "
        "If probability is below 50%, it is disclosed as a contingent liability, not recognised."
    )
    trace = run_critic_creator_loop(q, ideal, rounds=2)
    print(f"Final score: {trace['final_score']}")
    print(f"Prompt improved from:\n  {DEFAULT_SYSTEM_PROMPT[:80]}...\nTo:\n  {trace['final_prompt'][:120]}...")
