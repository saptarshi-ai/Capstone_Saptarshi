"""
End-to-end RAG Evaluation (ingest + eval in one shot).
Indexes the handbook then runs the golden set evaluation.

Usage: python scripts/run_rag_eval.py
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.chunking import chunk_by_characters
from src.rag.embeddings import get_default_embedder
from src.rag.vector_store import ChromaDBStore
from scripts.run_eval import build_pipeline, main as run_eval_main


def ingest_handbook(
    handbook_path: str = "data/temp/basecamp_handbook.md",
    chunk_size: int = 500,
    overlap: int = 50,
) -> int:
    text = Path(handbook_path).read_text()
    chunks = chunk_by_characters(text, chunk_size=chunk_size, overlap=overlap)
    embedder = get_default_embedder()
    store = ChromaDBStore(collection_name="capstone_rag", persist_dir="data/db")

    if store.count() > 0:
        print(f"  ChromaDB already has {store.count()} chunks — skipping re-index.")
        return store.count()

    print(f"  Embedding {len(chunks)} chunks (this takes ~60s)...")
    embeddings = embedder.get_embeddings_batch(chunks)
    metadata = [{"source": "basecamp_handbook.md", "chunk_index": i} for i in range(len(chunks))]
    store.add_documents(chunks, embeddings, metadata=metadata)
    print(f"  Indexed {store.count()} chunks into ChromaDB.")
    return store.count()


if __name__ == "__main__":
    print("Step 1: Ingest handbook")
    ingest_handbook()
    print("\nStep 2: Run evaluation")
    run_eval_main()
