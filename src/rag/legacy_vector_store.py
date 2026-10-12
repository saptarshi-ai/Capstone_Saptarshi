"""
Vector Database Interface.
Author: Saptarshi Sengupta

Provides ChromaDB (local persistent), Pinecone (cloud), and Qdrant (local/cloud)
vector stores behind a common VectorStore ABC.  Switch backends via VectorStoreFactory.

Dependencies:
    ChromaDB : pip install chromadb
    Pinecone : pip install pinecone-client
    Qdrant   : pip install qdrant-client
"""
from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

# ── Abstract Base ─────────────────────────────────────────────────────────────

class VectorStore(ABC):
    @abstractmethod
    def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None: ...

    @abstractmethod
    def search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    def delete(self, document_ids: list[str]) -> None: ...

    @abstractmethod
    def count(self) -> int: ...


# ── ChromaDB (local persistent) ───────────────────────────────────────────────

class ChromaDBStore(VectorStore):
    """
    ChromaDB local persistent store.
    Persisted to data/db/ — survives restarts.
    pip install chromadb
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
        documents: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        if not documents:
            return
        if ids is None:
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
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[dict[str, Any]]:
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )
        output = []
        docs  = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            output.append({
                "text": doc,
                "metadata": meta,
                # ChromaDB cosine distance: 0=identical → similarity 0-1
                "score": round(1 - dist / 2, 4),
            })
        return output

    def delete(self, document_ids: list[str]) -> None:
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


# ── Pinecone (cloud) ──────────────────────────────────────────────────────────

class PineconeStore(VectorStore):
    """
    Pinecone serverless/pod-based vector DB — production cloud scale.

    pip install pinecone-client

    Required env vars:
        PINECONE_API_KEY   — from console.pinecone.io
        PINECONE_INDEX_NAME — pre-created index (must match embedding dim)

    The index must already exist with the correct dimension and metric.
    Create it once via the Pinecone console or SDK before first use.
    """

    def __init__(
        self,
        api_key: str | None = None,
        index_name: str | None = None,
        namespace: str = "",
    ):
        try:
            from pinecone import Pinecone
        except ImportError:
            raise ImportError("Run: pip install pinecone-client")

        api_key = api_key or os.environ.get("PINECONE_API_KEY", "")
        index_name = index_name or os.environ.get("PINECONE_INDEX_NAME", "")

        if not api_key:
            raise ValueError("PINECONE_API_KEY is required (env or constructor arg)")
        if not index_name:
            raise ValueError("PINECONE_INDEX_NAME is required (env or constructor arg)")

        self._namespace = namespace
        pc = Pinecone(api_key=api_key)
        self._index = pc.Index(index_name)

    def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        if not documents:
            return
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        if metadata is None:
            metadata = [{} for _ in documents]

        # Pinecone expects metadata to carry the text (it doesn't store raw docs)
        records = []
        for doc_id, embedding, meta, text in zip(ids, embeddings, metadata, documents):
            combined_meta = {**meta, "text": text}
            records.append({"id": doc_id, "values": embedding, "metadata": combined_meta})

        # Upsert in batches of 100 (Pinecone limit)
        batch_size = 100
        for i in range(0, len(records), batch_size):
            self._index.upsert(
                vectors=records[i : i + batch_size],
                namespace=self._namespace,
            )

    def search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[dict[str, Any]]:
        results = self._index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=self._namespace,
        )
        output = []
        for match in results.get("matches", []):
            meta = dict(match.get("metadata", {}))
            text = meta.pop("text", "")
            output.append({
                "text": text,
                "metadata": meta,
                "score": round(float(match.get("score", 0.0)), 4),
            })
        return output

    def delete(self, document_ids: list[str]) -> None:
        self._index.delete(ids=document_ids, namespace=self._namespace)

    def count(self) -> int:
        stats = self._index.describe_index_stats()
        ns_stats = stats.get("namespaces", {}).get(self._namespace, {})
        return int(ns_stats.get("vector_count", 0))


# ── Qdrant (local Docker or cloud) ───────────────────────────────────────────

class QdrantStore(VectorStore):
    """
    Qdrant vector DB — runs as local Docker container or Qdrant Cloud.

    pip install qdrant-client

    Local Docker:
        docker run -p 6333:6333 qdrant/qdrant
        → url="http://localhost:6333", api_key=None

    Qdrant Cloud:
        → url="https://<cluster-id>.cloud.qdrant.io", api_key="<your-key>"

    Required env vars (alternative to constructor args):
        QDRANT_URL         e.g. http://localhost:6333
        QDRANT_API_KEY     (optional for local)
        QDRANT_COLLECTION  collection name

    The collection is created automatically on first use if it doesn't exist.
    You must supply `vector_size` to match your embedding model's dimension
    (e.g. 1536 for text-embedding-3-small, 384 for all-MiniLM-L6-v2).
    """

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        collection_name: str | None = None,
        vector_size: int = 1536,
        distance: str = "Cosine",
    ):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError:
            raise ImportError("Run: pip install qdrant-client")

        url = url or os.environ.get("QDRANT_URL", "http://localhost:6333")
        api_key = api_key or os.environ.get("QDRANT_API_KEY") or None
        collection_name = collection_name or os.environ.get(
            "QDRANT_COLLECTION", "capstone_rag"
        )

        self._collection = collection_name
        self._client = QdrantClient(url=url, api_key=api_key)

        # Create collection if it doesn't exist
        existing = {c.name for c in self._client.get_collections().collections}
        if collection_name not in existing:
            dist_map = {
                "Cosine": Distance.COSINE,
                "Euclid": Distance.EUCLID,
                "Dot":    Distance.DOT,
            }
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=dist_map.get(distance, Distance.COSINE),
                ),
            )

    def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        if not documents:
            return
        from qdrant_client.models import PointStruct

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        if metadata is None:
            metadata = [{} for _ in documents]

        points = []
        for point_id, embedding, meta, text in zip(ids, embeddings, metadata, documents):
            payload = {**meta, "text": text}
            points.append(
                PointStruct(id=point_id, vector=embedding, payload=payload)
            )

        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            self._client.upsert(
                collection_name=self._collection,
                points=points[i : i + batch_size],
            )

    def search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[dict[str, Any]]:
        results = self._client.search(
            collection_name=self._collection,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True,
        )
        output = []
        for hit in results:
            payload = dict(hit.payload or {})
            text = payload.pop("text", "")
            output.append({
                "text": text,
                "metadata": payload,
                "score": round(float(hit.score), 4),
            })
        return output

    def delete(self, document_ids: list[str]) -> None:
        from qdrant_client.models import PointIdsList
        self._client.delete(
            collection_name=self._collection,
            points_selector=PointIdsList(points=document_ids),
        )

    def count(self) -> int:
        info = self._client.get_collection(collection_name=self._collection)
        return int(info.points_count or 0)


# ── Factory ───────────────────────────────────────────────────────────────────

class VectorStoreFactory:
    """
    Returns the right VectorStore from environment config.

    Set VECTOR_STORE_BACKEND in .env:
        chroma   → ChromaDBStore  (default, local)
        pinecone → PineconeStore  (cloud, needs PINECONE_API_KEY + PINECONE_INDEX_NAME)
        qdrant   → QdrantStore    (local Docker or cloud, needs QDRANT_URL)
    """

    @staticmethod
    def get_store(
        backend: str | None = None,
        **kwargs: Any,
    ) -> VectorStore:
        backend = backend or os.environ.get("VECTOR_STORE_BACKEND", "chroma")

        if backend == "chroma":
            return ChromaDBStore(
                collection_name=kwargs.get("collection_name", "capstone_rag"),
                persist_dir=kwargs.get("persist_dir", "data/db"),
            )
        elif backend == "pinecone":
            return PineconeStore(
                api_key=kwargs.get("api_key"),
                index_name=kwargs.get("index_name"),
                namespace=kwargs.get("namespace", ""),
            )
        elif backend == "qdrant":
            return QdrantStore(
                url=kwargs.get("url"),
                api_key=kwargs.get("api_key"),
                collection_name=kwargs.get("collection_name"),
                vector_size=kwargs.get("vector_size", 1536),
            )
        else:
            raise ValueError(
                f"Unknown backend '{backend}'. Choose: chroma, pinecone, qdrant"
            )
