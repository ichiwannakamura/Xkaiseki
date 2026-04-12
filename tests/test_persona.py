# tests/test_persona.py
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.persona import PersonaManager, PersonaProfile

# ── テスト用固定プロフィール ──────────────────────────────────────

SAMPLE_PROFILE = PersonaProfile(
    tone="カジュアル・フレンドリー",
    sentence_length="短め 15〜25字",
    vocabulary=["なるほど", "マジで", "すごい", "めっちゃ", "やばい"],
    expressions=["ってか", "だよね〜", "まじかよ"],
    emoji_usage="よく使う: 😊🔥",
    formality="タメ口メイン、語尾〜だよ・〜じゃん",
    writing_quirks=["文末に「笑」をつける", "長い文を短く切る"],
    raw_analysis="カジュアルで親しみやすい文体。短い文を好み、絵文字を積極的に使う。",
)


# ── parse_tweets_csv ──────────────────────────────────────────────

def test_parse_tweets_csv_extracts_text():
    csv_content = "full_text,id\nこんにちは世界,1\nRT @user: リツイート,2\n今日も頑張る！,3"
    result = PersonaManager.parse_tweets_csv(csv_content)
    assert "こんにちは世界" in result
    assert "今日も頑張る！" in result


def test_parse_tweets_csv_excludes_retweets():
    csv_content = "full_text,id\nRT @a: 転載,1\n普通のツイート,2"
    result = PersonaManager.parse_tweets_csv(csv_content)
    assert not any(t.startswith("RT ") for t in result)
    assert "普通のツイート" in result


def test_parse_tweets_csv_fallback_text_column():
    csv_content = "text,id\nテキスト列のツイート,1"
    result = PersonaManager.parse_tweets_csv(csv_content)
    assert "テキスト列のツイート" in result


# ── parse_tweets_js ───────────────────────────────────────────────

def test_parse_tweets_js_extracts_text():
    js_data = [
        {"tweet": {"full_text": "テストツイート1"}},
        {"tweet": {"full_text": "RT @someone: リツイート"}},
        {"tweet": {"full_text": "テストツイート2"}},
    ]
    js_content = f"window.YTD.tweets.part0 = {json.dumps(js_data)}"
    result = PersonaManager.parse_tweets_js(js_content)
    assert "テストツイート1" in result
    assert "テストツイート2" in result


def test_parse_tweets_js_excludes_retweets():
    js_data = [
        {"tweet": {"full_text": "RT @a: リツイート"}},
        {"tweet": {"full_text": "オリジナル投稿"}},
    ]
    js_content = f"window.YTD.tweets.part0 = {json.dumps(js_data)}"
    result = PersonaManager.parse_tweets_js(js_content)
    assert not any(t.startswith("RT ") for t in result)


def test_parse_tweets_js_invalid_format():
    with pytest.raises(Exception):
        PersonaManager.parse_tweets_js("not valid js content {{{")


# ── combine_samples ───────────────────────────────────────────────

def test_combine_samples_respects_item_limit():
    texts = [f"サンプル{i}" for i in range(100)]
    result = PersonaManager.combine_samples(texts)
    # 60件ならセパレータは59個
    assert result.count("---") <= 59


def test_combine_samples_respects_char_limit():
    texts = ["あ" * 500] * 100
    result = PersonaManager.combine_samples(texts)
    assert len(result) <= 8000


def test_combine_samples_empty():
    result = PersonaManager.combine_samples([])
    assert result == ""


# ── analyze_style ─────────────────────────────────────────────────

def test_analyze_style_creates_profile(tmp_path):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text=json.dumps(
                {
                    "tone": "カジュアル",
                    "sentence_length": "短め",
                    "vocabulary": ["テスト語彙"],
                    "expressions": ["だよ"],
                    "emoji_usage": "よく使う",
                    "formality": "タメ口",
                    "writing_quirks": ["短文"],
                    "raw_analysis": "テスト分析テキスト",
                }
            )
        )
    ]
    mock_client.messages.create.return_value = mock_response

    manager = PersonaManager(profile_path=tmp_path / "persona.json")
    with patch("src.persona.anthropic.Anthropic", return_value=mock_client):
        profile = manager.analyze_style("サンプルテキスト", "fake-key")

    assert profile.tone == "カジュアル"
    assert profile.vocabulary == ["テスト語彙"]


def test_analyze_style_saves_to_disk(tmp_path):
    path = tmp_path / "persona.json"
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text=json.dumps(
                {
                    "tone": "T",
                    "sentence_length": "S",
                    "vocabulary": [],
                    "expressions": [],
                    "emoji_usage": "E",
                    "formality": "F",
                    "writing_quirks": [],
                    "raw_analysis": "R",
                }
            )
        )
    ]
    mock_client.messages.create.return_value = mock_response

    manager = PersonaManager(profile_path=path)
    with patch("src.persona.anthropic.Anthropic", return_value=mock_client):
        manager.analyze_style("サンプル", "fake-key")

    assert path.exists()


