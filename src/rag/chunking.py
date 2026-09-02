"""
Text Splitting and Chunking Strategies.
Implements fixed-size sliding-window chunking (W6 style) and token-aware splitting.
"""
from __future__ import annotations
import re
from abc import ABC, abstractmethod
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


# ── OOP class-based wrappers (matching Vishnu's architecture) ─────────────────

class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        ...


class SlidingWindowChunker(BaseChunker):
    """Wraps chunk_by_characters as a class (Vishnu's SlidingWindowChunking style)."""
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[str]:
        return chunk_by_characters(text, self.chunk_size, self.overlap)


class SectionChunking(BaseChunker):
    """
    Splits text on Markdown section headers (# / ## / ###).
    Each section header + its body becomes one chunk.
    Falls back to paragraph splitting if no headers found.
    Ideal for structured documents like handbooks, READMEs, policy docs.
    """
    def __init__(self, min_chunk_chars: int = 100):
        self.min_chunk_chars = min_chunk_chars

    def chunk(self, text: str) -> List[str]:
        # Split on lines that start with one or more # characters
        header_pattern = re.compile(r"^(#{1,6}\s.+)$", re.MULTILINE)
        positions = [m.start() for m in header_pattern.finditer(text)]

        if not positions:
            # No headers — fall back to paragraph splitting
            paras = [p.strip() for p in text.split("\n\n") if p.strip()]
            return [p for p in paras if len(p) >= self.min_chunk_chars]

        chunks: list[str] = []
        # Text before the first header (preamble)
        if positions[0] > 0:
            preamble = text[: positions[0]].strip()
            if len(preamble) >= self.min_chunk_chars:
                chunks.append(preamble)

        for i, start in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else len(text)
            section = text[start:end].strip()
            if len(section) >= self.min_chunk_chars:
                chunks.append(section)

        return chunks


class SemanticChunker(BaseChunker):
    """
    Groups sentences by embedding cosine-similarity so that semantically
    related sentences stay in the same chunk (topic-aware splitting).

    Requires: sentence-transformers
        pip install sentence-transformers

    Algorithm:
        1. Split text into sentences.
        2. Embed each sentence with a local SentenceTransformer model.
        3. Compute cosine similarity between adjacent sentences.
        4. Split at positions where similarity drops below `threshold`.
        5. Merge short fragments back up to `max_chunk_chars`.
    """
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        threshold: float = 0.45,
        max_chunk_chars: int = 1500,
    ):
        self.model_name = model_name
        self.threshold = threshold
        self.max_chunk_chars = max_chunk_chars
        self._model = None  # lazy load

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "SemanticChunker needs sentence-transformers: "
                    "pip install sentence-transformers"
                )
        return self._model

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        return dot / (norm_a * norm_b + 1e-9)

    def chunk(self, text: str) -> List[str]:
        import re as _re
        # Split into sentences on ". ", "! ", "? "
        sentence_endings = _re.compile(r"(?<=[.!?])\s+")
        sentences = [s.strip() for s in sentence_endings.split(text) if s.strip()]

        if len(sentences) <= 1:
            return [text.strip()] if text.strip() else []

        model = self._get_model()
        embeddings = model.encode(sentences).tolist()

        # Find split points where similarity drops below threshold
        groups: list[list[str]] = []
        current: list[str] = [sentences[0]]

        for i in range(1, len(sentences)):
            sim = self._cosine(embeddings[i - 1], embeddings[i])
            if sim < self.threshold:
                groups.append(current)
                current = [sentences[i]]
            else:
                current.append(sentences[i])
        groups.append(current)

        # Merge groups into chunks respecting max_chunk_chars
        chunks: list[str] = []
        buffer = ""
        for group in groups:
            block = " ".join(group)
            if buffer and len(buffer) + len(block) + 1 <= self.max_chunk_chars:
                buffer = buffer + " " + block
            else:
                if buffer:
                    chunks.append(buffer.strip())
                buffer = block
        if buffer:
            chunks.append(buffer.strip())

        return [c for c in chunks if c]
