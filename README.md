# Xkaiseki

X（旧Twitter）の推薦アルゴリズム（2025年9月公開 `the-algorithm-main` + 2026年1月公開 `x-algorithm-main`）を解析し、**アフィリエイトアカウントで1万インプレッション達成**のためのアドバイスをチャット形式で提供する Streamlit Web アプリ。

複数のAIモデル（Claude / GPT / Gemini / Grok）の同時回答をサポートし、ユーザーは自分の API キーを入力するだけで、複数視点からのマーケティング・技術的アドバイスを対話形式で得られる。

## 使い方（公開版）

1. Streamlit Cloud デプロイ版にアクセス（URL: TBD）
2. セットアップ画面で API キー（Claude/GPT/Gemini/Grok）を入力
3. 質問を入力またはクイック質問ボタンをクリック

## ローカル起動

```bash
pip install -r requirements.txt
streamlit run 🏠_ホーム.py
```

## インデックス構築（開発者向け・初回のみ）

SQLite FTS5 インデックスを作成します：

```bash
python index_source.py \
  --x-algo-path C:\dev\Proj\Xsrc\x-algorithm-main \
  --algo-path C:\dev\Proj\Xsrc\the-algorithm-main
```

実行後 `data/index.db` が生成されます。`.gitignore` に登録済みのため、Git にコミットしないこと。

## テスト実行

```bash
python -m pytest tests/ -v
```

## 技術スタック

| 用途 | 技術 |
|------|------|
| UI | Streamlit 1.32+ |
| AI | Claude / GPT / Gemini / Grok (マルチモデル対応) |
| データ検索 | SQLite FTS5 (全文検索インデックス) |
| デプロイ | Streamlit Cloud (無料) |
| テスト | pytest + unittest.mock |

## ディレクトリ構成

```
Xkaiseki/
├── src/
│   ├── models/
│   │   ├── claude_model.py      # Claude API呼び出し
│   │   ├── gpt_model.py         # GPT API呼び出し
│   │   ├── gemini_model.py      # Gemini API呼び出し
│   │   └── grok_model.py        # Grok API呼び出し
│   ├── index_search.py          # SQLite FTS5検索エンジン
│   └── analyzer.py              # リポジトリ解析
├── data/
│   └── index.db                 # SQLite インデックス（.gitignore 登録）
├── tests/
│   ├── test_index_search.py
│   ├── test_models.py
│   └── test_analyzer.py
├── 🏠_ホーム.py                  # Streamlit UI（セットアップ + チャット）
├── index_source.py              # インデックス構築スクリプト
├── requirements.txt
└── .env.example                 # API キーテンプレート
```

## 初回セットアップ

アプリを起動すると、初回のみ「セットアップ画面」が表示されます。各 API キーを入力してください：

- **Anthropic API キー**: [Anthropic Console](https://console.anthropic.com) から取得
- **OpenAI API キー**: [OpenAI Platform](https://platform.openai.com) から取得
- **Google Gemini API キー**: [Google AI Studio](https://aistudio.google.com) から取得
- **Grok API キー**: [xAI Console](https://console.x.ai) から取得

※ APIキーは `.streamlit/secrets.toml` に自動保存される（ローカルのみ）
