# Judge Calibration — W5 Take-Home Activity
**Capstone:** Corporate Finance & Revenue Policy Q&A Assistant
**Date:** 2026-08-26
**Evaluator:** Saptarshi Sengupta

---

## Purpose

Verify that the LLM judge rubric is calibrated against human judgment before using it to score all 20 golden entries. The target is:
- **Exact agreement ≥ 70%** on each dimension (accuracy, groundedness, format)
- **Within-1 agreement ≥ 95%** (scores differ by at most 1 point)

---

## Rubric (reminder)

Each dimension scored 1–4:

| Score | Accuracy | Groundedness | Format |
|-------|----------|-------------|--------|
| 1 | Significant factual error | Hallucinated content | Disorganised / unhelpful |
| 2 | Mostly correct, material omission | Plausible but goes beyond policy | Readable but missing structure |
| 3 | Correct, minor omissions | Grounded in standard norms | Clear, well-organised |
| 4 | Fully accurate, no unsupported claims | Fully traceable, cites standards | Finance-professional ready |

---

## Human Scores (blind — scored before seeing LLM output)

The 10 entries below were scored manually against the ideal answer in `golden_set.jsonl`.
Candidate answers are synthetic LLM outputs generated at `temperature=0.0` with `gpt-4o-mini`.

| Entry | Question (snippet) | Human Acc | Human Grd | Human Fmt | Notes |
|-------|-------------------|-----------|-----------|-----------|-------|
| g001 | Cash-basis vs accrual-basis accounting | 3 | 3 | 3 | Candidate correct on both definitions, missed mention of GAAP threshold |
| g002 | Revenue for SaaS subscription | 4 | 3 | 3 | Correct ratable recognition and deferred revenue treatment; didn't cite ASC 606 |
| g003 | CFO pre-approval expense categories | 3 | 2 | 3 | Correct categories but invented specific $ thresholds not in the golden answer |
| g004 | Customer refund in different period | 3 | 3 | 3 | Correct treatment for closed period; missed the "material enough for restatement" nuance |
| g005 | Capitalising vs expensing software costs | 4 | 4 | 4 | Cited ASC 350-40 correctly, named all three stages, mentioned amortisation period |
| g006 | Intercompany eliminations | 4 | 3 | 4 | Fully correct; didn't mention the requirement for designated account codes |
| g009 | Bad debt write-off documentation | 3 | 3 | 4 | Listed correct steps; missed the two-notice timing requirement (30 days apart) |
| g011 | Provision recognition conditions | 4 | 4 | 4 | All three conditions correct; correctly stated contingent liability threshold |
| g015 | Contract modification — separate or not | 3 | 3 | 3 | Harder entry. Correct test stated but explanation of the SSP link was thin |
| g019 | Crypto treasury investment (edge — refusal) | 4 | 4 | 3 | Correctly refused; redirect was vague, didn't mention CFO/Treasury specifically |

---

## LLM Judge Scores

*(To be filled in after running `python scripts/run_eval.py --limit 10 --label calibration-001`)*

| Entry | LLM Acc | LLM Grd | LLM Fmt |
|-------|---------|---------|---------|
| g001 | — | — | — |
| g002 | — | — | — |
| g003 | — | — | — |
| g004 | — | — | — |
| g005 | — | — | — |
| g006 | — | — | — |
| g009 | — | — | — |
| g011 | — | — | — |
| g015 | — | — | — |
| g019 | — | — | — |

---

## Agreement Analysis

*(To be filled after LLM scores are obtained)*

| Dimension | Exact Matches | Exact Agreement % | Within-1 Matches | Within-1 % |
|-----------|--------------|-------------------|-----------------|------------|
| Accuracy | — / 10 | — | — / 10 | — |
| Groundedness | — / 10 | — | — / 10 | — |
| Format | — / 10 | — | — / 10 | — |

**Target:** Exact ≥ 70%, Within-1 ≥ 95%

---

## Observations and Rubric Adjustments

*(To be completed after calibration run)*

**What the LLM judge did well:**


**Where the LLM judge diverged from human scores:**


**Rubric adjustments made (if any):**
- None required if within-1 ≥ 95%
- If groundedness is consistently overscored: add anchor text to the rubric noting that "answers referencing correct accounting standards but not citing a specific clause should score 3, not 4"

---

## Conclusion

- [ ] Exact agreement ≥ 70% on all three dimensions → **PASS**
- [ ] Within-1 agreement ≥ 95% on all three dimensions → **PASS**
- [ ] Rubric accepted for full 20-entry eval run → **PROCEED**

*Fill in checkboxes after running the calibration eval.*
