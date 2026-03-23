# Xkaiseki マルチモデル対応 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Claude・GPT・Gemini・Grok の4モデルが同時回答できるマルチモデルチャットアプリに再設計し、XアルゴリズムのソースコードをローカルSQLite DBとして索引化する。

**Architecture:** ソースコードを SQLite FTS5 でインデックス化しローカル検索。質問時に関連コード断片を取得し、選択した全モデルへ ThreadPoolExecutor で並列送信。UIはセットアップ画面（初回）とチャット画面（タブ/横並び切替）の2画面構成。

**Tech Stack:** Python 3.14, Streamlit 1.32+, anthropic, openai, google-generativeai, python-dotenv, pytest

**Worktree:** `.worktrees/feature-multimodel` (branch: `feature/multimodel`)

---

## File Map

| ファイル | 操作 | 役割 |
|---------|------|------|
| `src/config.py` | 新規作成 | .env 読み書き・セットアップ状態管理 |
| `src/models/__init__.py` | 新規作成 | パッケージ初期化 |
| `src/models/base.py` | 新規作成 | ModelAdapter 抽象基底クラス |
| `src/models/claude.py` | 新規作成 | Anthropic SDK アダプター |
| `src/models/openai_gpt.py` | 新規作成 | OpenAI SDK アダプター（GPT） |
| `src/models/grok.py` | 新規作成 | xAI API アダプター（OpenAI互換） |
| `src/models/gemini.py` | 新規作成 | Google Generativeai アダプター |
| `src/retriever.py` | 新規作成 | SQLite FTS5 検索 |
| `src/dispatcher.py` | 新規作成 | 全モデルへ並列送信・結果集約 |
| `index_source.py` | 新規作成 | ソースコードインデックス構築CLI |
| `🏠_ホーム.py` | 全面書き換え | Streamlit UI（セットアップ+チャット） |
| `src/analyzer.py` | 削除 | retriever.py に置き換え |
| `src/knowledge_base.py` | 削除 | retriever.py に置き換え |
| `src/chat_engine.py` | 削除 | dispatcher.py に置き換え |
| `generate_kb.py` | 削除 | index_source.py に置き換え |
| `tests/test_analyzer.py` | 削除 | 新テストに置き換え |
| `tests/test_knowledge_base.py` | 削除 | 新テストに置き換え |
| `tests/test_chat_engine.py` | 削除 | 新テストに置き換え |
| `tests/test_config.py` | 新規作成 | config.py のテスト |
| `tests/test_retriever.py` | 新規作成 | retriever.py のテスト |
| `tests/test_dispatcher.py` | 新規作成 | dispatcher.py のテスト |
| `tests/test_models.py` | 新規作成 | 全モデルアダプターのテスト |
| `requirements.txt` | 更新 | 新依存関係を追加 |
| `data/knowledge_base.json` | 削除 | index.db に置き換え |
| `.env.example` | 更新 | 新しいキー項目を追加 |

---

## Task 1: スキャフォールド（旧ファイル削除 + requirements.txt 更新）

**Files:**
- Delete: `src/analyzer.py`, `src/knowledge_base.py`, `src/chat_engine.py`, `generate_kb.py`, `data/knowledge_base.json`
- Delete: `tests/test_analyzer.py`, `tests/test_knowledge_base.py`, `tests/test_chat_engine.py`
- Modify: `requirements.txt`
- Modify: `.env.example`
- Create: `src/models/__init__.py`

- [ ] **Step 1: 旧ファイルを削除する**

```bash
cd .worktrees/feature-multimodel
rm src/analyzer.py src/knowledge_base.py src/chat_engine.py generate_kb.py
rm data/knowledge_base.json
rm tests/test_analyzer.py tests/test_knowledge_base.py tests/test_chat_engine.py
mkdir -p src/models
touch src/models/__init__.py
```

- [ ] **Step 2: requirements.txt を更新する**

```
streamlit>=1.32
anthropic>=0.83
openai>=1.0
google-generativeai>=0.8
python-dotenv>=1.0
pytest>=8.0
pytest-mock>=3.0
```

- [ ] **Step 3: .env.example を更新する**

```
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI (GPT)
OPENAI_API_KEY=sk-...

# Google (Gemini)
GEMINI_API_KEY=AIza...

# xAI (Grok)
GROK_API_KEY=xai-...

# 有効なモデル（カンマ区切り）
ENABLED_MODELS=claude

# 検索モード: fts または vector
SEARCH_MODE=fts
```

