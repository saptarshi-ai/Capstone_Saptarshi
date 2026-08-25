# DR#1 Summary — Module 1 Design Review

**Project:** Corporate Finance & Revenue Policy Q&A — RAG Capstone
**DR round:** 1 (W5 checkpoint)
**Date:** 2026-08-26
**Author:** Saptarshi Sengupta
**Status:** Ready for peer review

---

## What we built

The Module 1 deliverable is a complete evaluation infrastructure for a RAG Q&A assistant targeting FP&A analysts. No retrieval is wired yet — this milestone establishes the measurement system so that W6 retrieval improvements are objectively measurable.

Core components delivered:

**Data:** A 20-entry locked golden set covering 7 finance policy areas (revenue recognition, leases, provisions, FX, intercompany, expense management, disclosures) with 14 happy-path, 4 harder (multi-hop), and 2 edge (graceful refusal) entries.

**Evaluation:** A 3-dimensional LLM judge (accuracy / groundedness / format, 1-4 scale) with forced tool-calling to prevent unstructured output. SQLite persistence via `eval_runs` table with labels to tie runs together for comparison.

**Analysis tools:** Pairwise A/B comparison with position-flip debiasing (declares winner only when both A→B and B→A rounds agree), and a critic-creator loop that iteratively patches the system prompt based on identified flaws.

---

## Key decisions and why

**Why 3 dimensions, 1-4 scale?** Accuracy alone misses hallucination (a factually accurate sentence can be ungrounded if it cites a fabricated threshold). Format matters because the primary user — an analyst during month-end close — needs a scannable, direct answer. The 1-4 scale (no middle) forces the judge to pick a side; 5-point scales cluster at 3.

**Why separate the baseline from RAG?** Without a pre-RAG baseline, there's no way to know if retrieval actually helps. Wiring RAG first and then evaluating creates survivorship bias — you tune for the system you built rather than measuring improvement.

**Why g015 for critic-creator?** It's the golden set's hardest entry: ASC 606 contract modification with two simultaneous judgement calls (distinct performance obligation + standalone selling price). This is where a naive LLM is most likely to fail and where iterative prompt patching has the most room to improve.

---

## Baseline performance (pre-RAG)

*(Update with real numbers after running `python scripts/run_eval.py --label baseline-20260826` in Vocareum)*

| Metric | Baseline | Target (post-RAG) |
|--------|---------|-------------------|
| avg accuracy | [TBD] | ≥ 3.4 |
| avg groundedness | [TBD] | ≥ 3.3 |
| avg format | [TBD] | ≥ 3.4 |
| harder-bucket accuracy | [TBD] | ≥ 3.0 |

Expected baseline pattern: happy-path scores 3.0–3.5, harder 2.0–2.8, edge varies by refusal quality.

---

## What we learned from judge calibration

*(Update after filling `docs/judge-calibration.md` LLM scores column)*

Human scores were captured for 10 entries (g001–g006, g009, g011, g015, g019). The key calibration questions:

- Does the judge over-score on groundedness? (LLMs tend to reward confident-sounding answers)
- Does the judge agree with humans on edge entries? (graceful refusals are unusual inputs for the judge)
- Is within-1 agreement ≥ 95%? (target threshold for judge reliability)

---

## What's open

1. **Vocareum run** — scripts are implemented locally; need to transfer and run in Vocareum to get actual scores. All `[TBD]` values in eval-run-001.md, prompt-pairwise-001.md, and critic-creator-trace.md will be filled then.

2. **Corpus build** — the W6 RAG milestone requires a Finance Policy corpus. Planned approach: markdown documents derived from IFRS/GAAP standards summaries + internal policy templates. No proprietary data used.

3. **Retrieval integration** — once corpus exists: embed chunks, index into ChromaDB, wire retrieval into `/ask`, rerun eval with label `rag-v1-YYYYMMDD` and compare to baseline.

---

## Open questions for peer reviewers

1. Is 20 golden entries sufficient for a meaningful baseline? (Lab guide suggests ≥20; harder entries may need to be expanded in W6.)
2. Should format be weighted differently for edge entries? (The current judge applies the same 3-dimension rubric; graceful refusals don't have an "accuracy" in the normal sense.)
3. Is a 3-round cap on critic-creator too few? (g015 is complex; 3 rounds may not reach 3.5 threshold.)
