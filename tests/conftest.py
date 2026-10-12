"""Test-session defaults.

Modules in both code tracks build OpenAI clients at import time. Tests never call
the API, so a placeholder key lets them import when CI has no OPENAI_API_KEY secret.
"""
import os
import sys
from pathlib import Path

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "test-placeholder-key"

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
