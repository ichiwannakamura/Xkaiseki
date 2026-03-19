# Xkaiseki — 設計書

**作成日**: 2026-03-19
**ステータス**: 承認済み

---

## Goal（ゴール）

X（旧Twitter）の公開推薦アルゴリズム（2025年9月公開 `the-algorithm-main` + 2026年1月公開 `x-algorithm-main`）を徹底解析し、**アフィリエイトアカウントで1万インプレッション達成**のための知識をチャット形式で提供するWebアプリ。

ユーザーは自分のAnthropic APIキーを入力するだけで、アルゴリズムに基づいたマーケティング・技術的アドバイスを対話形式で得られる。

---

## Architecture（アーキテクチャ）

### 2フェーズ構成

```
【フェーズ1: 事前解析（ローカルで1回だけ実行）】
  x-algorithm-main/ + the-algorithm-main/
          ↓ generate_kb.py（Claude Sonnet で深く解析）
  data/knowledge_base.json（構造化知識ベース）
          ↓ Gitにコミット → Streamlit Cloudに含める

【フェーズ2: チャットアプリ（Streamlit Cloud 常時公開）】
  ユーザー → APIキー入力 → 質問入力
          ↓ knowledge_base.py でキーワードマッチ
          ↓ chat_engine.py でプロンプト構築
          ↓ Claude API（ユーザー自身のAPIキー）呼び出し
          ↓ マーケター視点 + 技術視点の2段構成で回答
```

### ディレクトリ構成

