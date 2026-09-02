"""
FastAPI RAG Backend.
Endpoints:
  GET  /health          — liveness check
  POST /upload          — ingest documents into ChromaDB
  POST /query           — ask a question, get a grounded answer + sources
  GET  /metrics         — latest eval run summary

Run: uvicorn api.main:app --reload --port 8000
"""
from __future__ import annotations
import time

from fastapi import FastAPI, HTTPException, UploadFile, File

from src.schemas.api import QueryRequest, QueryResponse, UploadResponse
from src.rag.chunking import chunk_by_characters
from src.rag.embeddings import get_default_embedder
from src.rag.vector_store import ChromaDBStore
from src.rag.retriever import DenseRetriever
from src.rag.generator import LLMGenerator
from src.pipeline.store import ExperimentTracker

app = FastAPI(
    title="Basecamp Handbook RAG API",
    description="Grounded Q&A over the 37signals Employee Handbook.",
    version="0.1.0",
)

# ── Singletons (initialised once on startup) ──────────────────────────────────
_embedder = get_default_embedder()
_vector_store = ChromaDBStore(collection_name="capstone_rag", persist_dir="data/db")
_retriever = DenseRetriever(vector_store=_vector_store, embedder=_embedder)
_generator = LLMGenerator(model="gpt-4o")
_tracker = ExperimentTracker(db_path="data/db/eval_runs.db")

# Track latency samples for /metrics
_latency_samples: list[float] = []


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "indexed_chunks": _vector_store.count(),
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a .txt or .md file and index its chunks into ChromaDB.
    Chunks are embedded with text-embedding-3-small and stored.
    """
    if not file.filename.endswith((".txt", ".md")):
        raise HTTPException(400, "Only .txt and .md files supported.")

    content = (await file.read()).decode("utf-8", errors="replace")
    chunks = chunk_by_characters(content, chunk_size=500, overlap=50)
    if not chunks:
        raise HTTPException(400, "File is empty or produced no chunks.")

    embeddings = _embedder.get_embeddings_batch(chunks)
    metadata = [{"source": file.filename, "chunk_index": i} for i in range(len(chunks))]
    _vector_store.add_documents(chunks, embeddings, metadata=metadata)

    return UploadResponse(
        status="indexed",
        filename=file.filename,
        chunks_added=len(chunks),
    )


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """
    Answer a question using the RAG pipeline.
    1. Retrieve top_k relevant chunks from ChromaDB.
    2. Generate a grounded answer with GPT-4o.
    """
    if _vector_store.count() == 0:
        raise HTTPException(503, "No documents indexed yet. POST /upload first.")

    t0 = time.perf_counter()
    retrieved = _retriever.retrieve(req.query, top_k=req.top_k or 5)
    result = _generator.generate_answer(req.query, retrieved)
    latency = round(time.perf_counter() - t0, 3)
    _latency_samples.append(latency)

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
    )


@app.get("/metrics")
def metrics():
    """Returns latency stats and index size."""
    if not _latency_samples:
        return {"message": "No queries yet."}
    sorted_lat = sorted(_latency_samples)
    n = len(sorted_lat)
    return {
        "total_queries": n,
        "latency_mean_s": round(sum(sorted_lat) / n, 3),
        "latency_p50_s": round(sorted_lat[n // 2], 3),
        "latency_p95_s": round(sorted_lat[int(n * 0.95)], 3),
        "indexed_chunks": _vector_store.count(),
    }
