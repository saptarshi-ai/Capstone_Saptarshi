# Golden Set Notes — Finance & Revenue Policy Q&A

**Capstone:** Corporate Finance & Revenue Policy Q&A Assistant
**Golden set:** `data/golden_set.jsonl`
**Date locked:** 2026-08-26
**Validator output:** `{'path': 'data/golden_set.jsonl', 'n': 20, 'coverage': {'happy-path': 14, 'harder': 4, 'edge': 2}}`

---

## Coverage mix

14 happy-path / 4 harder / 2 edge — matches the W5 lesson-plan target exactly.

**Happy-path topics (g001–g014):**
1. g001 — Cash-basis vs accrual-basis accounting (revenue recognition fundamentals)
2. g002 — SaaS subscription revenue recognition (ratable over term)
3. g003 — CFO pre-approval expense categories
4. g004 — Customer refund in a different financial period
5. g005 — Capitalising vs expensing software development costs (ASC 350-40)
6. g006 — Intercompany transaction elimination at consolidation
7. g007 — Related-party transaction disclosure thresholds
8. g008 — IFRS 16 lease accounting (right-of-use asset + lease liability)
9. g009 — Bad debt write-off documentation requirements
10. g010 — Foreign currency transaction gain/loss recording
11. g011 — Provision recognition: three-condition test
12. g012 — Goodwill impairment testing (annual + indicators)
13. g013 — Employee travel expense reimbursement process
14. g014 — Variable consideration in customer contracts (ASC 606)

**Harder topics (g015–g018):**
- g015 — Contract modification: separate contract vs. existing (multi-hop: modification rules × standalone selling price assessment)
- g016 — Post-close journal correction for wrong intercompany account code (multi-hop: journal policy × intercompany policy)
- g017 — Perpetual licence + mandatory support: one or two performance obligations (conditional: depends on software's standalone functionality)
- g018 — IFRS 16 lease term with renewal options + rent waiver (multi-hop: lease term assessment × incentive treatment)

**Edge topics (g019–g020):**
- g019 — Cryptocurrency treasury investment (genuinely out of scope; correct answer = graceful refusal + redirect to CFO/Treasury)
- g020 — Singapore tax rate for our operations (jurisdiction-specific tax rates out of scope; correct answer = redirect to Tax function + offer to help with deferred tax accounting)

---

## Sourcing

**Primary source:** Standard accounting principles — IFRS (IAS 12, IAS 37, IFRS 16), US GAAP (ASC 350-40, ASC 606), general corporate finance policy norms. All ideal answers are grounded in publicly documented standards; no proprietary company policy invented.

**Method:** Questions sourced from common queries FP&A analysts raise during month-end close and audit cycles. Topics selected by mapping the 5 most common finance policy areas: revenue recognition, expense management, intercompany, lease accounting, and financial instruments.

**Happy-path quality:** Each happy-path entry covers a distinct policy area (no duplicate topics). Ideal answers state the key rule + one concrete example or threshold where relevant.

**Harder quality:** Each harder entry explicitly requires combining two policy areas or applying a conditional rule. Notes field documents which combination is being tested.

**Edge quality:** Both edges are genuinely out of scope — not because the corpus is incomplete, but because the questions require specialist input (treasury strategy, jurisdiction tax law) that a finance policy Q&A assistant should not attempt to answer.

---

## Hardest to write

The **harder entries** were the most difficult. The challenge: a multi-hop question needs to be hard enough that a naive LLM gets it wrong, but not so obscure that it's unfair. g017 (perpetual licence + support as one vs. two performance obligations) required careful framing — the right answer depends on whether the software is "functional standalone," which is a judgement call that the ideal answer needs to frame without being circular.

The **edge entries** were easier to write than expected: once the domain is clearly Finance Policy (not tax law, not treasury strategy), the out-of-scope cases are obvious. The main care was ensuring the ideal answer for both edge cases includes a positive redirect — not just "I can't answer this" but "here's who can."

The **happy-path entries** were fastest to write but required the most editorial discipline: the temptation is to write 14 revenue recognition questions. Forcing coverage across 7+ policy areas (revenue, expenses, intercompany, FX, provisions, leases, disclosures) produces a golden set that actually tests the system rather than one policy area in depth.
