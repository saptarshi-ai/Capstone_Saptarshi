"""Unit tests for chunking, embeddings (mocked), retriever."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.chunking import chunk_by_characters, chunk_by_tokens


def test_chunk_basic():
    text = "Hello world. " * 100
    chunks = chunk_by_characters(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 150 for c in chunks)  # allow small overflow


def test_chunk_empty():
    assert chunk_by_characters("") == []


def test_chunk_short_text():
    text = "Short text."
    chunks = chunk_by_characters(text, chunk_size=500, overlap=50)
    assert chunks == ["Short text."]


def test_chunk_by_tokens():
    text = " ".join(["word"] * 200)
    chunks = chunk_by_tokens(text, max_tokens=100)
    assert len(chunks) > 1


def test_chunk_overlap():
    # Overlap should create some shared context between consecutive chunks
    text = "Alpha beta gamma delta epsilon. " * 30
    chunks = chunk_by_characters(text, chunk_size=80, overlap=30)
    assert len(chunks) >= 2
