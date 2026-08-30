"""
Vector Database Interface.
ChromaDB local store (default) with abstract base for swapping to Pinecone later.

PLACEHOLDER: PineconeStore — wire in when cloud-scale retrieval is needed (W8+).
"""
from __future__ import annotations
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional


class VectorStore(ABC):
    @abstractmethod
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None: ...

    @abstractmethod
    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def delete(self, document_ids: List[str]) -> None: ...

    @abstractmethod
    def count(self) -> int: ...


class ChromaDBStore(VectorStore):
    """
    ChromaDB local persistent store.
    Persisted to data/db/ — survives restarts.
    """
    def __init__(
        self,
        collection_name: str = "capstone_rag",
        persist_dir: str = "data/db",
    ):
        try:
            import chromadb
        except ImportError:
            raise ImportError("Run: pip install chromadb")

        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        if not documents:
            return
        if ids is None:
            # Generate stable IDs from current count + index
            start = self._collection.count()
            ids = [f"doc_{start + i}" for i in range(len(documents))]
        if metadata is None:
            metadata = [{}] * len(documents)
        self._collection.upsert(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadata,
            ids=ids,
        )

    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )
        output = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            output.append({
                "text": doc,
                "metadata": meta,
                # ChromaDB cosine distance: 0=identical, 2=opposite
                # Convert to similarity score 0-1
                "score": round(1 - dist / 2, 4),
            })
        return output

    def delete(self, document_ids: List[str]) -> None:
        self._collection.delete(ids=document_ids)

    def count(self) -> int:
        return self._collection.count()

    def reset(self) -> None:
        """Wipe the collection — useful for re-indexing."""
        self._client.delete_collection(self._collection.name)
        self._collection = self._client.create_collection(
            name=self._collection.name,
            metadata={"hnsw:space": "cosine"},
        )


# ── PLACEHOLDER ──────────────────────────────────────────────────────────────
class PineconeStore(VectorStore):
    """
    PLACEHOLDER — Pinecone cloud vector DB.
    Wire in for production scale (10M+ vectors).
    
    TODO (W8+): pip install pinecone-client
    Needs: PINECONE_API_KEY + PINECONE_ENVIRONMENT in .env
    """
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "PineconeStore is a placeholder. Use ChromaDBStore for now."
        )

    def add_documents(self, *a, **kw): ...
    def search(self, *a, **kw): ...
    def delete(self, *a, **kw): ...
    def count(self): ...
