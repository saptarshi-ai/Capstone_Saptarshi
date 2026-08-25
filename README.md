# Corporate Finance & Revenue Policy Q&A — RAG Capstone

A Retrieval-Augmented Generation (RAG) pipeline for answering corporate finance and revenue policy questions. Built as a capstone project for the IIT Madras AI Engineering programme.

The system helps FP&A analysts, controllers, and finance business partners answer policy questions during month-end close, budget cycles, and audit preparation — grounded in IFRS, GAAP (ASC 606, IFRS 15, IFRS 16, IAS 37), and internal finance policy.

---

## What's in here

### Evaluation infrastructure (Module 1 — complete)

A complete LLM-as-judge evaluation system built before any retrieval is wired up, so improvements from RAG are objectively measurable.

- **20-entry golden set** — 14 happy-path / 4 harder (multi-hop) / 2 edge (graceful refusal) questions covering revenue recognition, lease accounting, provisions, intercompany, FX, expense management
- **3-dimensional LLM judge** — accuracy / groundedness / format, scored 1–4, using forced OpenAI tool calling so output is always structured JSON
- **SQLite persistence** — `eval_runs` table ties every score to a run label for cross-run comparison
- **Pairwise A/B comparison** — position-flip debiased (judge runs twice with A/B swapped; winner declared only when both rounds agree)
- **Critic-creator loop** — iterative prompt refinement; critic identifies worst flaw per round and proposes a one-sentence prompt patch

### API (Module 1 — baseline)

FastAPI service with `/ask`, `/ask_batched`, `/health`, and `/metrics` endpoints. Currently calls the LLM directly (pre-RAG baseline). Retrieval will be wired in Module 2.

---

## Project structure

```
02_capstone_rag_pipeline/
├── api/
│   └── main.py                  # FastAPI app (/ask, /health, /metrics)
├── data/
│   ├── golden_set.jsonl         # 20-entry locked golden set
│   ├── prompt-v1.txt            # Minimal system prompt (pairwise variant A)
│   └── prompt-v2.txt            # Structured system prompt (pairwise variant B)
├── docs/
│   ├── adr/
│   │   ├── 0001-capstone-framing.md   # ADR v1 locked — domain, stack, scope
│   │   ├── 0001-stakeholder-map.md    # Primary user, success metrics
│   │   └── 0002-eval-system-decisions.md
│   ├── dr/
│   │   └── dr1-summary.md             # Design Review 1 summary
│   ├── judge-calibration.md           # Human vs LLM judge score comparison
│   ├── golden-set-notes.md            # Coverage rationale for the golden set
│   ├── eval-run-001.md                # Baseline eval results
│   ├── prompt-pairwise-001.md         # A/B comparison findings
│   └── critic-creator-trace.md        # g015 refinement trace
├── scripts/
│   ├── run_eval.py              # Baseline eval runner (CLI)
│   ├── run_pairwise.py          # A/B prompt comparison (CLI)
│   └── run_critic_creator.py    # Critic-creator loop (CLI)
├── src/
│   ├── eval/
│   │   ├── judge.py             # 3-dim rubric + forced tool calling
│   │   ├── golden.py            # JSONL loader + validator
│   │   ├── pairwise.py          # Position-flip debiased comparison
│   │   └── critic_creator.py    # Iterative prompt refinement loop
│   ├── pipeline/
│   │   └── store.py             # SQLite persistence (answers + eval_runs)
│   └── rag/                     # Retrieval components (Module 2)
│       ├── chunking.py
│       ├── embeddings.py
│       ├── retriever.py
│       └── vector_store.py
└── config/
    └── settings.py              # Pydantic settings (reads .env)
```

---

## Quickstart

**1. Clone and set up**

```bash
git clone https://github.com/TAlchemist/ai-engineering-capstone.git
cd ai-engineering-capstone
pip install openai fastapi uvicorn pydantic-settings
```

**2. Set your API key**

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=your-key-here
```

**3. Run the eval baseline**

```bash
python scripts/run_eval.py --label baseline-001
```

Output: per-entry scores + summary table. Results stored in `data/answers.db`.

**4. Run pairwise comparison**

```bash
python scripts/run_pairwise.py --output data/pairwise-001-results.json
```

**5. Run critic-creator on the hardest entry**

```bash
python scripts/run_critic_creator.py --golden-id g015 --max-rounds 3 --threshold 3.5 --output docs/critic-creator-trace.md
```

**6. Start the API**

```bash
uvicorn api.main:app --reload
# Test: curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "What is the accrual basis of accounting?"}'
```

---

## Eval system design

### Judge rubric

| Dimension | What it measures | Scale |
|-----------|-----------------|-------|
| Accuracy | Factual correctness vs ideal answer | 1–4 |
| Groundedness | No hallucination; claims are sourceable | 1–4 |
| Format | Structure, length, finance-domain register | 1–4 |

**Why 1–4 (not 1–5)?** Odd-point scales allow fence-sitting in the middle. Forcing a 4-point scale makes the judge pick a side.

**Why forced tool calling?** Prevents the LLM judge from returning free-text instead of structured scores.

### Golden set design

| Bucket | n | Description |
|--------|---|-------------|
| happy-path | 14 | Single-hop questions, one policy area applies directly |
| harder | 4 | Multi-hop questions combining two policy areas, or conditional logic |
| edge | 2 | Out-of-scope questions — correct answer is graceful refusal + redirect |

### Pairwise position-flip debiasing

Each pair is judged twice with A/B positions swapped. A winner is only declared when both rounds agree. Disagreements are recorded as position-bias events and the result is a tie.

---

## Domain scope

**In scope:** Revenue recognition (ASC 606 / IFRS 15), lease accounting (IFRS 16), expense management, intercompany eliminations, provisions (IAS 37), financial instruments, bad debt, FX transactions, goodwill impairment.

**Out of scope by design:** Jurisdiction-specific tax rates, treasury/investment strategy, legal advice. These are handled with graceful refusal + redirect in the golden set (entries g019, g020).

---

## Roadmap

- [x] Module 1 — Evaluation infrastructure (golden set, judge, pairwise, critic-creator)
- [ ] Module 2 — Retrieval (ChromaDB vector store, embedding pipeline, retriever)
- [ ] Module 3 — RAG eval (re-run baseline with retrieval, compare scores)
- [ ] Module 4 — UI (Streamlit or Gradio front-end)
