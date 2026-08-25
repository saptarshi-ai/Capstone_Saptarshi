# ADR-0002: Evaluation System Decisions — W5 Baseline

**Status:** Accepted
**Date:** 2026-08-26
**Capstone:** Corporate Finance & Revenue Policy Q&A Assistant

---

## Context

W5 requires establishing an eval baseline before RAG retrieval is wired up. This ADR records the three key design decisions made for the evaluation pipeline.

---

## Decision 1 — Rubric dimensions and scoring scale

**Chose:** 3 dimensions (accuracy, groundedness, format), each scored 1–4.

**Alternatives considered:**
- Binary pass/fail — too coarse; can't distinguish "mostly right" from "completely wrong"
- 5-point scale (1–5) — adds a midpoint (3) that evaluators interpret inconsistently; 4-point forces a lean
- Single composite score — loses diagnostic value; can't tell if failures are accuracy vs. hallucination vs. formatting

**Why 1–4, three dimensions:**
- Finance domain has three distinct failure modes: factual errors, hallucination, and poor structure
- Even split (no neutral midpoint) produces more actionable signals
- Matches the rubric design pattern used in the Track A notebook (RAGAS-inspired)

---

## Decision 2 — Candidate generation strategy for W5 baseline

**Chose:** Direct LLM call (no retrieval) using `gpt-4o-mini` at `temperature=0.0`.

**Rationale:** The W5 baseline intentionally excludes retrieval to create a pre-RAG benchmark. When retrieval is added in W6+, the delta vs. this baseline shows the value of RAG.

**Known limitation:** Without retrieval, the LLM is likely to hallucinate policy-specific details (thresholds, account codes) that only exist in internal documents — exactly what the groundedness dimension is designed to catch.

**Expected baseline scores:** accuracy ~2.8–3.2, groundedness ~2.0–2.5, format ~3.0–3.5.

---

## Decision 3 — eval_run_label scheme for comparing runs

**Chose:** Label format `{descriptor}-{YYYYMMDD}-{HHMM}`, e.g. `baseline-20260826-1400`.

**Rationale:**
- All rows in one run share the same label → easy GROUP BY in SQL
- Timestamp prevents accidental collision across runs
- Descriptor makes the label human-readable in reports

**Standard labels:**
| Label prefix | When to use |
|-------------|-------------|
| `baseline-` | Pre-RAG, direct LLM call |
| `rag-v1-` | First RAG retrieval run |
| `pairwise-` | Pairwise comparison run |
| `calibration-` | Judge calibration against human scores |
| `cc-improved-` | Post critic-creator prompt improvement |

---

## Consequences

- `scripts/run_eval.py --label baseline-YYYYMMDD` produces a named run in `data/answers.db`
- `summarise_eval_run(db_path, label)` returns per-run averages for the DR#1 readout
- All future runs compare against the baseline label to show improvement

---

## Next Decision Points (W6+)

- Retrieval model selection (dense vs. sparse vs. hybrid)
- Chunk size and overlap for finance PDFs
- Whether to include confidence scores in the Answer model
