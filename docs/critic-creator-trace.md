# Critic-Creator Trace — g015

**Golden ID:** g015
**Date:** 2026-08-26
**Creator model:** gpt-4o-mini
**Critic model:** gpt-4o
**Max rounds:** 3
**Threshold:** 3.5 / 4.0
**Starting prompt:** `data/prompt-v1.txt`

> **Note:** Run `python scripts/run_critic_creator.py --golden-id g015 --max-rounds 3 --threshold 3.5 --output docs/critic-creator-trace.md` in Vocareum to replace this template with the real trace.

---

## Question (g015)

A customer signed a 12-month SaaS contract for $120,000. After 3 months, they want to add a new module for an additional $30,000 per year, effective immediately. Should this be treated as a separate contract or a modification of the existing one?

---

## Ideal answer (reference)

Under ASC 606 (IFRS 15), a contract modification is treated as a **separate contract** only if two conditions are both met: (1) the modification adds distinct goods or services, and (2) the price reflects the standalone selling price of those additions.

For the new module to be a separate contract, the additional $30,000 must equal (or approximate) its standalone selling price. If the new module is functionally distinct from the original SaaS service and $30,000 reflects its standalone price, it is a separate contract — both contracts continue independently.

If either condition fails (e.g., the module is not distinct because it requires the base product to function, or $30,000 is discounted), the modification merges with the original contract. The combined revenue ($150,000 at month 4 = $120k + $30k annualised) is then recognised over the remaining term using a cumulative catch-up or prospective adjustment depending on whether the performance obligation is fully or partially satisfied.

The critical judgement is whether the new module has standalone functionality.

---

## Round 1

**Quality score:** [TBD — run in Vocareum]

**Prompt used:**
```
[prompt-v1 content — minimal system prompt]
```

**Generated answer:** [TBD]

**Flaw identified:** [TBD — e.g., "Model states the rule correctly but does not address the standalone functionality test or price comparison step."]

**Prompt patch:** [TBD — e.g., "When a contract modification question involves SaaS or software, always address both the distinct-goods test AND the standalone selling price test before stating the conclusion."]

---

## Round 2

**Quality score:** [TBD]

**Prompt used:**
```
[prompt-v1 + round 1 patch]
```

**Generated answer:** [TBD]

**Flaw identified:** [TBD]

**Prompt patch:** [TBD]

---

## Round 3 (if early stop not triggered)

**Quality score:** [TBD]

**Prompt used:**
```
[prompt-v1 + round 1 patch + round 2 patch]
```

**Generated answer:** [TBD]

**Flaw identified:** [TBD — or "None — quality threshold reached"]

**Prompt patch:** [TBD — or "N/A — loop stopped"]

---

## Final prompt (after all patches)

```
[TBD — paste from script output]
```

## Final answer

[TBD — paste from script output]

---

## Summary

| | Value |
|---|---|
| Rounds run | [TBD] |
| Early stop | [TBD] |
| Starting quality score | [TBD] |
| Final quality score | [TBD] |
| Score improvement | [TBD] |

**Why g015 was chosen:** This entry is the hardest in the golden set. It requires two simultaneous judgements: (1) is the new module a distinct performance obligation? and (2) does the modification price reflect standalone selling price? A naive LLM collapses this to one test. Iterative prompt patching can force it to address both.

**What the patches targeted:** Expected to patch in instructions about addressing both ASC 606 modification tests explicitly, then about including the cumulative catch-up vs prospective adjustment distinction, then about the specific "standalone functionality" language.
