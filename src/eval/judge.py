"""
LLM-as-judge for the Finance & Revenue Policy Q&A capstone.

Three rubric dimensions, each scored 1–4:
  - accuracy     : factual correctness of the candidate answer
  - groundedness : answer is supported by / traceable to source documents
  - format       : answer is clear, structured, and appropriate for finance staff

Usage:
    from src.eval.judge import judge_one
    score = judge_one(question, candidate_answer, ideal_answer)
    print(score.accuracy, score.groundedness, score.format, score.reasoning)
"""

import json
import os
from openai import OpenAI
from pydantic import BaseModel
from config.settings import Settings

settings = Settings()

# ---------------------------------------------------------------------------
# Rubric prompt — finance & revenue policy domain
# ---------------------------------------------------------------------------

RUBRIC_PROMPT = """You are a senior evaluator for a Corporate Finance and Revenue Policy Q&A assistant.
Your task is to score a candidate answer against an ideal answer using three rubric dimensions.
Score each dimension 1–4 using the anchors below. Be strict — most answers land at 2 or 3.

## Dimension 1: Accuracy (factual correctness)
Does the candidate answer state facts that are correct relative to the ideal answer?
1 — Contains a significant factual error that would mislead a finance professional (e.g., wrong accounting treatment, wrong threshold, wrong standard cited).
2 — Mostly correct but omits a material fact or slightly mischaracterises a rule (e.g., says "may be capitalised" when the rule is mandatory, or gives the right answer but wrong rationale).
3 — Correct on all material facts. Minor omissions or extra detail that does not mislead.
4 — Fully accurate, matches the ideal answer on all key facts, and does not introduce unsupported claims.

## Dimension 2: Groundedness (answer traceable to source documents)
Does the candidate answer stay within what a finance policy document would support, or does it invent/extrapolate?
1 — Contains at least one invented rule, threshold, or number not supported by any reasonable policy document. Hallucinated content.
2 — Answer is plausible but includes at least one statement that goes beyond what a policy document would state (e.g., invents a specific dollar threshold, implies a rule applies universally when it is jurisdiction-specific).
3 — Answer is grounded in standard accounting principles and policy norms. No invented facts, though may not cite a specific document.
4 — Fully grounded. Every claim is traceable to a known standard (IFRS, GAAP, ASC) or a reasonable policy document. Cites source section or standard where relevant.

## Dimension 3: Format (clarity and appropriateness for finance staff)
Is the answer structured clearly and appropriately for a finance professional?
1 — Disorganised, uses jargon without explanation, or is so brief as to be unhelpful (e.g., one sentence for a multi-part policy question).
2 — Readable but missing structure that would help the reader (e.g., no numbered steps for a process question, or no distinction between the main rule and exceptions).
3 — Clear and well-organised. Uses appropriate structure (numbered steps, bullet points, or prose paragraphs as fits the question type). Appropriate length.
4 — Excellent. Finance-appropriate language, well-structured, distinguishes the rule from exceptions, cites relevant standards or thresholds where helpful. A finance professional could act on this answer directly.

## Instructions
- Score each dimension independently. Do not let one dimension bias another.
- After scoring, write one sentence of reasoning per dimension explaining the key reason for that score.
- If the question is a graceful-refusal edge case (question is out of scope), score accuracy=4 and groundedness=4 if the candidate correctly refuses and redirects; score them 1 if the candidate invents an answer.
- ALWAYS call the rate_answer tool. Never reply in plain text.
"""

# ---------------------------------------------------------------------------
# Pydantic schema for structured output
# ---------------------------------------------------------------------------

class JudgeScore(BaseModel):
    accuracy: int       # 1–4
    groundedness: int   # 1–4
    format: int         # 1–4
    reasoning: str      # one sentence per dimension, pipe-separated: "acc: ... | grd: ... | fmt: ..."


# ---------------------------------------------------------------------------
# Tool definition for OpenAI function calling
# ---------------------------------------------------------------------------

RATE_ANSWER_TOOL = {
    "type": "function",
    "function": {
        "name": "rate_answer",
        "description": "Submit rubric scores for a candidate answer.",
        "parameters": {
            "type": "object",
            "properties": {
                "accuracy": {
                    "type": "integer",
                    "description": "Accuracy score 1–4",
                    "enum": [1, 2, 3, 4]
                },
                "groundedness": {
                    "type": "integer",
                    "description": "Groundedness score 1–4",
                    "enum": [1, 2, 3, 4]
                },
                "format": {
                    "type": "integer",
                    "description": "Format score 1–4",
                    "enum": [1, 2, 3, 4]
                },
                "reasoning": {
                    "type": "string",
                    "description": "One sentence per dimension, pipe-separated: 'acc: ... | grd: ... | fmt: ...'"
                }
            },
            "required": ["accuracy", "groundedness", "format", "reasoning"]
        }
    }
}


# ---------------------------------------------------------------------------
# Core judge function
# ---------------------------------------------------------------------------

def judge_one(
    question: str,
    candidate_answer: str,
    ideal_answer: str,
    judge_model: str = "gpt-4o",
) -> JudgeScore:
    """
    Score one (question, candidate_answer, ideal_answer) triple.
    Returns a JudgeScore with accuracy, groundedness, format, reasoning.
    """
    client = OpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )

    user_message = f"""## Question
{question}

## Ideal Answer
{ideal_answer}

## Candidate Answer
{candidate_answer}

Score the Candidate Answer against the Ideal Answer using the rubric. Call rate_answer with your scores."""

    # TODO 3b — call the client
    resp = client.chat.completions.create(
        model=judge_model,
        messages=[
            {"role": "system", "content": RUBRIC_PROMPT},
            {"role": "user", "content": user_message},
        ],
        tools=[RATE_ANSWER_TOOL],
        tool_choice={"type": "function", "function": {"name": "rate_answer"}},
        temperature=0.0,
    )

    # TODO 3c — parse the tool_call into a JudgeScore
    tool_call = resp.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)

    return JudgeScore(
        accuracy=args["accuracy"],
        groundedness=args["groundedness"],
        format=args["format"],
        reasoning=args["reasoning"],
    )


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    q = "When can we recognise revenue for a subscription SaaS product?"
    ideal = (
        "Revenue for a subscription SaaS product is recognised ratably over the subscription period "
        "(straight-line), as the performance obligation is the ongoing availability of the service. "
        "For example, a $12,000 annual subscription billed upfront is recognised as $1,000/month "
        "over 12 months. The upfront cash is recorded as deferred revenue and released monthly."
    )
    candidate = (
        "SaaS subscription revenue is recognised over the contract period. "
        "A $12,000 annual deal would be $1,000 per month."
    )

    score = judge_one(q, candidate, ideal)
    print(f"accuracy={score.accuracy} groundedness={score.groundedness} format={score.format}")
    print(f"reasoning: {score.reasoning}")
