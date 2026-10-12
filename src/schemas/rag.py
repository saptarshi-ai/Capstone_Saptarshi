"""
RAG Core Schemas.
Defines internal data structures passed between chunker, retriever, and generator.

Classes:
- DocumentChunk: Represents a single piece of text with metadata and an optional embedding.
- RetrievalResult: Represents a chunk fetched from the vector store with a similarity score.
"""
from typing import Any

from pydantic import BaseModel


class DocumentChunk(BaseModel):
    text: str
    metadata: dict[str, Any] = {}
    embedding: list[float] | None = None
