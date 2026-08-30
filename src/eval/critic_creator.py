"""
Critic-Creator Agent Pattern.
Two-agent loop: Creator generates an answer; Critic finds flaws; Creator improves.
Experimental — used for red-teaming the RAG pipeline.
"""
from __future__ import annotations
import os
from typing import Any, Dict, List
import openai


class CriticCreatorAgent:
    """
    Two-agent refinement loop.
    1. Creator generates an answer from context.
    2. Critic identifies hallucinations, gaps, or inaccuracies.
    3. Creator revises based on criticism.
    Max `max_rounds` refinement iterations.
    """
    def __init__(self, model: str = "gpt-4o", max_rounds: int = 2):
        self.model = model
        self.max_rounds = max_rounds
        self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    def _call(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
        )
        return resp.choices[0].message.content or ""

    def run(
        self,
        query: str,
        context: str,
        initial_answer: str = "",
    ) -> Dict[str, Any]:
        """
        Returns {final_answer: str, trace: List[{round, answer, critique}]}
        """
        answer = initial_answer or self._call(
            "You are a helpful HR policy assistant. Answer using ONLY the provided context.",
            f"Context:\n{context}\n\nQuestion: {query}",
        )
        trace: List[Dict] = []

        for round_num in range(1, self.max_rounds + 1):
            critique = self._call(
                "You are a strict fact-checker for an AI answer about company HR policy. "
                "Identify any claim NOT supported by the context, any hallucination, or any missing key info. "
                "Be brief and specific.",
                f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer to critique:\n{answer}",
            )
            trace.append({"round": round_num, "answer": answer, "critique": critique})

            if "no issues" in critique.lower() or "looks good" in critique.lower():
                break

            answer = self._call(
                "You are a helpful HR policy assistant. Revise your answer based on the critique. "
                "Use ONLY information from the context.",
                f"Context:\n{context}\n\nQuestion: {query}\n\nPrevious answer:\n{answer}\n\nCritique:\n{critique}\n\nRevised answer:",
            )

        return {"final_answer": answer, "rounds": len(trace), "trace": trace}
