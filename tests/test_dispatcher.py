# tests/test_dispatcher.py
import pytest
from unittest.mock import MagicMock, patch
from src.dispatcher import dispatch

@pytest.fixture
def mock_adapters():
    with patch("src.dispatcher.ADAPTERS", {
        "claude": MagicMock(chat=MagicMock(return_value="Claudeの回答")),
        "gpt":    MagicMock(chat=MagicMock(return_value="GPTの回答")),
    }):
        yield

def test_dispatch_returns_all_model_answers(mock_adapters):
    result = dispatch(
        question="test",
        context_chunks=[],
        model_names=["claude", "gpt"],
        api_keys={"claude": "sk-c", "gpt": "sk-g"},
        history=[],
    )
    assert result["claude"] == "Claudeの回答"
    assert result["gpt"] == "GPTの回答"

def test_dispatch_missing_api_key_returns_error():
    result = dispatch(
        question="test",
        context_chunks=[],
        model_names=["claude"],
        api_keys={},
        history=[],
    )
    assert "APIキーが未設定" in result["claude"]

def test_dispatch_includes_context_in_messages():
    chunks = [{"file": "scorer.py", "chunk": "def score(): pass"}]
    mock_adapter = MagicMock(chat=MagicMock(return_value="ok"))
    fake_adapters = {"claude": mock_adapter}

    with patch("src.dispatcher.ADAPTERS", fake_adapters):
        dispatch("test", chunks, ["claude"], {"claude": "sk"}, [])

    call_args = mock_adapter.chat.call_args
    messages = call_args[0][0]
    assert any("scorer.py" in str(m) for m in messages)

def test_dispatch_unknown_model_is_skipped():
    result = dispatch(
        question="test",
        context_chunks=[],
        model_names=["unknown_model"],
        api_keys={"unknown_model": "key"},
        history=[],
    )
    assert "unknown_model" not in result
