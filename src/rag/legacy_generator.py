"""
Prompt Construction and LLM Answer Generation.
Injects retrieved context into the prompt and calls GPT-4o.
Supports streaming (token-by-token) for the Streamlit UI.
"""
from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import openai

_PROMPT_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    return (_PROMPT_DIR / filename).read_text().strip()


def _build_context_block(retrieved: list[dict[str, Any]]) -> str:
    """Format retrieved chunks into a numbered context block."""
    if not retrieved:
        return "(No relevant context found.)"
    lines = []
    for i, chunk in enumerate(retrieved, 1):
        lines.append(f"[Source {i}]\n{chunk['text'].strip()}")
    return "\n\n".join(lines)


class LLMGenerator:
    """
    Manages interactions with GPT-4o for grounded answer generation.
    System prompt: loaded from prompts/system_prompt.txt
    User prompt:   loaded from prompts/user_prompt.txt (has {context} and {query} slots)
    """
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.0):
        self.model = model
        self.temperature = temperature
        self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
        self._system_prompt = _load_prompt("system_prompt.txt")
        self._user_prompt_template = _load_prompt("user_prompt.txt")

    def _build_messages(self, query: str, retrieved: list[dict[str, Any]]) -> list:
        context_block = _build_context_block(retrieved)
        user_msg = self._user_prompt_template.format(
            context=context_block, query=query
        )
        return [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": user_msg},
        ]

    def generate_answer(
        self, query: str, retrieved_context: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Returns:
            {answer: str, sources: List[str], model: str}
        """
        messages = self._build_messages(query, retrieved_context)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        answer = response.choices[0].message.content or ""
        sources = [c.get("text", "")[:120] + "..." for c in retrieved_context]
        return {
            "answer": answer,
            "sources": sources,
            "model": self.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
        }

    def generate_stream(
        self, query: str, retrieved_context: list[dict[str, Any]]
    ) -> Generator[str, None, None]:
        """
        Yields answer tokens one by one for Streamlit streaming.
        Usage: for token in generator.generate_stream(q, ctx): st.write(token)
        """
        messages = self._build_messages(query, retrieved_context)
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