```
Xkaiseki/
├── src/
│   ├── analyzer.py          # リポジトリ解析エンジン
│   ├── knowledge_base.py    # KB検索・セクション抽出
│   └── chat_engine.py       # Claude APIプロンプト構築・呼び出し
├── data/
│   └── knowledge_base.json  # 事前解析結果（生成後コミット）
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-03-19-xkaiseki-design.md
├── 🏠_ホーム.py             # Streamlit メインUI
├── generate_kb.py           # KB生成スクリプト（ローカル1回実行）
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Components（コンポーネント詳細）

### `analyzer.py` — リポジトリ解析エンジン

**役割**: 両リポジトリの主要ファイルを読み込み、Claudeで構造化解析する

**解析対象ファイル**:
- `x-algorithm-main/README.md`（アーキテクチャ全体像）
- `x-algorithm-main/home-mixer/**`（ランキング・フィルタリング）
- `x-algorithm-main/phoenix/**`（Grokベーストランスフォーマー・スコアリング）
- `x-algorithm-main/thunder/**`（インネットワーク候補生成）
- `x-algorithm-main/candidate-pipeline/**`（候補ソース）
- `the-algorithm-main/src/scala/.../heavy-ranker`（スコアリング重み）
- `the-algorithm-main/visibilitylib/`（フィルタリング・NG行動）
- `the-algorithm-main/user-signal-service/`（シグナル定義）

**インターフェース**:
```python
def analyze_repository(repo_path: str, api_key: str) -> dict
# Returns: {topic: str, summary: str, marketing_insights: list[str]}
# ※ 1トピック分の補助関数。generate_kb.py が複数トピックを束ねて
#    最終的な knowledge_base.json 構造に変換する。
```

### `knowledge_base.py` — KB管理・検索

**役割**: `knowledge_base.json` のロードとキーワード検索

**knowledge_base.json 構造**:
```json
{
  "scoring": {
    "signals": ["like", "reply", "retweet", "bookmark", "video_watch", "profile_click"],
    "weights_summary": "...",
    "marketing_insight": "..."
  },
  "forbidden_actions": {
    "hard_filters": [...],
    "soft_filters": [...],
    "marketing_insight": "..."
  },
  "for_you_conditions": {
    "requirements": [...],
    "marketing_insight": "..."
  },
  "affiliate_strategy": {
    "content_types": [...],
    "posting_timing": "...",
    "engagement_tactics": [...],
    "marketing_insight": "..."
  },
  "roadmap_10k_impressions": {
    "phases": [
      {"phase": 1, "goal": "...", "actions": [...], "kpi": "..."},
      {"phase": 2, "goal": "...", "actions": [...], "kpi": "..."},
      {"phase": 3, "goal": "...", "actions": [...], "kpi": "..."}
    ]
  }
}
```

**インターフェース**:
```python
def load_knowledge_base() -> dict
def search(query: str, kb: dict) -> list[dict]
# キーワード部分一致（lowercase比較）で関連セクションを最大3件返す
# 複数キーワードはOR検索。ヒットしたセクションはdict形式で返す
```

### `chat_engine.py` — Claude API 呼び出し

**役割**: KBコンテキスト + 会話履歴 + 質問 → Claudeプロンプト構築 → 回答生成

**システムプロンプト方針**:
- マーケター向け解説を先に、技術解説を後に
- 具体的な数値・行動指針を含める
- 「アフィリエイトアカウント運用者」の視点に特化

**会話履歴**: 直近10往復のスライディングウィンドウ
**モデル**: `claude-sonnet-4-6`（コスト・品質バランス）

**インターフェース**:
```python
def chat(
    question: str,
    api_key: str,
    kb: dict,
    history: list[dict]
) -> str
```

### `🏠_ホーム.py` — Streamlit UI

**役割**: ユーザー向けメイン画面

**画面構成**:
1. ヘッダー（タイトル + 説明）
2. APIキー入力欄（`type="password"`）
3. クイック質問ボタン（よくある質問をワンクリック）
4. チャット欄（送受信）
5. サイドバー（会話リセット + 使い方ガイド）

**クイック質問プリセット**:
- 「1万インプレッションへのロードマップを教えて」
- 「絶対にやってはいけないNG行動を教えて」
- 「いいねの正しい使い方と影響を教えて」
- 「For Youに出やすくなる投稿の条件は？」
- 「アフィリエイトリンクはどう扱えばいい？」

### `generate_kb.py` — KB生成スクリプト

**役割**: ローカルで1回実行し `data/knowledge_base.json` を生成

**実行方法**:
```bash
ANTHROPIC_API_KEY=sk-... python generate_kb.py \
  --x-algo-path ../x-algorithm-main \
  --algo-path ../the-algorithm-main

# --dry-run オプションで実際の解析を行わず対象ファイル一覧とトークン見積もりを表示
# 例: python generate_kb.py --dry-run ...
# 想定コスト: claude-sonnet-4-6 使用時 約50〜150円/回（ファイル量による）
```

---

## Design System（デザインシステム）

*ui-ux-pro-maxスキル原則に基づき適用*

### スタイル: Dark Analytics Dashboard

分析ツールとしての信頼感・プロフェッショナル感を重視。Xのブランドカラー（ブラック）に合わせたダークテーマ。

### カラーパレット

| 用途 | 色 | Tailwind |
|---|---|---|
| 背景（メイン） | `#0F172A` | `slate-900` |
| 背景（カード） | `#1E293B` | `slate-800` |
| ボーダー | `#334155` | `slate-700` |
| テキスト（メイン） | `#F1F5F9` | `slate-100` |
| テキスト（サブ） | `#94A3B8` | `slate-400` |
| アクセント（Xブルー） | `#1D9BF0` | カスタム |
| 成功 | `#22C55E` | `green-500` |
| 警告 | `#F59E0B` | `amber-500` |
| エラー | `#EF4444` | `red-500` |

### タイポグラフィ

| 要素 | フォント | サイズ |
|---|---|---|
| 見出し | Space Grotesk（テック感） | 1.5rem〜2rem |
| 本文 | Inter（可読性） | 1rem（16px最小） |
| コード | JetBrains Mono | 0.875rem |

### UXルール（ui-ux-pro-max準拠）

- **タッチターゲット**: ボタン最小44×44px
- **コントラスト比**: テキスト 4.5:1 以上（ダークモードで `slate-100` 使用）
- **ホバー状態**: `transition-colors duration-200`
- **フォーカス**: キーボードナビ対応のフォーカスリング
- **アイコン**: SVGアイコン（Heroicons）のみ。絵文字アイコン禁止
- **ローディング**: 送信中はボタンをdisable＋スピナー表示
- **アニメーション**: 150〜300ms、`transform/opacity` のみ使用

### チャットUIデザイン

```
┌─────────────────────────────────────────────────┐
│ 🔍 Xkaiseki                          [サイドバー] │
│ X推薦アルゴリズム解析チャット                      │
├─────────────────────────────────────────────────┤
│ 🔑 Anthropic API Key ████████████████ [設定済み✓]│
├─────────────────────────────────────────────────┤
│ よくある質問:                                     │
│ [ロードマップ] [NG行動] [いいね] [For You] [アフィ]│
├─────────────────────────────────────────────────┤
│ 💬 チャット                                      │
│                                                  │
│  🤖 Xkaisekiへようこそ。アルゴリズムについて      │
│     何でも聞いてください。                        │
│                                                  │
│  👤 いいねはスコアにどう影響しますか？            │
│                                                  │
│  🤖 [マーケター向け解説]                         │
│     いいねは...                                  │
│     [技術的補足]                                 │
│     アルゴリズム上は...                          │
│                                                  │
├─────────────────────────────────────────────────┤
│ > 質問を入力...                          [送信→] │
└─────────────────────────────────────────────────┘
```

---

## Error Handling（エラーハンドリング）

| ケース | 対処 |
|---|---|
| APIキー未入力 | チャット欄ロック + 「APIキーを入力してください」 |
| APIキー無効（401） | 「APIキーが正しくありません。Anthropicコンソールで確認してください」 |
| レート制限（429） | 「しばらく待ってから再試行してください」 |
| タイムアウト | 「タイムアウトしました。再試行してください」 |
| KB未生成 | 「knowledge_base.jsonが見つかりません。generate_kb.pyを実行してください」 |
| KB該当なし | Claudeの一般知識でフォールバック回答 |

---

## Deployment（デプロイ）

### Streamlit Cloud（無料公開）

```
1. GitHubリポジトリ作成・プッシュ
2. streamlit.io → GitHubと連携
3. リポジトリ選択 → 「Deploy」
4. URLが発行 → 共有するだけで誰でも使える
```

**注意事項**:
- `data/knowledge_base.json` は事前生成してGitにコミットすること
- `.env` はGitに含めない（`.gitignore` で除外）
- Streamlit Cloudのシークレット機能は使わない（各自がAPIキー入力する設計のため）

---

## Testing（テスト方針）

| テスト種類 | 対象 | 方法 |
|---|---|---|
| ユニットテスト | `knowledge_base.py`（検索ロジック） | pytest |
| ユニットテスト | `chat_engine.py`（プロンプト構築） | pytestでモック |
| 統合テスト | `generate_kb.py` | 小さなダミーリポジトリで検証 |
| 手動テスト | Streamlit UI | ローカル起動で動作確認 |

---

## Constraints（制約）

- アルゴリズムリポジトリはStreamlit Cloudにデプロイしない（サイズ大・機密性）
- `knowledge_base.json`（解析結果のみ）をデプロイに含める
- Streamlit Cloudメモリ制限（~1GB）に収まる設計
- 会話履歴は直近10往復のみ保持
