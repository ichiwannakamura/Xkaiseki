# Xkaiseki マルチモデル対応 — 設計書

**作成日**: 2026-03-19
**ステータス**: 承認済み

---

## Goal（ゴール）

Xkaiseki を、Claude・GPT・Gemini・Grok の4モデルが同時回答できるマルチモデルチャットアプリに再設計する。
XアルゴリズムのソースコードをローカルDBとして索引化し、**APIキー不要のオフライン検索 + 選択モデルによる回答生成**を実現する。

---

## Architecture（アーキテクチャ）

### フェーズ構成

```
【フェーズ1: インデックス構築（初回のみ・ローカル実行）】
  x-algorithm-main/ + the-algorithm-main/
          ↓ index_source.py
  data/index.db（SQLite FTS5 または ChromaDB）

【フェーズ2: チャット（ローカルまたはStreamlit Cloud）】
  ユーザー → 質問入力
          ↓ src/retriever.py でDB検索（API不要）
          ↓ 関連コード断片を取得
          ↓ src/models/ の各アダプターへ並列送信
          ↓ 全モデルの回答をUIに表示
```

### ディレクトリ構成

```
Xkaiseki/
├── src/
│   ├── retriever.py        # DB検索（FTS または ベクトル検索）
│   ├── dispatcher.py       # 選択モデルへ並列送信・結果集約
│   ├── config.py           # .env読み書き・設定管理
│   └── models/
│       ├── base.py         # ModelAdapter 抽象基底クラス
│       ├── claude.py       # Anthropic SDK
│       ├── openai_gpt.py   # OpenAI SDK
│       ├── gemini.py       # google-generativeai SDK
│       └── grok.py         # xAI API（OpenAI互換）
├── data/
│   └── index.db            # ソースコードインデックス（ローカル生成）
├── tests/
├── 🏠_ホーム.py             # Streamlit UI（全面再設計）
├── index_source.py         # インデックス構築スクリプト（generate_kb.py の後継）
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Components（コンポーネント詳細）

### `src/retriever.py` — DB検索

**役割**: `index.db` に対してキーワードまたは意味検索を行い、関連コード断片を返す

**検索方式（ユーザー選択可）**:
- `fts`: SQLite FTS5 によるキーワード検索（追加インストール不要）
- `vector`: sentence-transformers による意味検索（初回 ~100MB ダウンロード）

```python
def search(query: str, mode: str = "fts", top_k: int = 5) -> list[dict]:
    # Returns: [{"file": str, "chunk": str, "score": float}]
```

### `src/dispatcher.py` — マルチモデル並列送信

**役割**: 選択されたモデルアダプター全てに対して並列でプロンプトを送信し、回答を集約する

```python
def dispatch(
    question: str,
    context_chunks: list[dict],
    model_names: list[str],   # ["claude", "gpt", "gemini", "grok"]
    api_keys: dict[str, str],
    history: list[dict]
) -> dict[str, str]:
    # Returns: {"claude": "...", "gpt": "...", "gemini": "...", "grok": "..."}
```

**並列実行**: `concurrent.futures.ThreadPoolExecutor` で並列送信（待ち時間を最小化）

### `src/models/base.py` — 抽象基底クラス

```python
class ModelAdapter(ABC):
    @abstractmethod
    def chat(self, messages: list[dict], api_key: str) -> str:
        ...
```

### `src/models/` — 各モデルアダプター

| ファイル | モデル | SDK | 備考 |
|---------|-------|-----|------|
| `claude.py` | claude-sonnet-4-6 | anthropic | 既存実装を流用 |
| `openai_gpt.py` | gpt-4o-mini | openai | |
| `gemini.py` | gemini-2.0-flash | google-generativeai | |
| `grok.py` | grok-3-mini | xAI API | OpenAI互換エンドポイント使用 |

### `src/config.py` — 設定管理

**役割**: `.env` の読み書き、セットアップ状態の管理

```python
def load_config() -> dict          # .envから設定を読み込む
def save_config(config: dict)      # .envに設定を書き込む
def is_setup_complete() -> bool    # セットアップ済みか確認
```

### `index_source.py` — インデックス構築スクリプト

**役割**: ソースコードを分割・索引化して `data/index.db` を生成する（`generate_kb.py` の後継）

```bash
python index_source.py \
  --x-algo-path ../x-algorithm-main \
  --algo-path ../the-algorithm-main \
  --mode fts        # または --mode vector
