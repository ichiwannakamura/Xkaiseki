import pytest
from unittest.mock import MagicMock, patch
from src.chat_engine import build_prompt, chat

SAMPLE_KB_SECTIONS = [
    {
        "section": "scoring",
        "data": {
            "signals": ["like", "reply"],
            "marketing_insight": "いいねは重要"
        }
    }
]

SAMPLE_HISTORY = [
    {"role": "user", "content": "前の質問"},
    {"role": "assistant", "content": "前の回答"}
]


def test_build_prompt_contains_question():
    # Arrange
    question = "いいねの影響は？"

    # Act
    messages = build_prompt(question, SAMPLE_KB_SECTIONS, [])

    # Assert
    user_msg = next(m for m in messages if m["role"] == "user")
    assert question in user_msg["content"]


def test_build_prompt_contains_kb_context():
    # Arrange
    question = "テスト"

    # Act
    messages = build_prompt(question, SAMPLE_KB_SECTIONS, [])

    # Assert
    user_msg = next(m for m in messages if m["role"] == "user")
    assert "scoring" in user_msg["content"]


def test_build_prompt_history_sliding_window():
    # Arrange: 12往復（24メッセージ）の履歴を用意
    long_history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg{i}"}
        for i in range(24)
    ]

    # Act
    messages = build_prompt("質問", [], long_history)

    # Assert: 直近10往復（20メッセージ）のみ含まれる
    # 最後のuserメッセージは質問本文なので除外してカウント
    history_msgs = [m for m in messages if m["content"] != "質問"]
    assert len(history_msgs) <= 20


def test_build_prompt_no_kb_sections():
    # Arrange
    question = "一般的な質問"

    # Act
    messages = build_prompt(question, [], [])

    # Assert: エラーにならない
    assert len(messages) >= 1


def test_chat_returns_string():
    # Arrange
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="テスト回答")]

    with patch("anthropic.Anthropic") as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create.return_value = mock_message

        # Act
        result = chat("質問", "sk-test", {}, [])

    # Assert
    assert isinstance(result, str)
    assert len(result) > 0


def test_chat_invalid_api_key_returns_error_message():
    # Arrange
    import anthropic

    with patch("anthropic.Anthropic") as MockAnthropic:
        mock_client = MockAnthropic.return_value
        # __new__ を使って httpx.Response なしでインスタンス化する
        exc = anthropic.AuthenticationError.__new__(anthropic.AuthenticationError)
        mock_client.messages.create.side_effect = exc

        # Act
        result = chat("質問", "invalid-key", {}, [])

    # Assert
    assert "APIキーが正しくありません" in result


def test_chat_rate_limit_returns_error_message():
    # Arrange
    import anthropic

    with patch("anthropic.Anthropic") as MockAnthropic:
        mock_client = MockAnthropic.return_value
        # __new__ を使って httpx.Response なしでインスタンス化する
        exc = anthropic.RateLimitError.__new__(anthropic.RateLimitError)
        mock_client.messages.create.side_effect = exc

        # Act
        result = chat("質問", "sk-test", {}, [])

    # Assert
    assert "しばらく待って" in result


def test_chat_timeout_returns_error_message():
    # Arrange
    import anthropic

    with patch("anthropic.Anthropic") as MockAnthropic:
        mock_client = MockAnthropic.return_value
        exc = anthropic.APITimeoutError.__new__(anthropic.APITimeoutError)
        mock_client.messages.create.side_effect = exc

        # Act
        result = chat("質問", "sk-test", {}, [])

    # Assert
    assert "タイムアウト" in result
