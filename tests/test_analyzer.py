import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.analyzer import _read_key_files, analyze_repository

# テスト用ダミーリポジトリ構造をtmp_pathで作る
@pytest.fixture
def dummy_repo(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# Test Algorithm\nThis is a test.", encoding="utf-8")
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    py_file = src_dir / "scorer.py"
    py_file.write_text("def score(tweet): return 1.0", encoding="utf-8")
    return tmp_path


def test_read_key_files_returns_string(dummy_repo):
    # Arrange / Act
    content = _read_key_files(str(dummy_repo))

    # Assert
    assert isinstance(content, str)
    assert "Test Algorithm" in content


def test_read_key_files_nonexistent_path():
    # Arrange / Act / Assert
    with pytest.raises(FileNotFoundError):
        _read_key_files("/nonexistent/path")


def test_read_key_files_truncates_at_limit(dummy_repo):
    # Arrange: 大きなファイルを作る
    big_file = dummy_repo / "big.md"
    big_file.write_text("x" * 100_000, encoding="utf-8")

    # Act
    content = _read_key_files(str(dummy_repo), max_chars=50_000)

    # Assert
    assert len(content) <= 50_000 + 1000  # バッファ込みで


def test_analyze_repository_returns_dict(dummy_repo):
    # Arrange
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"topic": "scoring", "summary": "test", "marketing_insights": ["insight1"]}')]

    with patch("anthropic.Anthropic") as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create.return_value = mock_message

        # Act
        result = analyze_repository(str(dummy_repo), "sk-test", "scoring")

    # Assert
    assert isinstance(result, dict)
    assert "topic" in result


def test_analyze_repository_invalid_json_returns_fallback(dummy_repo):
    # Arrange: Claude が不正な JSON を返す場合
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="これはJSONじゃない")]

    with patch("anthropic.Anthropic") as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create.return_value = mock_message

        # Act
        result = analyze_repository(str(dummy_repo), "sk-test", "scoring")

    # Assert: エラーにならずフォールバック構造が返る
    assert isinstance(result, dict)
    assert result.get("topic") == "scoring"
