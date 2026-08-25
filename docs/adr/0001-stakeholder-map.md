# Stakeholder Map — M1 Locked
**Capstone:** Corporate Finance & Revenue Policy Q&A Assistant
**Committed:** 2026-08-25
**Status:** LOCKED for M1 (DR #1)

---

## 1. Primary User

**Finance business partners and revenue operations analysts** during month-end close and financial reporting cycles.

Specifically: accounting staff, FP&A analysts, and revenue operations managers who handle 3–8 finance-related policy questions per week — sourced from audits, expense approvals, revenue recognition decisions, or intercompany transactions. These users currently resolve questions by searching shared drives, emailing the finance controller, or reading through lengthy policy PDFs. Each query takes 10–20 minutes to resolve. Across a team of 8 analysts, that's roughly 10–20 hours per month spent on lookups that should take under 2 minutes.

---

## 2. Secondary Stakeholders

**Who else has skin in this:**

- **Finance Controller / CFO** — Sponsor. Wants consistent policy application across the team, fewer escalations to senior staff, and an auditable record of how policy questions are resolved.
- **Compliance & Internal Audit** — Gatekeeper. Any AI-generated financial guidance must cite the source document. Hallucinated policy answers create audit risk. The system must ground every response in a retrieved document excerpt.
- **IT / Information Security** — Gatekeeper. Financial policy documents may contain commercially sensitive information. Data must stay within approved infrastructure; no sending documents to third-party APIs without a data-handling agreement.
- **Revenue Operations team** — Whose work is augmented. They run revenue recognition, commission calculations, and ARR reconciliations — all governed by policy documents that rarely change but are frequently misremembered.

---

## 3. Before-AI Workflow

How finance policy questions are resolved today:

1. Analyst encounters a policy question during month-end close (e.g. "Does the refund for customer X qualify as a revenue adjustment or a credit note under our recognition policy?").
2. Searches the shared drive for the relevant policy document (~3 min, assuming they know the document name).
3. Reads through a 40–80 page PDF to find the specific clause (~10–15 min).
4. If unsure, emails the Finance Controller or FP&A lead, waits for a response (~24–48 h turnaround during close).
5. Documents the answer informally (sometimes not at all).

**Quantified cost:** ~3 policy questions per analyst per week × 15 min each × 8 analysts = **6 hours/week** lost to policy lookups, not counting escalation wait time. During quarterly close, frequency doubles.

---

## 4. Desired After-State

What changes when the RAG assistant is live:

- An analyst types a natural-language question and gets a cited, policy-grounded answer in under 10 seconds.
- Each answer includes the source document name, section, and the exact retrieved passage — so the analyst can verify and audit.
- Escalations to the Finance Controller drop by at least 50% for routine policy questions.
- Policy lookup time falls from ~15 min per question to under 2 min (including verification).
- Answers are consistently grounded in the current version of the document corpus — no more "I think the policy says…" from memory.

---

## 5. Top 3 Sponsor Metrics

All three are measurable with the eval pipeline built in W5:

| # | Metric | Target | Measurement |
|---|--------|--------|-------------|
| 1 | **Groundedness score** (answer grounded in retrieved doc) | ≥ 3.5 / 4.0 average across golden set | LLM-as-judge on eval_runs table, per eval run |
| 2 | **Retrieval hit rate** (correct source document retrieved for the question) | ≥ 85% on golden set | Manual spot-check of sources[] field in /ask response |
| 3 | **Hallucination rate** (answers with invented facts not in retrieved passage) | ≤ 10% | Judge accuracy dimension score ≤ 2 flagged as hallucination risk |

**Secondary metric (operational):** p95 response latency ≤ 5 seconds end-to-end (tracked via cost_usd proxy until real latency logging added in W6+).