- [ ] **Step 4: コミットする**

```bash
git add -A
git commit -m "chore: 旧ファイルを削除しscaffoldを更新"
```

---

## Task 2: src/config.py — 設定管理

**Files:**
- Create: `src/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: テストを書く**

```python
# tests/test_config.py
import pytest
from pathlib import Path
from unittest.mock import patch
from src.config import load_config, save_config, is_setup_complete

def test_load_config_returns_dict(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=sk-test\nENABLED_MODELS=claude\nSEARCH_MODE=fts\n")
    with patch("src.config.ENV_PATH", env_file):
        config = load_config()
    assert config["claude_api_key"] == "sk-test"
    assert config["enabled_models"] == ["claude"]
    assert config["search_mode"] == "fts"

def test_save_config_writes_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.touch()
    with patch("src.config.ENV_PATH", env_file):
        save_config({"claude_api_key": "sk-new", "enabled_models": ["claude", "gpt"], "search_mode": "fts", "gpt_api_key": "", "gemini_api_key": "", "grok_api_key": ""})
    content = env_file.read_text()
    assert "sk-new" in content
    assert "claude,gpt" in content

def test_is_setup_complete_true(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=sk-test\nENABLED_MODELS=claude\nSEARCH_MODE=fts\n")
    with patch("src.config.ENV_PATH", env_file):
        assert is_setup_complete() is True

def test_is_setup_complete_false_no_key(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=\nENABLED_MODELS=claude\nSEARCH_MODE=fts\n")
    with patch("src.config.ENV_PATH", env_file):
        assert is_setup_complete() is False
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_config.py -v
# Expected: FAIL (ImportError: src.config not found)
```

- [ ] **Step 3: src/config.py を実装する**

```python
# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

ENV_PATH = Path(__file__).parent.parent / ".env"

MODEL_NAMES = ("claude", "gpt", "gemini", "grok")


def load_config() -> dict:
    """Read config from .env file."""
    load_dotenv(ENV_PATH, override=True)
    return {
        "claude_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "gpt_api_key": os.getenv("OPENAI_API_KEY", ""),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "grok_api_key": os.getenv("GROK_API_KEY", ""),
        "enabled_models": [
            m.strip()
            for m in os.getenv("ENABLED_MODELS", "").split(",")
            if m.strip()
        ],
        "search_mode": os.getenv("SEARCH_MODE", "fts"),
    }


def save_config(config: dict) -> None:
    """Write config to .env file."""
    ENV_PATH.touch()
    mapping = {
        "ANTHROPIC_API_KEY": config.get("claude_api_key", ""),
        "OPENAI_API_KEY": config.get("gpt_api_key", ""),
        "GEMINI_API_KEY": config.get("gemini_api_key", ""),
        "GROK_API_KEY": config.get("grok_api_key", ""),
        "ENABLED_MODELS": ",".join(config.get("enabled_models", [])),
        "SEARCH_MODE": config.get("search_mode", "fts"),
    }
    for key, value in mapping.items():
        set_key(str(ENV_PATH), key, value)


def is_setup_complete() -> bool:
    """Return True if at least one model is enabled and has an API key."""
    config = load_config()
    if not config["enabled_models"]:
        return False
    key_map = {
        "claude": config["claude_api_key"],
        "gpt": config["gpt_api_key"],
        "gemini": config["gemini_api_key"],
        "grok": config["grok_api_key"],
    }
    return any(key_map.get(m) for m in config["enabled_models"])
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_config.py -v
# Expected: 4 passed
```

- [ ] **Step 5: コミットする**

```bash
git add src/config.py tests/test_config.py
git commit -m "feat: src/config.py — .env読み書き・セットアップ状態管理"
```

---

## Task 3: src/models/base.py + src/models/claude.py

**Files:**
- Create: `src/models/base.py`
- Create: `src/models/claude.py`
- Create: `tests/test_models.py`（claude部分）

- [ ] **Step 1: テストを書く**

```python
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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_models.py -v
# Expected: FAIL (ImportError)
```

- [ ] **Step 3: base.py を実装する**

```python
# src/models/base.py
from abc import ABC, abstractmethod


class ModelAdapter(ABC):
    """Xkaisekiが対応する各LLMモデルの共通インターフェース。"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """モデルの識別名（config で使う短縮名）。"""
        ...

    @abstractmethod
    def chat(self, messages: list[dict], api_key: str) -> str:
        """messages を送信して回答テキストを返す。エラー時はエラーメッセージ文字列を返す。"""
        ...
```

- [ ] **Step 4: claude.py を実装する**

```python
# src/models/claude.py
import logging
import anthropic
from .base import ModelAdapter

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2048
SYSTEM_PROMPT = (
    "あなたはXの推薦アルゴリズムの専門家です。"
    "提供されたソースコードの断片を参考に、アフィリエイト運用者向けに"
    "マーケター視点（先に）と技術視点（後に）で簡潔に回答してください。"
)


class ClaudeAdapter(ModelAdapter):

    @property
    def model_name(self) -> str:
        return "claude"

    def chat(self, messages: list[dict], api_key: str) -> str:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
            if response.content and hasattr(response.content[0], "text"):
                return response.content[0].text
            return "❌ 予期しないAPI応答形式"
        except anthropic.AuthenticationError:
            return "❌ APIキーが正しくありません（Claude）"
        except anthropic.RateLimitError:
            return "⏳ レート制限。しばらく待ってから再試行してください（Claude）"
        except anthropic.APITimeoutError:
            return "⏱️ タイムアウト（Claude）"
        except anthropic.APIError as e:
            logger.error("Claude API error: %s", e)
            return "❌ APIエラー（Claude）"
```

- [ ] **Step 5: テストが通ることを確認する**

```bash
python -m pytest tests/test_models.py -v
# Expected: 3 passed
```

- [ ] **Step 6: コミットする**

```bash
git add src/models/base.py src/models/claude.py tests/test_models.py
git commit -m "feat: models/base.py + models/claude.py — ModelAdapter + Claudeアダプター"
```

---

## Task 4: src/models/openai_gpt.py + src/models/grok.py

**Files:**
- Create: `src/models/openai_gpt.py`
- Create: `src/models/grok.py`
- Modify: `tests/test_models.py`（GPT・Grok テストを追加）

- [ ] **Step 1: テストを追加する**（test_models.py に追記）

```python
# tests/test_models.py に追加
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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_models.py::test_gpt_returns_text -v
# Expected: FAIL (ImportError)
```

- [ ] **Step 3: openai_gpt.py を実装する**

```python
# src/models/openai_gpt.py
import logging
import openai
from .base import ModelAdapter
from .claude import SYSTEM_PROMPT  # 同じシステムプロンプトを共有

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"
MAX_TOKENS = 2048


class OpenAIGPTAdapter(ModelAdapter):

    @property
    def model_name(self) -> str:
        return "gpt"

    def chat(self, messages: list[dict], api_key: str) -> str:
        try:
            client = openai.OpenAI(api_key=api_key)
            all_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=all_messages,
            )
            return response.choices[0].message.content or "❌ 空の応答"
        except openai.AuthenticationError:
            return "❌ APIキーが正しくありません（GPT）"
        except openai.RateLimitError:
            return "⏳ レート制限（GPT）"
        except openai.APITimeoutError:
            return "⏱️ タイムアウト（GPT）"
        except openai.APIError as e:
            logger.error("GPT API error: %s", e)
            return "❌ APIエラー（GPT）"
```

- [ ] **Step 4: grok.py を実装する**

```python
# src/models/grok.py
import logging
import openai
from .base import ModelAdapter
from .claude import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

MODEL = "grok-3-mini"
MAX_TOKENS = 2048
XAI_BASE_URL = "https://api.x.ai/v1"


class GrokAdapter(ModelAdapter):

    @property
    def model_name(self) -> str:
        return "grok"

    def chat(self, messages: list[dict], api_key: str) -> str:
        try:
            client = openai.OpenAI(api_key=api_key, base_url=XAI_BASE_URL)
            all_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=all_messages,
            )
            return response.choices[0].message.content or "❌ 空の応答"
        except openai.AuthenticationError:
            return "❌ APIキーが正しくありません（Grok）"
        except openai.RateLimitError:
            return "⏳ レート制限（Grok）"
        except openai.APITimeoutError:
            return "⏱️ タイムアウト（Grok）"
        except openai.APIError as e:
            logger.error("Grok API error: %s", e)
            return "❌ APIエラー（Grok）"
```

- [ ] **Step 5: テストが通ることを確認する**

```bash
python -m pytest tests/test_models.py -v
# Expected: 8 passed
```

- [ ] **Step 6: コミットする**

```bash
git add src/models/openai_gpt.py src/models/grok.py tests/test_models.py
git commit -m "feat: models/openai_gpt.py + models/grok.py — GPT・Grokアダプター"
```

---

## Task 5: src/models/gemini.py

**Files:**
- Create: `src/models/gemini.py`
- Modify: `tests/test_models.py`（Gemini テストを追加）

- [ ] **Step 1: テストを追加する**

```python
# tests/test_models.py に追加
from src.models.gemini import GeminiAdapter

def test_gemini_returns_text():
    mock_response = MagicMock()
    mock_response.text = "Geminiの回答"
    mock_chat = MagicMock()
    mock_chat.send_message.return_value = mock_response
    mock_model = MagicMock()
    mock_model.start_chat.return_value = mock_chat
    with patch("google.generativeai.configure"), \
         patch("google.generativeai.GenerativeModel", return_value=mock_model):
        result = GeminiAdapter().chat([{"role": "user", "content": "test"}], "AIza-test")
    assert result == "Geminiの回答"

def test_gemini_model_name():
    assert GeminiAdapter().model_name == "gemini"
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_models.py::test_gemini_returns_text -v
# Expected: FAIL (ImportError)
```

- [ ] **Step 3: gemini.py を実装する**

```python
# src/models/gemini.py
import logging
from .base import ModelAdapter
from .claude import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

MODEL = "gemini-2.0-flash"


class GeminiAdapter(ModelAdapter):

    @property
    def model_name(self) -> str:
        return "gemini"

    def chat(self, messages: list[dict], api_key: str) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=MODEL,
                system_instruction=SYSTEM_PROMPT,
            )
            # メッセージ履歴を Gemini 形式に変換（最後のメッセージ以外）
            history = [
                {
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [msg["content"]],
                }
                for msg in messages[:-1]
            ]
            chat = model.start_chat(history=history)
            response = chat.send_message(messages[-1]["content"])
            return response.text
        except Exception as e:
            err = str(e)
            if "API_KEY_INVALID" in err or "401" in err:
                return "❌ APIキーが正しくありません（Gemini）"
            if "429" in err or "quota" in err.lower():
                return "⏳ レート制限（Gemini）"
            logger.error("Gemini API error: %s", e)
            return f"❌ APIエラー（Gemini）"
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_models.py -v
# Expected: 10 passed
```

- [ ] **Step 5: コミットする**

```bash
git add src/models/gemini.py tests/test_models.py
git commit -m "feat: models/gemini.py — Geminiアダプター"
```

---

## Task 6: src/retriever.py — SQLite FTS5 検索

**Files:**
- Create: `src/retriever.py`
- Create: `tests/test_retriever.py`

- [ ] **Step 1: テストを書く**

```python
# tests/test_retriever.py
import pytest
import sqlite3
from pathlib import Path
from src.retriever import search, _build_fts_db

@pytest.fixture
def fts_db(tmp_path):
    db_path = tmp_path / "index.db"
    _build_fts_db(db_path, [
        ("repo/scoring.py", "def like_score(): return engagement * weight"),
        ("repo/README.md", "# X Algorithm\nThis is the recommendation system"),
        ("repo/filter.scala", "object VisibilityFilter extends Filter"),
    ])
    return db_path

def test_search_fts_returns_matching_chunks(fts_db):
    results = search("like score", mode="fts", db_path=fts_db)
    assert len(results) > 0
    assert any("like_score" in r["chunk"] or "like score" in r["chunk"].lower() for r in results)

def test_search_fts_returns_list_of_dicts(fts_db):
    results = search("algorithm", mode="fts", db_path=fts_db)
    assert isinstance(results, list)
    for r in results:
        assert "file" in r
        assert "chunk" in r

def test_search_fts_empty_query_returns_empty(fts_db):
    results = search("", mode="fts", db_path=fts_db)
    assert results == []

def test_search_raises_if_db_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        search("test", db_path=tmp_path / "nonexistent.db")

def test_search_mode_mismatch_uses_stored_mode(fts_db):
    # DBがftsモードで作られているのにvectorを指定 → ftsで動作する
    results = search("algorithm", mode="vector", db_path=fts_db)
    assert isinstance(results, list)
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_retriever.py -v
# Expected: FAIL (ImportError)
```

- [ ] **Step 3: retriever.py を実装する**

```python
# src/retriever.py
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "index.db"
TOP_K = 5


def search(query: str, mode: str = "fts", db_path: Path | None = None) -> list[dict]:
    """ソースコードインデックスを検索して関連チャンクを返す。"""
    if not query.strip():
        return []

    path = db_path or DEFAULT_DB_PATH
    if not path.exists():
        raise FileNotFoundError(f"インデックスが見つかりません: {path}")

    with sqlite3.connect(path) as conn:
        stored_mode = _get_stored_mode(conn)
        effective_mode = stored_mode if stored_mode else mode
        if stored_mode and stored_mode != mode:
            # DBのモードと要求モードが異なる場合はDBのモードを優先
            effective_mode = stored_mode

        if effective_mode == "fts":
            return _fts_search(conn, query)
        else:
            return _vector_search(conn, query)


def _get_stored_mode(conn: sqlite3.Connection) -> str | None:
    try:
        row = conn.execute(
            "SELECT value FROM meta WHERE key='search_mode'"
        ).fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None


def _fts_search(conn: sqlite3.Connection, query: str) -> list[dict]:
    try:
        rows = conn.execute(
            "SELECT file_path, chunk FROM chunks_fts WHERE chunks_fts MATCH ? LIMIT ?",
            (query, TOP_K),
        ).fetchall()
        return [{"file": r[0], "chunk": r[1]} for r in rows]
    except sqlite3.OperationalError:
        return []


def _vector_search(conn: sqlite3.Connection, query: str) -> list[dict]:
    """ベクトル検索。sentence-transformersが必要。"""
    import numpy as np
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_vec = model.encode(query).astype("float32")

    rows = conn.execute(
        "SELECT file_path, chunk, embedding FROM chunks_vec"
    ).fetchall()

    scored = []
    for file_path, chunk, emb_blob in rows:
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        norm = np.linalg.norm(query_vec) * np.linalg.norm(emb)
        score = float(np.dot(query_vec, emb) / norm) if norm > 0 else 0.0
        scored.append((score, file_path, chunk))

    scored.sort(reverse=True)
    return [{"file": r[1], "chunk": r[2]} for r in scored[:TOP_K]]


def _build_fts_db(
    db_path: Path, chunks: list[tuple[str, str]]
) -> None:
    """テスト用ヘルパー: FTSインデックスDBを構築する。"""
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(file_path, chunk)")
        conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO meta VALUES ('search_mode', 'fts')")
        conn.executemany(
            "INSERT INTO chunks_fts(file_path, chunk) VALUES (?, ?)", chunks
        )
        conn.commit()
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_retriever.py -v
# Expected: 5 passed
```

- [ ] **Step 5: コミットする**

```bash
git add src/retriever.py tests/test_retriever.py
git commit -m "feat: src/retriever.py — SQLite FTS5検索エンジン"
```

---

## Task 7: src/dispatcher.py — マルチモデル並列送信

**Files:**
- Create: `src/dispatcher.py`
- Create: `tests/test_dispatcher.py`

- [ ] **Step 1: テストを書く**

```python
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

def test_dispatch_includes_context_in_messages(mock_adapters):
    chunks = [{"file": "scorer.py", "chunk": "def score(): pass"}]
    with patch("src.dispatcher.ADAPTERS") as mock_adp:
        mock_adp.__contains__ = lambda self, x: True
        mock_adp.__getitem__ = lambda self, x: MagicMock(chat=MagicMock(return_value="ok"))
        dispatch("test", chunks, ["claude"], {"claude": "sk"}, [])
        call_args = mock_adp["claude"].chat.call_args
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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
python -m pytest tests/test_dispatcher.py -v
# Expected: FAIL (ImportError)
```

- [ ] **Step 3: dispatcher.py を実装する**

```python
# src/dispatcher.py
import concurrent.futures
import logging

from .models.claude import ClaudeAdapter
from .models.openai_gpt import OpenAIGPTAdapter
from .models.gemini import GeminiAdapter
from .models.grok import GrokAdapter

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20

ADAPTERS = {
    "claude": ClaudeAdapter(),
    "gpt": OpenAIGPTAdapter(),
    "gemini": GeminiAdapter(),
    "grok": GrokAdapter(),
}


def dispatch(
    question: str,
    context_chunks: list[dict],
    model_names: list[str],
    api_keys: dict[str, str],
    history: list[dict],
) -> dict[str, str]:
    """選択モデル全てに並列でプロンプトを送信し回答を集約する。"""
    recent = history[-MAX_HISTORY_MESSAGES:]

    context_text = "\n\n".join(
        f"=== {c['file']} ===\n{c['chunk']}" for c in context_chunks
    )
    user_content = (
        f"## 参照コード\n{context_text}\n\n## 質問\n{question}"
        if context_text
        else question
    )
    messages = [*recent, {"role": "user", "content": user_content}]

    results: dict[str, str] = {}

    # APIキー未設定のモデルは即座にエラー返却
    runnable = []
    for name in model_names:
        if name not in ADAPTERS:
            continue
        if not api_keys.get(name):
            results[name] = "❌ APIキーが未設定です"
        else:
            runnable.append(name)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(ADAPTERS[name].chat, messages, api_keys[name]): name
            for name in runnable
        }
        for future, name in futures.items():
            try:
                results[name] = future.result(timeout=60)
            except concurrent.futures.TimeoutError:
                results[name] = "⏱️ タイムアウト"
            except Exception as e:
                logger.error("Dispatch error for %s: %s", name, e)
                results[name] = "❌ エラー"

    return results
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
python -m pytest tests/test_dispatcher.py -v
# Expected: 4 passed
```

- [ ] **Step 5: 全テストが通ることを確認する**

```bash
python -m pytest tests/ -v
# Expected: 全テスト passed
```

- [ ] **Step 6: コミットする**

```bash
git add src/dispatcher.py tests/test_dispatcher.py
git commit -m "feat: src/dispatcher.py — マルチモデル並列送信"
```

---

## Task 8: index_source.py — ソースコードインデックス構築

**Files:**
- Create: `index_source.py`

TDD省略（外部ファイルシステムに依存するCLIスクリプト。手動テストで確認）。

- [ ] **Step 1: index_source.py を実装する**

```python
# index_source.py
"""ソースコードインデックス構築スクリプト

Usage:
    python index_source.py \\
        --x-algo-path ../x-algorithm-main \\
        --algo-path ../the-algorithm-main \\
        --mode fts
"""
import argparse
import sqlite3
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent / "data" / "index.db"
TARGET_EXTENSIONS = {".md", ".py", ".scala", ".java", ".ts", ".go"}
CHUNK_SIZE = 1_000
CHUNK_OVERLAP = 200


def _chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _index_repo(conn: sqlite3.Connection, repo_path: str, repo_name: str) -> int:
    count = 0
    for file in sorted(Path(repo_path).rglob("*")):
        if file.suffix not in TARGET_EXTENSIONS:
            continue
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
            relative = f"{repo_name}/{file.relative_to(repo_path)}"
            for chunk in _chunk_text(text):
                conn.execute(
                    "INSERT INTO chunks_fts(file_path, chunk) VALUES (?, ?)",
                    (relative, chunk),
                )
                count += 1
        except Exception:
            continue
    return count


def build_fts(x_algo_path: str, algo_path: str) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(OUTPUT_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS chunks_fts")
        conn.execute("DROP TABLE IF EXISTS meta")
        conn.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(file_path, chunk)")
        conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO meta VALUES ('search_mode', 'fts')")

        total = 0
        for name, path in [
            ("x-algorithm-main", x_algo_path),
            ("the-algorithm-main", algo_path),
        ]:
            print(f"インデックス中: {name}...")
            n = _index_repo(conn, path, name)
            total += n
            print(f"  {n} チャンク追加")

        conn.commit()

    print(f"\n✅ index.db 生成完了: {total} チャンク → {OUTPUT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Xkaiseki ソースコードインデックス構築")
    parser.add_argument("--x-algo-path", required=True, help="x-algorithm-main のパス")
    parser.add_argument("--algo-path", required=True, help="the-algorithm-main のパス")
    parser.add_argument(
        "--mode", choices=["fts", "vector"], default="fts",
        help="検索モード（vector は要 sentence-transformers）"
    )
    args = parser.parse_args()

    if args.mode == "vector":
        print("※ vector モードは現在 fts にフォールバックします")

    build_fts(args.x_algo_path, args.algo_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: ドライランで動作確認する**

```bash
python index_source.py --x-algo-path C:/dev/Proj/Xsrc/x-algorithm-main --algo-path C:/dev/Proj/Xsrc/the-algorithm-main --mode fts
# Expected: index.db 生成完了: X チャンク
```

- [ ] **Step 3: コミットする**

```bash
git add index_source.py
git commit -m "feat: index_source.py — ソースコードFTSインデックス構築CLI"
```

---

## Task 9: 🏠_ホーム.py — セットアップ画面 + チャット画面（全面書き換え）

**Files:**
- Modify: `🏠_ホーム.py`（全面書き換え）

- [ ] **Step 1: 🏠_ホーム.py を書き換える**

```python
# 🏠_ホーム.py
import streamlit as st
from pathlib import Path
from src.config import load_config, save_config, is_setup_complete, MODEL_NAMES
from src.retriever import search, DEFAULT_DB_PATH
from src.dispatcher import dispatch

st.set_page_config(page_title="Xkaiseki", page_icon="🔍", layout="wide")

# ===== CSS =====
st.markdown("""
<style>
body { background: #0F172A; color: #F1F5F9; }
.model-chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px;
  border-radius: 8px; border: 2px solid #334155; cursor: pointer;
  font-size: 0.82rem; font-weight: 500; margin-right: 6px; }
</style>
""", unsafe_allow_html=True)

MODEL_COLORS = {
    "claude": "#7c3aed", "gpt": "#10a37f", "gemini": "#4285f4", "grok": "#e7482e"
}
MODEL_LABELS = {
    "claude": "Claude", "gpt": "GPT", "gemini": "Gemini", "grok": "Grok"
}

# ===== セッション初期化 =====
if "history" not in st.session_state:
    st.session_state.history = []
if "show_setup" not in st.session_state:
    st.session_state.show_setup = not is_setup_complete()
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "tab"
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "claude"
if "last_answers" not in st.session_state:
    st.session_state.last_answers = {}


# ===== セットアップ画面 =====
def render_setup():
    st.title("⚙️ セットアップ")
    st.caption("初回のみ設定します。次回から自動で読み込まれます。")

    config = load_config()

    st.subheader("使用するモデルを選択（複数可）")
    enabled = set(config.get("enabled_models", []))
    new_enabled = []
    cols = st.columns(4)
    for i, name in enumerate(MODEL_NAMES):
        with cols[i]:
            if st.checkbox(MODEL_LABELS[name], value=name in enabled, key=f"chk_{name}"):
                new_enabled.append(name)

    st.subheader("APIキー")
    claude_key = st.text_input("Claude (Anthropic)", value=config.get("claude_api_key", ""), type="password")
    gpt_key    = st.text_input("GPT (OpenAI)",       value=config.get("gpt_api_key", ""),    type="password")
    gemini_key = st.text_input("Gemini (Google)",    value=config.get("gemini_api_key", ""), type="password")
    grok_key   = st.text_input("Grok (xAI)",         value=config.get("grok_api_key", ""),   type="password")

    st.subheader("検索方式")
    search_mode = st.radio(
        "ソースコード検索方式",
        options=["fts", "vector"],
        format_func=lambda x: "キーワード検索（追加不要）" if x == "fts" else "意味検索（初回~100MBダウンロード）",
        index=0 if config.get("search_mode", "fts") == "fts" else 1,
        horizontal=True,
    )

    if not DEFAULT_DB_PATH.exists():
        st.warning("⚠️ ソースコードインデックスが見つかりません。index_source.py を実行してください。")

    if st.button("チャットを開始 →", type="primary", disabled=not new_enabled):
        save_config({
            "claude_api_key": claude_key,
            "gpt_api_key": gpt_key,
            "gemini_api_key": gemini_key,
            "grok_api_key": grok_key,
            "enabled_models": new_enabled,
            "search_mode": search_mode,
        })
        st.session_state.show_setup = False
        st.rerun()


# ===== チャット画面 =====
def render_chat():
    config = load_config()
    enabled_models = config.get("enabled_models", ["claude"])
    search_mode = config.get("search_mode", "fts")
    api_keys = {
        "claude": config["claude_api_key"],
        "gpt":    config["gpt_api_key"],
        "gemini": config["gemini_api_key"],
        "grok":   config["grok_api_key"],
    }

    # ヘッダー
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🔍 Xkaiseki")
    with col2:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("タブ"):
                st.session_state.view_mode = "tab"
        with c2:
            if st.button("並べて"):
                st.session_state.view_mode = "grid"
        with c3:
            if st.button("⚙ 設定"):
                st.session_state.show_setup = True
                st.rerun()

    # モデル選択チップ（複数選択）
    st.write("**表示モデル:**")
    display_models = list(st.session_state.get("display_models", enabled_models))
    cols = st.columns(len(MODEL_NAMES))
    new_display = []
    for i, name in enumerate(MODEL_NAMES):
        if name not in enabled_models:
            continue
        with cols[i]:
            checked = st.checkbox(MODEL_LABELS[name], value=name in display_models, key=f"disp_{name}")
            if checked:
                new_display.append(name)
    if new_display:
        st.session_state.display_models = new_display
    else:
        st.session_state.display_models = enabled_models

    st.divider()

    # チャット履歴 + 回答表示
    for i, turn in enumerate(st.session_state.history):
        with st.chat_message("user"):
            st.write(turn["question"])
        with st.chat_message("assistant"):
            _render_answers(turn["answers"], st.session_state.display_models, f"hist_{i}")

    # 入力
    question = st.chat_input("質問を入力...")
    if question:
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("全モデルが回答中..."):
                chunks = []
                if DEFAULT_DB_PATH.exists():
                    try:
                        chunks = search(question, mode=search_mode)
                    except Exception:
                        pass

                answers = dispatch(
                    question=question,
                    context_chunks=chunks,
                    model_names=enabled_models,
                    api_keys=api_keys,
                    history=[
                        msg
                        for turn in st.session_state.history
                        for msg in [
                            {"role": "user", "content": turn["question"]},
                            {"role": "assistant", "content": next(iter(turn["answers"].values()), "")},
                        ]
                    ],
                )
            _render_answers(answers, st.session_state.display_models, f"new_{len(st.session_state.history)}")

        st.session_state.history.append({"question": question, "answers": answers})
        if len(st.session_state.history) > 10:
            st.session_state.history = st.session_state.history[-10:]
        st.rerun()


def _render_answers(answers: dict, display_models: list[str], key_prefix: str):
    """タブ または 横並びで回答を表示する。"""
    models_to_show = [m for m in display_models if m in answers]
    if not models_to_show:
        st.info("表示するモデルを選択してください。")
        return

    if st.session_state.view_mode == "tab":
        tabs = st.tabs([MODEL_LABELS[m] for m in models_to_show])
        for tab, name in zip(tabs, models_to_show):
            with tab:
                st.write(answers[name])
    else:
        cols = st.columns(len(models_to_show))
        for col, name in zip(cols, models_to_show):
            with col:
                st.markdown(f"**{MODEL_LABELS[name]}**")
                st.write(answers[name])


# ===== メイン =====
if st.session_state.show_setup:
    render_setup()
else:
    render_chat()
```

- [ ] **Step 2: ローカルで起動して動作確認する**

```bash
streamlit run "🏠_ホーム.py"
# http://localhost:8501 でセットアップ画面が表示されること
# APIキーを入力してチャット画面に遷移できること
# 質問を送信して全モデルの回答が表示されること
```

- [ ] **Step 3: 全テストが通ることを確認する**

```bash
python -m pytest tests/ -v
# Expected: 全テスト passed
```

- [ ] **Step 4: コミットする**

```bash
git add "🏠_ホーム.py"
git commit -m "feat: 🏠_ホーム.py — マルチモデルUI全面再設計（セットアップ+チャット）"
```

---

## Task 10: ドキュメント更新

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `.gitignore`

- [ ] **Step 1: .gitignore に data/index.db を追加する**

```bash
echo "data/index.db" >> .gitignore
git add .gitignore
```

- [ ] **Step 2: README.md を更新する**（ローカル起動手順と index_source.py の説明を更新）

- [ ] **Step 3: 最終コミットする**

```bash
git add README.md CLAUDE.md .gitignore
git commit -m "docs: README・CLAUDE.md・.gitignore をマルチモデル対応に更新"
```
