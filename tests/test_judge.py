"""Tests for ExactMatchJudge (no API calls)."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from src.eval.judge import ExactMatchJudge

def test_exact_match_true():
    j = ExactMatchJudge()
    r = j.evaluate("The company pays 75%.", "The company pays 75%.")
    assert r["exact_match"] is True
    assert r["composite"] == 1.0

def test_exact_match_false():
    j = ExactMatchJudge()
    r = j.evaluate("The company pays 75%.", "Company pays 80%.")
    assert r["exact_match"] is False
    assert r["composite"] < 1.0

def test_case_insensitive():
    j = ExactMatchJudge()
    r = j.evaluate("hello world", "Hello World", case_sensitive=False)
    assert r["exact_match"] is True
