# tests/test_models.py
import pytest
from unittest.mock import MagicMock, patch
import anthropic
from src.models.claude import ClaudeAdapter

def test_claude_returns_text():
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Claudeの回答")]
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_msg
        result = ClaudeAdapter().chat([{"role": "user", "content": "test"}], "sk-test")
    assert result == "Claudeの回答"

def test_claude_invalid_key_returns_error():
    exc = anthropic.AuthenticationError.__new__(anthropic.AuthenticationError)
    with patch("anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.side_effect = exc
        result = ClaudeAdapter().chat([{"role": "user", "content": "test"}], "bad-key")
    assert "APIキーが正しくありません" in result

def test_claude_model_name():
    assert ClaudeAdapter().model_name == "claude"
