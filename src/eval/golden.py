"""
Golden set loader for the Finance & Revenue Policy Q&A capstone.

Each line in the JSONL file must have:
  id           str  — unique identifier, e.g. "g001"
  question     str  — the question posed to the RAG assistant
  ideal_answer str  — the ground-truth answer
  notes        str  — starts with bucket prefix: "happy-path.", "harder.", "edge."

Public API
----------
load_golden_set(path)  — returns list of dicts
iter_golden_set(path)  — generator version
"""

import json
from pathlib import Path
from typing import Generator

DEFAULT_PATH = Path(__file__).parent.parent.parent / "data" / "golden_set.jsonl"

REQUIRED_FIELDS = {"id", "question", "ideal_answer", "notes"}
VALID_BUCKETS = {"happy-path", "harder", "edge"}


def _parse_bucket(notes: str) -> str:
    """Extract the bucket prefix from the notes field."""
    prefix = notes.split(".")[0].strip()
    return prefix if prefix in VALID_BUCKETS else "unknown"


def load_golden_set(path: str | Path = DEFAULT_PATH) -> list[dict]:
    """
    Load all entries from the golden set JSONL file.

    Returns a list of dicts; each dict has the original fields plus
    a derived 'bucket' key ('happy-path', 'harder', or 'edge').
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Golden set not found: {path}")

    entries = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {lineno}: {exc}") from exc

            missing = REQUIRED_FIELDS - entry.keys()
            if missing:
                raise ValueError(f"Line {lineno} missing fields: {missing}")

            entry["bucket"] = _parse_bucket(entry["notes"])
            entries.append(entry)

    return entries


def iter_golden_set(path: str | Path = DEFAULT_PATH) -> Generator[dict, None, None]:
    """Generator version — avoids loading everything into memory at once."""
    for entry in load_golden_set(path):
        yield entry


def describe_golden_set(path: str | Path = DEFAULT_PATH) -> dict:
    """Print a short summary of the golden set composition."""
    entries = load_golden_set(path)
    from collections import Counter
    buckets = Counter(e["bucket"] for e in entries)
    return {
        "total": len(entries),
        "by_bucket": dict(buckets),
        "ids": [e["id"] for e in entries],
    }


def validate_golden_set(path: str | Path = DEFAULT_PATH) -> dict:
    """
    Validate the golden set and return a summary.
    Raises ValueError if any entry is malformed.
    """
    entries = load_golden_set(path)
    from collections import Counter
    buckets = Counter(e["bucket"] for e in entries)
    summary = {
        "path": str(path),
        "n": len(entries),
        "coverage": dict(buckets),
        "ids": [e["id"] for e in entries],
        "valid": True,
    }
    return summary


if __name__ == "__main__":
    import pprint
    summary = validate_golden_set()
    pprint.pprint(summary)
