# Eval Run 001 — Pre-RAG Baseline

**Label:** `baseline-20260826`
**Date:** 2026-08-26
**Candidate model:** gpt-4o-mini
**Judge model:** gpt-4o
**Golden entries evaluated:** 20 / 20
**Script:** `python scripts/run_eval.py --label baseline-20260826`

> **Note:** Run this in Vocareum to replace `[TBD]` values with real scores.
> Command: `python scripts/run_eval.py --label baseline-20260826`
> Then update the tables below from the printed summary.

---

## Aggregate scores

| Metric | Score |
|--------|-------|
| avg accuracy | [TBD — run eval] |
| avg groundedness | [TBD — run eval] |
| avg format | [TBD — run eval] |
| avg overall | [TBD — run eval] |
| n evaluated | 20 |

**Expected ranges** (pre-RAG baseline, direct LLM call):
- Accuracy: 2.8–3.3 (IFRS/GAAP well represented in training data; harder entries pull it down)
- Groundedness: 2.5–3.0 (model tends to hallucinate specific thresholds)
- Format: 3.2–3.7 (model is generally well-structured)

---

## By-bucket breakdown

| Bucket | n | avg accuracy | avg groundedness | avg format |
|--------|---|-------------|-----------------|-----------|
| happy-path | 14 | [TBD] | [TBD] | [TBD] |
| harder | 4 | [TBD] | [TBD] | [TBD] |
| edge | 2 | [TBD] | [TBD] | [TBD] |

Expected pattern: happy-path scores higher than harder (multi-hop requires retrieval to get right); edge scores are assessed mainly on format (graceful refusal quality).

---

## Interesting individual results

*(Fill in after running — copy 3-5 notable entries from stdout)*

| Golden ID | Bucket | Accuracy | Groundedness | Format | Notes |
|-----------|--------|----------|-------------|--------|-------|
| [TBD] | | | | | highest overall |
| [TBD] | harder | | | | expected to be low — multi-hop |
| g019 | edge | [TBD] | [TBD] | [TBD] | crypto refusal — format is what matters |
| g020 | edge | [TBD] | [TBD] | [TBD] | SG tax refusal |

---

## Observations

*(Fill in after running)*

**Where the model does well (expected):**
- Happy-path revenue recognition questions (IFRS 15 / ASC 606): model has strong training data coverage
- Format dimension: model consistently produces clean, readable answers

**Where the model struggles (expected):**
- g015–g018 (harder bucket): multi-hop contract modification, intercompany journal correction — model picks one policy area and misses the interaction
- Groundedness on harder entries: model tends to state specific thresholds (e.g., "50% probability") without sourcing
- Edge entries: model occasionally attempts an answer instead of redirecting gracefully

---

## What this baseline establishes

This run is the W5 pre-RAG baseline. It sets the floor for:
1. **Judge calibration** — comparing these scores to human scores (see `docs/judge-calibration.md`)
2. **Pairwise comparison** — prompt-v2 should outperform on harder entries
3. **W6 RAG improvement** — after wiring retrieval, re-run with label `rag-v1-YYYYMMDD` and compare averages

The expectation is RAG improves harder-bucket accuracy and groundedness by 0.3–0.5 points, with smaller gains on happy-path (already near ceiling).

---

## Raw DB query (for reference)

```sql
SELECT golden_id, accuracy, groundedness, format, eval_run_label
FROM eval_runs
WHERE eval_run_label = 'baseline-20260826'
ORDER BY golden_id;
```

Run in Vocareum: `python -c "import sqlite3; ..."` or open `data/answers.db` with any SQLite viewer.
