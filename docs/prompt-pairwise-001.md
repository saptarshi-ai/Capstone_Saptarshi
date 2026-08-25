# Pairwise Comparison 001 — prompt-v1 vs prompt-v2

**Comparison ID:** pairwise-001
**Date:** 2026-08-26
**Candidate model:** gpt-4o-mini
**Judge model:** gpt-4o
**Golden entries:** 20
**Method:** Position-flip debiasing (each pair judged twice, A/B swapped; winner declared only when both rounds agree)
**Results file:** `data/pairwise-001-results.json`

> **Note:** Run `python scripts/run_pairwise.py --output data/pairwise-001-results.json` in Vocareum to replace `[TBD]` values.

---

## Prompt variants

### prompt-v1 (minimal)
```
You are a Corporate Finance and Revenue Policy assistant. Answer the question based on standard accounting principles (IFRS/GAAP). Be concise. If the question is outside your scope, say so politely.
```

### prompt-v2 (structured)
Full structured prompt with: explicit role + audience, format rules (lead with direct answer, ≤200 words, cite standard), out-of-scope list with redirect instructions. See `data/prompt-v2.txt`.

**Hypothesis:** prompt-v2 outperforms prompt-v1 on harder entries (better format instructions help multi-step reasoning) and on edge entries (explicit out-of-scope handling). Happy-path gap expected to be small.

---

## Results

| Metric | Value |
|--------|-------|
| prompt-v1 wins | [TBD] / 20 ([TBD]%) |
| prompt-v2 wins | [TBD] / 20 ([TBD]%) |
| ties | [TBD] / 20 ([TBD]%) |
| position bias events | [TBD] rounds where A/B flip changed the result |

---

## By-bucket results

| Bucket | n | prompt-v1 wins | prompt-v2 wins | ties |
|--------|---|---------------|---------------|------|
| happy-path | 14 | [TBD] | [TBD] | [TBD] |
| harder | 4 | [TBD] | [TBD] | [TBD] |
| edge | 2 | [TBD] | [TBD] | [TBD] |

---

## Analysis

*(Fill in after running)*

**Overall winner:** [TBD]

**Key findings:**

1. **Happy-path entries** — Expected: small gap (both prompts handle single-hop questions fine). Actual: [TBD]

2. **Harder entries** — Expected: prompt-v2 wins (structured format + standard citation requirement helps multi-hop reasoning). Actual: [TBD]

3. **Edge entries** — Expected: prompt-v2 wins clearly (explicit out-of-scope redirect instruction). Actual: [TBD]

4. **Position bias** — [TBD] rounds had disagreement when positions were flipped. This is [low/moderate/high] — [TBD] interpretation.

---

## Design note: what differs between v1 and v2

The key structural differences in prompt-v2 are:

- **Standard citation instruction**: "Cite the relevant standard (e.g., 'Under ASC 606...')" — expected to improve groundedness scores
- **Format rules**: lead with direct answer, ≤200 words — expected to improve format scores
- **Explicit out-of-scope list**: names three redirect categories — expected to improve edge entry scores significantly
- **Audience framing**: "supporting FP&A analysts, controllers..." — expected small improvement from domain-appropriate register

---

## Conclusion and next step

*(Fill in after running)*

If prompt-v2 wins: adopt prompt-v2 as the base system prompt for W6 RAG wiring.
If prompt-v1 wins or tie: investigate which entries flipped and why before deciding.

The winning prompt becomes `src/rag/prompts/system_prompt.txt` in W6.
