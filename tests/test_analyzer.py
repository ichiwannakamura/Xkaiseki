import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.analyzer import _read_key_files, analyze_repositories_combined

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


def test_analyze_repositories_combined_returns_dict(dummy_repo):
    # Arrange: 両リポジトリとも dummy_repo を使用
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"topic": "scoring", "summary": "統合テスト要約", "marketing_insights": ["insight1", "insight2"]}')]

    with patch("anthropic.Anthropic") as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create.return_value = mock_message

        # Act
        result = analyze_repositories_combined(str(dummy_repo), str(dummy_repo), "sk-test", "scoring")

    # Assert
    assert isinstance(result, dict)
    assert result.get("topic") == "scoring"
    assert isinstance(result.get("marketing_insights"), list)


def test_analyze_repositories_combined_passes_both_repos_in_prompt(dummy_repo):
    # Arrange: プロンプトに両リポジトリの内容が含まれることを確認
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"topic": "scoring", "summary": "test", "marketing_insights": []}')]

    with patch("anthropic.Anthropic") as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create.return_value = mock_message

        # Act
        analyze_repositories_combined(str(dummy_repo), str(dummy_repo), "sk-test", "scoring")

        # Assert: messages.create が1回呼ばれ、プロンプトに両リポジトリのラベルが含まれる
        call_args = mock_client.messages.create.call_args
        prompt_content = call_args[1]["messages"][0]["content"]
        assert "x-algorithm-main" in prompt_content
        assert "the-algorithm-main" in prompt_content


def test_analyze_repositories_combined_invalid_json_returns_fallback(dummy_repo):
    # Arrange: Claude が不正な JSON を返す場合
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="これはJSONじゃない")]

    with patch("anthropic.Anthropic") as MockAnthropic:
        mock_client = MockAnthropic.return_value
        mock_client.messages.create.return_value = mock_message

        # Act
        result = analyze_repositories_combined(str(dummy_repo), str(dummy_repo), "sk-test", "scoring")

    # Assert: エラーにならずフォールバック構造が返る
    assert isinstance(result, dict)
    assert result.get("topic") == "scoring"
    assert result.get("marketing_insights") == []
