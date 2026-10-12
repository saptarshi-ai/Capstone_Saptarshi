# Upstream sync — 12 Oct 2026 (Week 12 graded mini project)

Upstream: `vishnuap-ai-works/AIARAG-Capstone-Project`, synced to `81aaf47` (reference commit `84be031`, 3 Oct).
Previous sync: `1fc4a8d` (17 Sep).

## What I pulled in

| Upstream commit | Feature | Where it lives here |
|---|---|---|
| 4f201e5 | HyDE query augmentation | `src/rag/retriever.py`, `src/rag/prompts/prompts.py`, `USE_HYDE` |
| 6201cc0 | Query rewriting | `src/rag/retriever.py`, `USE_QUERY_REWRITING` |
| 0a0a128 | PII redaction (Presidio) at ingestion and query time | `src/rag/pii_redactor.py`, `USE_PII_REDACTION` |
| 84be031 | `run_evals.sh` forwards CLI args (e.g. `--limit`) | `bin/run_evals.sh` |
| c4b3f87 | Token and cost metrics in the eval report | `src/eval/pipeline_golden.py`, `scripts/run_pipeline_eval.py` |
| 2b5dc06 | Prompt compression (LLMLingua) | `src/rag/prompt_compressor.py`, `src/rag/generator.py` |
| c80128d | black / flake8 formatting | all upstream modules |
| 470c809, 319bd0c, 3c705c1 | Semantic cache (with TTL) and embedding cache | `src/rag/semantic_cache.py`, `src/rag/embedding_cache.py` |

Upstream reverted the three cache commits on 10 Oct. I kept them because they match the W11 live build,
but both caches are **off by default** (`ENABLE_SEMANTIC_CACHE=false`, `ENABLE_EMBEDDING_CACHE=false`).

## Two-track layout

My repo had two codebases mixed together: the upstream async pipeline and my own W5 evaluation stack.
They share module names, so I separated them.

| Track | Entry points | Modules |
|---|---|---|
| Pipeline (upstream, W6–W11) | `bin/run_ingestion.*`, `bin/run_inference.*`, `bin/run_evals.*` → `scripts/run_pipeline_eval.py` | `src/rag/{embeddings,generator,retriever,vector_store,reranker,semantic_cache,embedding_cache,pii_redactor,prompt_compressor}.py`, `src/pipeline/{store,inference}.py`, `src/eval/pipeline_{golden,judge}.py` |
| My W5 stack (API, UI, experiments) | `api/main.py`, `ui/app.py`, `scripts/run_eval.py`, `scripts/run_rag_eval.py`, `scripts/run_critic_creator.py`, `scripts/run_pairwise.py` | `src/rag/legacy_{embeddings,generator,retriever,vector_store}.py`, `src/pipeline/run_tracker.py`, `src/eval/{golden,judge,pairwise,critic_creator}.py` |

Shared: `src/rag/chunking.py` (added the async `SlidingWindowChunking` the ingestion pipeline expects),
`src/rag/document_loader.py`, `config/settings.py`.

## Other changes

- `.env.example` now carries every pipeline setting; my W5 keys are kept at the top.
- `pyproject.toml` adds the pipeline dependencies (qdrant, fastembed, presidio, spacy, tiktoken, llmlingua, ...).
- `tests/conftest.py` sets a placeholder `OPENAI_API_KEY` so tests import in CI without the secret.
- Fixed a typo in `scripts/run_critic_creator.py` (`collect_name` → `collection_name`).
- Upstream docs and eval results copied to `docs/vishnu-ref/` (reference only).

## Checks

- All modules compile; every script imports cleanly.
- `pytest tests` → 14 passed (the API test now runs; before it was silently skipped).
- `InferencePipeline()` starts with both caches disabled.
