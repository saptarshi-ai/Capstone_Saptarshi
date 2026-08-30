"""
Text Splitting and Chunking Strategies.
Implements fixed-size sliding-window chunking (W6 style) and token-aware splitting.
"""
from __future__ import annotations
import re
from typing import List


def chunk_by_characters(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[str]:
    """
    Recursive character text splitting with sliding-window overlap.
    Splits on paragraph boundaries first, then sentences, then words.
    
    Args:
        text: Raw document text.
        chunk_size: Target characters per chunk.
        overlap: Characters of overlap between consecutive chunks.
    Returns:
        List of text chunk strings.
    """
    text = text.strip()
    if not text:
        return []

    # Split on paragraph breaks first, then sentences, then whitespace
    separators = ["\n\n", "\n", ". ", " ", ""]
    
    def _split(text: str, separators: list[str]) -> list[str]:
        if not separators or len(text) <= chunk_size:
            return [text]
        sep = separators[0]
        parts = text.split(sep) if sep else list(text)
        chunks = []
        current = ""
        for part in parts:
            candidate = current + (sep if current else "") + part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.extend(_split(current, separators[1:]) if len(current) > chunk_size else [current])
                current = part
        if current:
            chunks.extend(_split(current, separators[1:]) if len(current) > chunk_size else [current])
        return [c.strip() for c in chunks if c.strip()]

    raw_chunks = _split(text, separators)

    # Apply sliding-window overlap to merge/re-split into target size
    if overlap == 0:
        return [c for c in raw_chunks if c]

    merged: list[str] = []
    window = ""
    for chunk in raw_chunks:
        if not window:
            window = chunk
        elif len(window) + len(chunk) + 1 <= chunk_size:
            window = window + " " + chunk
        else:
            merged.append(window.strip())
            # Keep `overlap` chars of previous window for continuity
            tail = window[-overlap:] if len(window) > overlap else window
            window = tail + " " + chunk
    if window:
        merged.append(window.strip())

    return [c for c in merged if c]


def chunk_by_tokens(text: str, max_tokens: int = 512) -> List[str]:
    """
    Token-aware splitting using rough word-count approximation.
    Each word ≈ 1.3 tokens (OpenAI rule of thumb).
    For precise token counts use tiktoken (installed separately).
    """
    words = text.split()
    words_per_chunk = int(max_tokens / 1.3)
    chunks = []
    for i in range(0, len(words), words_per_chunk):
        chunk = " ".join(words[i : i + words_per_chunk])
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks
