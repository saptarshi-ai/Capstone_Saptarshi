# DR1 — Design Review Summary

**Date:** TBD  
**Presenter:** Saptarshi Sengupta  
**Reviewer(s):** TBD  

---

## System Under Review

RAG-powered Q&A assistant for the Basecamp (37signals) Employee Handbook.

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Vector DB | ChromaDB (local) | Zero-setup, persisted, swappable to Pinecone |
| Embedding model | text-embedding-3-small | 1536-dim, cost-effective, strong perf |
| Generator | GPT-4o | Highest faithfulness for grounded generation |
| Chunk size | 500 chars / 50 overlap | W6 recommendation, balances precision vs recall |
| Retrieval | DenseRetriever (top-5) | Starting point; HybridRetriever PLACEHOLDER ready |

## KPI Baseline Results (from run_eval.py)

| KPI | Target | Baseline | Status |
|-----|--------|----------|--------|
| Faithfulness | ≥ 0.85 | TBD | ⬜ |
| Answer Relevance | ≥ 0.80 | TBD | ⬜ |
| Latency p95 | ≤ 4.0s | TBD | ⬜ |

*Run `python scripts/run_rag_eval.py` to populate baseline.*

## What's Working

- End-to-end pipeline: ingest → embed → store → retrieve → generate
- All 4 eval scripts implemented
- Streamlit UI connected to FastAPI
- Corpus indexed: Basecamp Employee Handbook (data/temp/basecamp_handbook.md)

## Open Items / Placeholders

- [ ] HybridRetriever (BM25 + dense) — post W6 Day 4
- [ ] PineconeStore — for production scale (W8+)
- [ ] Streaming in Streamlit UI — post W6 streaming session
- [ ] Full golden set expansion (currently 5 questions; target 20+)

## Peer Feedback

*(to be filled in during DR1 session)*
