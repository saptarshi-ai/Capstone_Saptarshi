# Capstone: Basecamp Handbook RAG Pipeline

**Author:** Saptarshi Sengupta  
**Programme:** AI Engineering — IITMP  
**Corpus:** 37signals Employee Handbook (Basecamp)

---

## What this does

RAG-powered Q&A assistant. Employees ask natural-language questions about company policies and receive grounded, cited answers from the handbook — no hallucination allowed.

---

## Quick Start

### 1. Install dependencies

```bash
# Windows
bin\setup_env.ps1

# Mac/Linux
bash bin/setup_env.sh
```

### 2. Add your API key

```bash
# Edit .env
OPENAI_API_KEY=sk-your-key-here
```

### 3. Index the handbook + run eval

```bash
python scripts/run_rag_eval.py
```

### 4. Launch the app

```bash
# Windows
bin\run_app.ps1

# Mac/Linux
bash bin/run_app.sh
```

Then open http://localhost:8501 in your browser.

---

## Architecture

```
User (Browser)
     │
     ▼
Streamlit UI  (ui/app.py) ─── POST /query ──► FastAPI  (api/main.py)
                                                    │
                              ┌─────────────────────┼───────────────────────┐
                              ▼                     ▼                       ▼
                      Embeddings            Retriever                 Generator
                 (src/rag/embeddings)   (src/rag/retriever)     (src/rag/generator)
                   OpenAI / HuggingFace   DenseRetriever            GPT-4o
                                         [PLACEHOLDER:          grounded prompt
                                         HybridRetriever]
                              │
                              ▼
                     Vector Store (configurable)
                 ChromaDB (local) | Pinecone (cloud) | Qdrant (Docker/cloud)
                      (src/rag/vector_store)
```

---

## KPIs (from ADR 0001)

| KPI | Target | Measured by |
|-----|--------|-------------|
| Faithfulness | ≥ 0.85 | LLM-as-judge (src/eval/judge.py) |
| Answer Relevance | ≥ 0.80 | Cosine sim: answer vs query embedding |
| Latency p95 | ≤ 4.0s | GET /metrics |

Run baseline: `python scripts/run_eval.py`

---

## File Map

```
src/
  rag/
    document_loader.py  ✅ TextLoader | MarkdownLoader | DocxLoader | DocLoader
                           PDFLoader (pdfplumber/pypdf) | PDFOcrLoader (pytesseract)
    chunking.py         ✅ SlidingWindowChunker | SectionChunking | SemanticChunker
    embeddings.py       ✅ OpenAIEmbeddings | HuggingFaceEmbeddings (sentence-transformers)
    vector_store.py     ✅ ChromaDBStore (local) | PineconeStore (cloud) | QdrantStore (Docker/cloud)
                           VectorStoreFactory — set VECTOR_STORE_BACKEND in .env
    retriever.py        ✅ DenseRetriever | 🔲 HybridRetriever (placeholder — post W6 Day 4)
    generator.py        ✅ GPT-4o grounded generation + streaming
    prompts/
      system_prompt.txt ✅ HR policy assistant
      user_prompt.txt   ✅ context injection template
  eval/
    judge.py            ✅ LLMJudge (faithfulness + relevance, 0-1)
    golden.py           ✅ golden set loader + run_evaluation + aggregate_metrics
    pairwise.py         ✅ position-debiased A/B comparison
    critic_creator.py   ✅ two-agent refinement loop
  pipeline/
    store.py            ✅ SQLite experiment tracker
  schemas/
    api.py              ✅ QueryRequest / QueryResponse / UploadResponse
    rag.py              ✅ DocumentChunk / RetrievalResult

api/main.py             ✅ /health /upload /query /metrics
ui/app.py               ✅ Streamlit chat + file upload + sidebar
config/
  settings.py           ✅ pydantic-settings from .env
  logging_config.py     ✅ standardised logging

data/
  golden_set.jsonl      ✅ 5 test cases (g001-g005)
  temp/basecamp_handbook.md  ✅ corpus (pre-downloaded)

scripts/
  run_rag_eval.py       ✅ ingest + eval in one shot
  run_eval.py           ✅ eval only (assumes already indexed)
  run_pairwise.py       ✅ A/B comparison
  run_critic_creator.py ✅ red-team agent loop

docs/
  adr/0001-capstone-framing.md  ✅ locked architecture
  dr/dr1-summary-template.md    ✅ fill after baseline eval
```

---

## Vector Store Configuration

Set `VECTOR_STORE_BACKEND` in `.env` to switch:

| Value | Store | Use when |
|-------|-------|----------|
| `chroma` (default) | ChromaDB local | Dev / POC — no infra needed |
| `qdrant` | Qdrant Docker | Local testing with prod-like perf |
| `pinecone` | Pinecone cloud | Prod / scale (10M+ vectors) |

**Qdrant quick start:**
```bash
docker run -p 6333:6333 qdrant/qdrant
# .env: VECTOR_STORE_BACKEND=qdrant  QDRANT_URL=http://localhost:6333
```

**Pinecone:** set `PINECONE_API_KEY` + `PINECONE_INDEX_NAME` in `.env` (create index first in console).

---

## Remaining Placeholder

| File | What's missing |
|------|---------------|
| `src/rag/retriever.py` → `HybridRetriever` | BM25 + dense fusion; needs `rank_bm25` |

---

## Commit convention

```
feat(rag): implement HybridRetriever with BM25
fix(eval): handle null score in aggregate_metrics
docs(dr1): populate baseline eval scores
eval(golden): add g006-g010 edge cases
```
