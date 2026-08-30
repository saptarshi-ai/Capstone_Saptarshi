"""
API Schemas — Pydantic models for FastAPI request/response bodies.
"""
from pydantic import BaseModel
from typing import List, Optional


class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]


class UploadResponse(BaseModel):
    status: str
    filename: str
    chunks_added: int
