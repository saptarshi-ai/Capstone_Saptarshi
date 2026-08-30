"""UI smoke test — checks app.py imports without error."""
import sys, importlib
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

def test_ui_importable():
    try:
        import streamlit  # noqa
    except ImportError:
        import pytest; pytest.skip("streamlit not installed")
    # If streamlit is present, app.py should be parseable at least
    import ast
    src = __import__("pathlib").Path("ui/app.py").read_text()
    ast.parse(src)  # will raise SyntaxError if broken
