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


from src.models.openai_gpt import OpenAIGPTAdapter
from src.models.grok import GrokAdapter
import openai

def test_gpt_returns_text():
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="GPTの回答"))]
    with patch("openai.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = mock_resp
        result = OpenAIGPTAdapter().chat([{"role": "user", "content": "test"}], "sk-test")
    assert result == "GPTの回答"

def test_gpt_invalid_key_returns_error():
    exc = openai.AuthenticationError.__new__(openai.AuthenticationError)
    with patch("openai.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.side_effect = exc
        result = OpenAIGPTAdapter().chat([{"role": "user", "content": "test"}], "bad")
    assert "APIキーが正しくありません" in result

def test_gpt_model_name():
    assert OpenAIGPTAdapter().model_name == "gpt"

def test_grok_model_name():
    assert GrokAdapter().model_name == "grok"

def test_grok_uses_xai_base_url():
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="Grokの回答"))]
    with patch("openai.OpenAI") as MockClient:
        MockClient.return_value.chat.completions.create.return_value = mock_resp
        GrokAdapter().chat([{"role": "user", "content": "test"}], "xai-test")
        call_kwargs = MockClient.call_args[1]
    assert "x.ai" in call_kwargs.get("base_url", "")


import sys
import types

# google.generativeai がインストールされていない環境でも patch できるよう
# sys.modules に仮モジュールを登録しておく
_fake_genai = types.ModuleType("google.generativeai")
_fake_google = types.ModuleType("google")
_fake_google.generativeai = _fake_genai
sys.modules.setdefault("google", _fake_google)
sys.modules.setdefault("google.generativeai", _fake_genai)

from src.models.gemini import GeminiAdapter

def test_gemini_returns_text():
    mock_response = MagicMock()
    mock_response.text = "Geminiの回答"
    mock_chat = MagicMock()
    mock_chat.send_message.return_value = mock_response
    mock_model = MagicMock()
    mock_model.start_chat.return_value = mock_chat
    with patch("google.generativeai.configure", create=True), \
         patch("google.generativeai.GenerativeModel", return_value=mock_model, create=True):
        result = GeminiAdapter().chat([{"role": "user", "content": "test"}], "AIza-test")
    assert result == "Geminiの回答"

def test_gemini_model_name():
    assert GeminiAdapter().model_name == "gemini"
