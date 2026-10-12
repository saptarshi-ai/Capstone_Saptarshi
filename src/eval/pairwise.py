"""
Pairwise A/B comparison (W5 judge pattern).
Flips position to remove ordering bias.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import openai

_PAIRWISE_PROMPT = """You are judging two AI-generated answers to the same question.
Pick the BETTER answer based on accuracy, groundedness, and completeness.
To avoid position bias, you will see both orderings; your preference should be consistent.

Question: {query}

Answer A:
{answer_a}

Answer B:
{answer_b}

Respond ONLY with JSON:
{{"winner": "A" or "B" or "tie", "reason": "one sentence"}}
"""


class PairwiseJudge:
    """
    Compares two system outputs via LLM-as-judge.
    Runs twice (A-B and B-A) and resolves ordering bias.
    """
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    def _judge_once(self, query: str, answer_a: str, answer_b: str) -> str:
        prompt = _PAIRWISE_PROMPT.format(
            query=query, answer_a=answer_a, answer_b=answer_b
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=100,
        )
        raw = re.sub(r"```(?:json)?\s*", "", resp.choices[0].message.content or "").strip().rstrip("`").strip()
        parsed = json.loads(raw)
        return parsed.get("winner", "tie")

    def compare(self, query: str, answer_a: str, answer_b: str) -> dict[str, Any]:
        """
        Returns {winner: "A"|"B"|"tie", reason: str, consistent: bool}
        consistent=True means both orderings agreed.
        """
        try:
            forward = self._judge_once(query, answer_a, answer_b)      # A vs B
            time.sleep(0.5)
            reverse = self._judge_once(query, answer_b, answer_a)       # B vs A (flipped)
            # Reverse result: if judge said "A" it means B won (positions swapped)
            reverse_mapped = "B" if reverse == "A" else ("A" if reverse == "B" else "tie")
            consistent = forward == reverse_mapped
            if consistent:
                winner = forward
            else:
                winner = "tie"  # disagreement → call it a tie
            return {
                "winner": winner,
                "forward_vote": forward,
                "reverse_vote": reverse_mapped,
                "consistent": consistent,
            }
        except Exception as e:
            return {"winner": "tie", "error": str(e)}
