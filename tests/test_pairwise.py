"""PairwiseJudge smoke test (mocked OpenAI)."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from unittest.mock import patch, MagicMock
from src.eval.pairwise import PairwiseJudge

def test_compare_consistent_winner():
    judge = PairwiseJudge()
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = '{"winner": "A", "reason": "more accurate"}' 
    with patch.object(judge.client.chat.completions, "create", return_value=mock_resp):
        result = judge.compare("What is PTO?", "20 days PTO.", "15 days PTO.")
    assert result["winner"] in ("A", "B", "tie")
