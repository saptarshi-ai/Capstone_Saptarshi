"""
API Schemas — Pydantic models for FastAPI request/response bodies.
"""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    top_k: int | None = 5


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]


class UploadResponse(BaseModel):
    status: str
    filename: str
    chunks_added: int
