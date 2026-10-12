"""
Core Retrieval Logic.
DenseRetriever: top-k cosine similarity via ChromaDB.
HybridRetriever: PLACEHOLDER — dense + BM25 sparse search (post W6 Day 4).
"""
from __future__ import annotations
from typing import List, Dict, Any

from src.rag.legacy_embeddings import BaseEmbeddingModel, get_default_embedder
from src.rag.legacy_vector_store import ChromaDBStore, VectorStore


class BaseRetriever:
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError


class DenseRetriever(BaseRetriever):
    """
    Standard dense vector similarity search.
    Embeds the query with the same model used for documents,
    queries ChromaDB, returns top_k chunks sorted by cosine similarity.
    """
    def __init__(
        self,
        vector_store: VectorStore | None = None,
        embedder: BaseEmbeddingModel | None = None,
    ):
        self.store = vector_store or ChromaDBStore()
        self.embedder = embedder or get_default_embedder()

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Args:
            query: Natural language question from the user.
            top_k: Number of chunks to return.
        Returns:
            List of dicts: {text, metadata, score}
        """
        query_embedding = self.embedder.get_embedding(query)
        results = self.store.search(query_embedding, top_k=top_k)
        return results


class HybridRetriever(BaseRetriever):
    """
    PLACEHOLDER — Hybrid search: dense (ChromaDB) + sparse (BM25).
    
    TODO after W6 Day 4 (Advanced Retrieval):
    1. pip install rank_bm25
    2. Build BM25 index from corpus chunks
    3. Combine dense score + BM25 score (weighted: alpha*dense + (1-alpha)*bm25)
    4. Optional: add cross-encoder re-ranking for final top_k
    
    Stub: falls back to DenseRetriever until implemented.
    """
    def __init__(
        self,
        vector_store: VectorStore | None = None,
        embedder: BaseEmbeddingModel | None = None,
        alpha: float = 0.7,  # weight for dense vs sparse
    ):
        self._dense = DenseRetriever(vector_store=vector_store, embedder=embedder)
        self.alpha = alpha
        # PLACEHOLDER: self._bm25 = BM25Retriever(corpus_chunks)

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # TODO: merge dense + BM25 scores, re-rank
        # For now: delegate to dense only
        return self._dense.retrieve(query, top_k=top_k)