```

### `🏠_ホーム.py` — Streamlit UI（全面再設計）

**画面構成**:

1. **セットアップ画面**（初回のみ・未設定時に表示）
   - 使用するモデルのチェックボックス選択（Claude / GPT / Gemini / Grok）
   - 各モデルのAPIキー入力
   - 検索方式の選択（キーワード / 意味検索）
   - 「チャットを開始」ボタン → `.env` に保存

2. **チャット画面**
   - アプリタイトル + 右上の「⚙ 設定」ボタン（セットアップに戻る）
   - **モデル選択バー**: チップ形式で表示モデルを絞り込み（複数選択可）
   - **表示切替トグル**: 「タブ」↔「並べて」
     - タブ: 選択モデルをタブで切り替え
     - 並べて: 選択モデルを横に均等配置
   - チャット履歴（スライディングウィンドウ10往復）
   - 質問入力欄 + 送信ボタン

---

## Data Flow（データフロー）

```
質問入力
  → retriever.search(question) → コード断片5件
  → dispatcher.dispatch(question, chunks, selected_models, api_keys)
      ├─ claude.chat(messages)   → 回答A  ┐
      ├─ gpt.chat(messages)      → 回答B  ├─ 並列実行
      ├─ gemini.chat(messages)   → 回答C  │
      └─ grok.chat(messages)     → 回答D  ┘
  → UI: タブ or 横並びで表示
```

---

## Error Handling（エラーハンドリング）

| ケース | 対処 |
|--------|------|
| APIキー未設定のモデル | そのモデルのタブに「APIキーが未設定です」を表示 |
| APIキー無効（401） | 「APIキーが正しくありません」をタブ内に表示 |
| レート制限（429） | 「しばらく待ってから再試行」をタブ内に表示 |
| タイムアウト | 「タイムアウト。再試行してください」をタブ内に表示 |
| インデックス未生成 | セットアップ画面に「index_source.pyを実行してください」を表示 |
| 意味検索モデル未DL | 初回起動時に自動ダウンロード（プログレス表示） |

---

## Testing（テスト方針）

| テスト対象 | 方法 |
|-----------|------|
| `retriever.py` | ダミーDBでFTS・ベクトル検索をpytestで検証 |
| `dispatcher.py` | 各アダプターをモックしてpytestで並列送信を検証 |
| `models/*.py` | 各SDKをモックしてpytestで検証 |
| `config.py` | tmp_pathを使ったpytestで読み書きを検証 |
| Streamlit UI | ローカル起動で手動確認 |

---

## Migration（既存コードからの移行）

| 既存ファイル | 扱い |
|------------|------|
| `src/analyzer.py` | 削除（index_source.pyに役割移行） |
| `src/knowledge_base.py` | 削除（retriever.pyに置き換え） |
| `src/chat_engine.py` | 削除（dispatcher.py + models/に置き換え） |
| `generate_kb.py` | 削除（index_source.pyに置き換え） |
| `data/knowledge_base.json` | 削除（data/index.dbに置き換え） |
| `tests/` | 既存テストを削除し新規テストに置き換え |

---

## Constraints（制約）

- `data/index.db` が100MB超の場合はGitにコミットせずローカル生成とする
- Streamlit Cloudのメモリ制限（~1GB）に収まる設計
- 会話履歴は直近10往復のみ保持
- **本設計はローカル動作を主目的とする**。`.env` への書き込みはローカル専用機能。Streamlit Cloudではシークレット機能を別途使用するが、本フェーズでは対象外とする
- `index.db` 生成時の検索モード（fts/vector）をDB内のメタテーブルに記録し、起動時に不一致を検出してユーザーに警告する
- 既存ファイル（`analyzer.py`等）の削除は新実装の動作確認完了後に行う
