# システムアーキテクチャと設計判断

## 🏗️ ディレクトリ構造

```
Xkaiseki/
├── src/
│   ├── __init__.py
│   ├── knowledge_base.py   # KB load/search（JSONファイル読み込み・キーワード検索）
│   ├── chat_engine.py      # Claude API呼び出し（プロンプト構築・エラーハンドリング）
│   └── analyzer.py         # リポジトリ解析（ファイル読み込み・Claude解析）
├── data/
│   └── knowledge_base.json # 事前生成KB（Gitにコミット、Streamlit Cloudに含める）
├── tests/
│   ├── __init__.py
│   ├── test_knowledge_base.py
│   ├── test_chat_engine.py
│   └── test_analyzer.py
├── docs/superpowers/
│   ├── specs/2026-03-19-xkaiseki-design.md   # 承認済み設計書
│   └── plans/2026-03-19-xkaiseki.md          # 実装計画書
├── 🏠_ホーム.py            # Streamlit メインUI
├── generate_kb.py          # KB生成CLIスクリプト（ローカル1回実行）
├── requirements.txt
├── .env.example
└── .gitignore
```

## 🧠 主要な設計判断 (Architecture Decisions)

### 2026-03-19: 2フェーズ構成（オフライン解析 + オンラインチャット）

- **背景:** アルゴリズムリポジトリ（数百MB）をStreamlit Cloudにデプロイできない。また毎回Claude APIで解析するとコストが高い。
- **決定:** Phase1（ローカルで1回だけ `generate_kb.py` を実行して `knowledge_base.json` を生成してコミット）+ Phase2（Streamlit CloudはJSONのみを使ってチャット）の2フェーズ構成。
- **トレードオフ:** アルゴリズムの更新に追随するには再生成が必要。ただし年1〜2回程度の更新なので許容範囲。

### 2026-03-19: ユーザー自身のAPIキー方式

- **背景:** Streamlit Cloud無料プランでサーバーサイドでAPIキーを持つとコスト無制限リスクがある。
- **決定:** ユーザーが自分のAnthropic APIキーをUI上で入力する方式。サーバーには保存しない。
- **トレードオフ:** ユーザーがAPIキーを持っている必要がある。一般ユーザーには若干のハードル。

### 2026-03-19: KB検索 = キーワード部分一致OR検索（最大3件）

- **背景:** ベクトル検索は依存関係が重く、Streamlit Cloudの1GBメモリ制限に引っかかる。
- **決定:** `search()` は lowercase 部分一致 OR 検索で最大3件を返す。シンプルだが実用に十分。
- **トレードオフ:** 意味的な類似検索はできない。ただしKBが5トピック（scoring/forbidden_actions/for_you_conditions/affiliate_strategy/roadmap_10k_impressions）と小さいため問題なし。

### 2026-03-19: 会話履歴は直近20メッセージ（10往復）のスライディングウィンドウ

- **背景:** Claude APIのcontext windowには上限があり、コストにも影響する。
- **決定:** `history[-20:]` で直近10往復のみ保持。古い会話は切り捨てる。
- **トレードオフ:** 10往復より前の会話を参照する質問への回答精度が落ちる。許容範囲。
