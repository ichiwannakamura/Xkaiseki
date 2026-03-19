# Xkaiseki

X（旧Twitter）の推薦アルゴリズム（2025年9月公開 `the-algorithm-main` + 2026年1月公開 `x-algorithm-main`）を解析し、**アフィリエイトアカウントで1万インプレッション達成**のためのアドバイスをチャット形式で提供する Streamlit Web アプリ。

ユーザーは自分の Anthropic API キーを入力するだけで、アルゴリズムに基づいたマーケティング・技術的アドバイスを対話形式で得られる。

## 使い方（公開版）

1. Streamlit Cloud デプロイ版にアクセス（URL: TBD）
2. [Anthropic Console](https://console.anthropic.com) で取得した API キーを入力
3. 質問を入力またはクイック質問ボタンをクリック

## ローカル起動

```bash
pip install -r requirements.txt
streamlit run 🏠_ホーム.py
```

## KB生成（開発者向け・初回のみ）

```bash
# ドライラン（コスト見積もり、API呼び出しなし）
python generate_kb.py --dry-run \
  --x-algo-path C:\dev\Proj\Xsrc\x-algorithm-main \
  --algo-path C:\dev\Proj\Xsrc\the-algorithm-main

# 実際に生成（約50〜150円、claude-sonnet-4-6使用）
ANTHROPIC_API_KEY=sk-ant-... python generate_kb.py \
  --x-algo-path C:\dev\Proj\Xsrc\x-algorithm-main \
  --algo-path C:\dev\Proj\Xsrc\the-algorithm-main
```

生成後 `data/knowledge_base.json` を Git にコミットすること。

## テスト実行

```bash
python -m pytest tests/ -v
# 20 tests, 0 failures
```

## 技術スタック

| 用途 | 技術 |
|------|------|
| UI | Streamlit 1.32+ |
| AI | anthropic SDK (claude-sonnet-4-6) |
| データ | JSON (pre-generated knowledge base) |
| デプロイ | Streamlit Cloud (無料) |
| テスト | pytest + unittest.mock |

## ディレクトリ構成

```
Xkaiseki/
├── src/
│   ├── knowledge_base.py   # KB検索エンジン
│   ├── chat_engine.py      # Claude API呼び出し
│   └── analyzer.py         # リポジトリ解析
├── data/
│   └── knowledge_base.json # 事前生成KB（要コミット）
├── tests/
│   ├── test_knowledge_base.py
│   ├── test_chat_engine.py
│   └── test_analyzer.py
├── 🏠_ホーム.py            # Streamlit UI
├── generate_kb.py          # KB生成スクリプト
└── requirements.txt
```
