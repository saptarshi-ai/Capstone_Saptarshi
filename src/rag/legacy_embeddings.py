"""
Embedding Model Wrappers.
Unified interface over OpenAI and HuggingFace embedding models.
Same model must be used for both documents and queries.
"""
from __future__ import annotations
import os
import time
from abc import ABC, abstractmethod
from typing import List
import openai


class BaseEmbeddingModel(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        ...

    @abstractmethod
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        ...


class OpenAIEmbeddings(BaseEmbeddingModel):
    """
    OpenAI text-embedding-3-small (default) or text-embedding-3-large.
    1536-dim vectors. Same model MUST be used for docs and queries.
    """
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

    def get_embedding(self, text: str) -> List[float]:
        text = text.replace("\n", " ").strip()
        response = self.client.embeddings.create(input=[text], model=self.model)
        return response.data[0].embedding

    def get_embeddings_batch(
        self, texts: List[str], batch_size: int = 100, retry_delay: float = 1.0
    ) -> List[List[float]]:
        """
        Embed a list of texts in batches to respect API limits.
        Retries once on rate-limit errors.
        """
        embeddings: list[list[float]] = []
        cleaned = [t.replace("\n", " ").strip() for t in texts]
        for i in range(0, len(cleaned), batch_size):
            batch = cleaned[i : i + batch_size]
            for attempt in range(2):
                try:
                    response = self.client.embeddings.create(
                        input=batch, model=self.model
                    )
                    # OpenAI returns in order; sort by index for safety
                    batch_embs = sorted(response.data, key=lambda d: d.index)
                    embeddings.extend([d.embedding for d in batch_embs])
                    break
                except openai.RateLimitError:
                    if attempt == 0:
                        time.sleep(retry_delay)
                    else:
                        raise
        return embeddings


class HuggingFaceEmbeddings(BaseEmbeddingModel):
    """
    Local HuggingFace sentence-transformers — free, GPU optional.
    Default: all-MiniLM-L6-v2 (384-dim). Good for offline dev/testing.
    
    # PLACEHOLDER — install sentence-transformers if using:
    # pip install sentence-transformers
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError("Run: pip install sentence-transformers")

    def get_embedding(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()


def get_default_embedder() -> BaseEmbeddingModel:
    """Returns OpenAIEmbeddings with text-embedding-3-small."""
    return OpenAIEmbeddings(model="text-embedding-3-small")
