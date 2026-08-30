# Capstone Project — Build Status

**Author:** Saptarshi Sengupta  
**Last updated:** 2026-08-30  
**Repo:** `Capstone/AIARAG-Capstone-Project-main/`

---

## What's Built

| Layer | File | Status |
|---|---|---|
| RAG | `src/rag/chunking.py` | ✅ Fixed-size + sliding window — 289 chunks from handbook |
| RAG | `src/rag/embeddings.py` | ✅ OpenAI `text-embedding-3-small` + HuggingFace fallback |
| RAG | `src/rag/vector_store.py` | ✅ ChromaDB (persistent to `data/db/`) |
| RAG | `src/rag/retriever.py` | ✅ DenseRetriever working · HybridRetriever = placeholder |
| RAG | `src/rag/generator.py` | ✅ GPT-4o grounded generation + streaming |
| RAG | `src/rag/prompts/system_prompt.txt` | ✅ Fixed (was "financial assistant" bug) |
| Eval | `src/eval/judge.py` | ✅ LLMJudge — faithfulness + relevance (0–1) |
| Eval | `src/eval/golden.py` | ✅ 5 test cases, KPI aggregation |
| Eval | `src/eval/pairwise.py` | ✅ Position-debiased A/B comparison |
| Eval | `src/eval/critic_creator.py` | ✅ Two-agent refinement loop |
| Pipeline | `src/pipeline/store.py` | ✅ SQLite experiment tracker |
| API | `api/main.py` | ✅ /health /upload /query /metrics |
| UI | `ui/app.py` | ✅ Streamlit chat + file upload + quick-index |
| Scripts | `scripts/run_rag_eval.py` | ✅ One command: ingest → eval → KPI gate |
| Scripts | `scripts/run_eval.py` | ✅ Eval only (assumes already indexed) |
| Scripts | `scripts/run_pairwise.py` | ✅ A/B comparison runner |
| Tests | `tests/*.py` | ✅ 6 test files (chunking, judge, golden, API, pairwise, UI) |
| Docs | `docs/adr/0001-capstone-framing.md` | ✅ Locked architecture |
| Docs | `docs/dr/dr1-summary-template.md` | ✅ Populated (fill baseline scores after first eval run) |

---

## Placeholders (fill after W6 Day 4+)

| Placeholder | File | Needs |
|---|---|---|
| `HybridRetriever` | `src/rag/retriever.py` | `pip install rank_bm25` + W6 Day 4 content |
| `PineconeStore` | `src/rag/vector_store.py` | `pip install pinecone-client` (W8+) |
| Streaming UI | `ui/app.py` | Wire `generate_stream()` into Streamlit `st.write_stream()` |

---

## KPI Targets (from ADR 0001)

| KPI | Target | Baseline | Status |
|---|---|---|---|
| Faithfulness | ≥ 0.85 | run `scripts/run_eval.py` | ⬜ pending |
| Answer Relevance | ≥ 0.80 | run `scripts/run_eval.py` | ⬜ pending |
| Latency p95 | ≤ 4.0s | GET /metrics | ⬜ pending |

---

## How to Run

```bash
# 1. Setup
bash bin/setup_env.sh
# add OPENAI_API_KEY to .env

# 2. Ingest handbook + run full eval (one command)
python scripts/run_rag_eval.py

# 3. Launch the app
bash bin/run_app.sh
# → API on :8000, UI on :8501
```

---

## Graded Mini Projects (separate from capstone)

| Project | Location | Status |
|---|---|---|
| MP1 — Prompt Lab | `Week_5/Week 5_Graded Mini Project_Sengupta/` | ✅ Built — run notebook then submit ZIP on Emeritus |

