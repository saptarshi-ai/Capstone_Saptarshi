"""
LLM-as-a-Judge evaluation.
Scores generated answers on faithfulness and relevance using GPT-4o.
"""
from __future__ import annotations
import json
import os
import re
import time
from typing import Any, Dict, Optional
import openai


JUDGE_PROMPT = """You are an expert evaluation judge for a RAG (Retrieval-Augmented Generation) system.
Score the AI-generated answer on TWO dimensions using the rubric below.

RUBRIC:
faithfulness (0.0–1.0): Does the answer contain ONLY information from the provided context?
  1.0 = every claim is grounded in context, no hallucination
  0.5 = mostly grounded but contains at least one unsupported claim
  0.0 = answer fabricates information not in the context

relevance (0.0–1.0): Does the answer directly address the user's question?
  1.0 = fully answers the question
  0.5 = partially answers, misses key parts
  0.0 = off-topic or refuses to answer when context is available

Respond ONLY with a JSON object like:
{{"faithfulness": 0.9, "relevance": 0.8, "reasoning": "one sentence"}}

--- CONTEXT ---
{context}

--- QUESTION ---
{query}

--- GENERATED ANSWER ---
{answer}

--- IDEAL ANSWER (for reference only) ---
{ideal}
"""


class LLMJudge:
    """Uses GPT-4o to score RAG answers on faithfulness and relevance."""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    def evaluate(
        self,
        query: str,
        context: str,
        generated_answer: str,
        expected_answer: str = "",
    ) -> Dict[str, Any]:
        """
        Returns:
            {faithfulness: float, relevance: float, reasoning: str, composite: float}
        """
        prompt = JUDGE_PROMPT.format(
            context=context[:3000],  # cap context to avoid token overflow
            query=query,
            answer=generated_answer,
            ideal=expected_answer,
        )
        for attempt in range(2):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=150,
                )
                raw = response.choices[0].message.content or "{}"
                # Strip markdown fences
                raw = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
                scores = json.loads(raw)
                faithfulness = float(scores.get("faithfulness", 0))
                relevance = float(scores.get("relevance", 0))
                return {
                    "faithfulness": round(faithfulness, 3),
                    "relevance": round(relevance, 3),
                    "composite": round((faithfulness + relevance) / 2, 3),
                    "reasoning": scores.get("reasoning", ""),
                }
            except (json.JSONDecodeError, openai.RateLimitError) as e:
                if attempt == 0:
                    time.sleep(2)
                else:
                    return {"faithfulness": 0.0, "relevance": 0.0, "composite": 0.0, "reasoning": str(e)}

        return {"faithfulness": 0.0, "relevance": 0.0, "composite": 0.0, "reasoning": "judge failed"}


class ExactMatchJudge:
    """Simple string-matching judge for deterministic questions."""

    def evaluate(
        self, generated_answer: str, expected_answer: str, case_sensitive: bool = False
    ) -> Dict[str, Any]:
        a = generated_answer.strip()
        b = expected_answer.strip()
        if not case_sensitive:
            a, b = a.lower(), b.lower()
        match = a == b
        # Partial credit: check if key terms from ideal are in answer
        ideal_words = set(b.split())
        answer_words = set(a.split())
        overlap = len(ideal_words & answer_words) / max(len(ideal_words), 1)
        return {
            "exact_match": match,
            "term_overlap": round(overlap, 3),
            "composite": 1.0 if match else round(overlap * 0.5, 3),
        }