def test_analyze_style_raises_on_bad_response(tmp_path):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="JSONを含まないテキスト")]
    mock_client.messages.create.return_value = mock_response

    manager = PersonaManager(profile_path=tmp_path / "persona.json")
    with patch("src.persona.anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(ValueError, match="JSON"):
            manager.analyze_style("サンプル", "fake-key")


# ── build_system_prompt ───────────────────────────────────────────

def test_build_system_prompt_contains_profile_data():
    manager = PersonaManager.__new__(PersonaManager)
    manager.profile = SAMPLE_PROFILE
    prompt = manager.build_system_prompt()
    assert "分身ペルソナ" in prompt
    assert "カジュアル・フレンドリー" in prompt
    assert "なるほど" in prompt
    assert "文末に「笑」をつける" in prompt


def test_build_system_prompt_raises_without_profile():
    manager = PersonaManager.__new__(PersonaManager)
    manager.profile = None
    with pytest.raises(ValueError, match="未作成"):
        manager.build_system_prompt()


# ── rewrite_text ──────────────────────────────────────────────────

def test_rewrite_text_returns_response(tmp_path):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="書き直されたテキストです")]
    mock_client.messages.create.return_value = mock_response

    manager = PersonaManager(profile_path=tmp_path / "persona.json")
    manager.profile = SAMPLE_PROFILE

    with patch("src.persona.anthropic.Anthropic", return_value=mock_client):
        result = manager.rewrite_text("元のテキスト", "fake-key")

    assert result == "書き直されたテキストです"


def test_rewrite_text_passes_system_prompt(tmp_path):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="結果")]
    mock_client.messages.create.return_value = mock_response

    manager = PersonaManager(profile_path=tmp_path / "persona.json")
    manager.profile = SAMPLE_PROFILE

    with patch("src.persona.anthropic.Anthropic", return_value=mock_client):
        manager.rewrite_text("テスト", "fake-key")

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert "system" in call_kwargs
    assert "分身ペルソナ" in call_kwargs["system"]


# ── save / load / delete profile ─────────────────────────────────

def test_init_does_not_auto_load(tmp_path):
    """__init__ はディスクを読まず、常に profile=None で開始する。"""
    path = tmp_path / "persona.json"
    # ファイルが存在していても init では読み込まない
    manager_seed = PersonaManager(profile_path=path)
    manager_seed.profile = SAMPLE_PROFILE
    manager_seed._save_profile()

    manager_new = PersonaManager(profile_path=path)
    assert manager_new.profile is None


def test_load_profile_from_disk_returns_profile(tmp_path):
    """load_profile_from_disk() を明示的に呼んだときだけ読み込まれる。"""
    path = tmp_path / "persona.json"
    manager = PersonaManager(profile_path=path)
    manager.profile = SAMPLE_PROFILE
    manager._save_profile()
    manager.profile = None  # リセット

    loaded = manager.load_profile_from_disk()
    assert loaded is not None
    assert loaded.tone == SAMPLE_PROFILE.tone
    assert manager.profile is loaded


def test_load_profile_from_disk_returns_none_when_missing(tmp_path):
    manager = PersonaManager(profile_path=tmp_path / "missing.json")
    result = manager.load_profile_from_disk()
    assert result is None
    assert manager.profile is None


def test_load_profile_from_disk_returns_none_on_corrupt_json(tmp_path):
    path = tmp_path / "persona.json"
    path.write_text("これはJSONではない", encoding="utf-8")
    manager = PersonaManager(profile_path=path)
    result = manager.load_profile_from_disk()
    assert result is None
    assert manager.profile is None


def test_has_saved_profile(tmp_path):
    path = tmp_path / "persona.json"
    manager = PersonaManager(profile_path=path)
    assert not manager.has_saved_profile()

    manager.profile = SAMPLE_PROFILE
    manager._save_profile()
    assert manager.has_saved_profile()


def test_delete_profile_clears_memory_and_disk(tmp_path):
    """delete_profile() はメモリとディスクの両方を削除する。"""
    path = tmp_path / "persona.json"
    manager = PersonaManager(profile_path=path)
    manager.profile = SAMPLE_PROFILE
    manager._save_profile()
    assert path.exists()

    manager.delete_profile()
    assert manager.profile is None
    assert not path.exists()


def test_delete_profile_no_error_when_no_file(tmp_path):
    """ファイルがなくても delete_profile() はエラーにならない。"""
    manager = PersonaManager(profile_path=tmp_path / "missing.json")
    manager.profile = SAMPLE_PROFILE
    manager.delete_profile()  # ファイルなしでも例外を出さない
    assert manager.profile is None


def test_save_and_reload_profile(tmp_path):
    """_save_profile → load_profile_from_disk の往復テスト。"""
    path = tmp_path / "persona.json"
    manager = PersonaManager(profile_path=path)
    manager.profile = SAMPLE_PROFILE
    manager._save_profile()

    manager2 = PersonaManager(profile_path=path)
    manager2.load_profile_from_disk()
    assert manager2.profile is not None
    assert manager2.profile.tone == SAMPLE_PROFILE.tone
    assert manager2.profile.vocabulary == SAMPLE_PROFILE.vocabulary
    assert manager2.profile.writing_quirks == SAMPLE_PROFILE.writing_quirks
