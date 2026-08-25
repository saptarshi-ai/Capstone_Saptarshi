# ADR 0001: Capstone Framing — Corporate Finance & Revenue Policy Q&A

**Status:** LOCKED — v1 (do not modify without creating 0001-v2)
**Date:** 2026-08-26
**Author:** Saptarshi Sengupta
**Deciders:** Self (solo capstone)

---

## 1. Context

The IIT Madras AI Engineering capstone (Module 1) requires building a RAG-based Q&A assistant for a domain that meets three criteria: (a) there is a clear expert audience with real questions, (b) the corpus is sourceable without legal risk, and (c) a "correctness" standard exists against which LLM answers can be judged.

Three domains were evaluated before locking:

| Domain | Pro | Con |
|--------|-----|-----|
| Personal AU property Q&A | Rich real data available | Privacy risk; corpus is proprietary |
| Public equity research | Interesting; dense corpus | Real-time data dependency; IP complexity |
| **Corporate Finance & Revenue Policy** | Clear standard (IFRS/GAAP); FP&A analyst is real primary user; corpus is open standards | No retrieval corpus yet — must be built |

Corporate Finance & Revenue Policy was selected.

---

## 2. Decision

**Capstone domain:** Corporate Finance & Revenue Policy Q&A Assistant.

The system answers questions that FP&A analysts, controllers, and finance business partners ask during month-end close, budget cycles, and external audit preparation. Questions span revenue recognition (ASC 606, IFRS 15), lease accounting (IFRS 16, ASC 842), expense management, intercompany eliminations, provisions (IAS 37), and financial instruments (IAS 32/39/IFRS 9).

**Out of scope by design:** jurisdiction-specific tax rates, treasury/investment strategy, HR policy, legal advice. These categories are handled via graceful refusal + redirect in the golden set (g019, g020).

---

## 3. Technology stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| LLM | gpt-4o-mini (candidate) + gpt-4o (judge) | Cost: mini for generation; full 4o for judging |
| Embedding | text-embedding-ada-002 (W6 wire-up) | Standard; already in cohort toolchain |
| Vector store | ChromaDB (in-process, W6) | No infra; easy local dev |
| API | FastAPI + uvicorn | Cohort standard from W4 |
| Persistence | SQLite via store.py | Zero-dependency; answers + eval_runs tables |
| API gateway | Vocareum OpenAI proxy | Lab requirement; OPENAI_BASE_URL override |

---

## 4. Scope for Module 1 (W5 deliverables)

Module 1 is the evaluation infrastructure only. No retrieval is wired yet — W5 establishes a pre-RAG baseline so that W6 retrieval improvements are measurable.

M1 deliverables:
- 20-entry golden set (14 happy-path / 4 harder / 2 edge)
- 3-dimensional LLM judge (accuracy / groundedness / format, 1-4 scale)
- SQLite eval store (eval_runs table)
- Baseline eval run (direct LLM, no retrieval)
- Judge calibration (≥10 human scores vs LLM scores)
- Pairwise A/B comparison (prompt-v1 vs prompt-v2)
- Critic-creator trace (g015, ≤3 rounds)
- ADR v1 (this document) + DR#1 1-pager

---

## 5. Golden set design

20 entries, 14/4/2 split (happy-path / harder / edge).

**Happy-path:** Single-hop questions where one policy area applies directly. Correct answer is a 3–5 sentence statement of the rule plus a concrete example. Target score: accuracy 3.5+, groundedness 3.5+.

**Harder:** Multi-hop questions requiring two policy areas in combination, or conditional logic ("it depends on X"). Intentionally harder for a naive LLM without retrieval. Target score: accuracy 2.5–3.0 at baseline, 3.5+ after RAG.

**Edge:** Out-of-scope questions. Correct answer is graceful refusal + redirect. Scored on format (politeness, clarity of redirect) not accuracy.

---

## 6. Judge design

3 dimensions, 1-4 integer scale:

| Dimension | What it measures |
|-----------|-----------------|
| Accuracy | Factual correctness vs ideal answer |
| Groundedness | Answer stays within what is documentable; no hallucination |
| Format | Clear structure, appropriate length, finance-domain register |

Rationale for 1-4 (not 1-5 or binary): odd-point scales allow fence-sitting in the middle; binary collapses nuance; 1-4 forces the judge to pick a side (better or worse than adequate). See ADR-0002 for full rubric rationale.

Implementation: forced tool-call (`rate_answer`) prevents the judge from returning free-text. JudgeScore Pydantic model validates all three dimensions.

---

## 7. Baseline hypothesis

Without retrieval, a direct LLM call using gpt-4o-mini is expected to:
- Score 3.0–3.5 avg accuracy on happy-path (IFRS/GAAP well-represented in training data)
- Score 2.0–2.5 on harder questions (multi-hop fails more often)
- Score 3.5+ on format (model is generally well-formatted)
- Score lower on groundedness than accuracy (model hallucinates specific thresholds)

After RAG (W6), the hypothesis is accuracy and groundedness improve by 0.3–0.5 on harder entries.

---

## 8. Pairwise comparison design

Two prompt variants compared A/B using the full golden set:

- **prompt-v1:** Minimal system prompt ("answer based on IFRS/GAAP")
- **prompt-v2:** Structured system prompt with explicit format instructions, out-of-scope framing, and finance-specific persona

Position-flip debiasing: each pair is judged twice with A/B positions swapped. Winner declared only when both rounds agree. Ties recorded as-is.

---

## 9. Critic-creator design

Entry g015 selected for critic-creator trace: "contract modification — separate contract vs. existing." This is the most complex happy-path/harder crossover — it requires conditional reasoning about standalone selling price, making it the highest-value entry for iterative prompt improvement.

Loop: up to 3 rounds. Critic identifies worst single flaw in each answer; its prompt patch is appended to the current system prompt. Early stop if quality_score ≥ 3.5.

---

## 10. Risks and mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Vocareum API rate-limited during eval | Medium | `--limit 5` for smoke test first |
| Judge is inconsistent across runs | Medium | `temperature=0.0` on all judge calls |
| Pairwise position-bias contaminates results | High | Flip-and-both-must-agree logic in pairwise.py |
| Corpus not ready for W6 | Low | W5 baseline runs without corpus |
| Golden harder entries too hard (all 1s) | Low | g015–g018 were pilot-tested mentally; each has a clear correct answer |

---

## 11. Consequences

Locking this framing now means:
- The golden set cannot change (adding entries invalidates previous eval runs)
- Judge rubric cannot change between baseline and RAG eval (to keep scores comparable)
- The domain boundary (Finance Policy, not Tax Law or Treasury) is enforced by the golden set's edge cases

Changes to any of the above require creating a new ADR version (0001-v2) and a new eval_run_label prefix.

**Next ADR:** 0002-eval-system-decisions (eval store schema, label scheme, baseline strategy) — see `docs/adr/0002-eval-system-decisions.md`.
