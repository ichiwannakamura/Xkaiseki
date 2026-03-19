import json
import re
from pathlib import Path
import anthropic

MAX_CHARS = 50_000
MODEL = "claude-sonnet-4-6"

# 解析対象の拡張子
TARGET_EXTENSIONS = {".md", ".py", ".scala", ".java", ".ts", ".go"}

# 解析トピック定義（generate_kb.py が使用）
ANALYSIS_TOPICS = [
    "scoring",          # スコアリングシグナルと重み
    "forbidden_actions",  # 禁止・NG行動
    "for_you_conditions", # For Youフィード表示条件
    "affiliate_strategy", # アフィリエイト戦略
    "roadmap_10k_impressions"  # 1万インプレッションロードマップ
]

COMBINED_ANALYSIS_PROMPT_TEMPLATE = """
以下は、Xの推薦アルゴリズムを構成する2つのリポジトリのソースコードです。

【重要な前提】
- x-algorithm-main（2026年版）は the-algorithm-main（2025年版）を基盤として構築されています
- 2026年版は2025年版の上位レイヤーとして動作し、一部コンポーネントを継承・拡張・置き換えています
- 両者は独立したシステムではなく、統合されたアーキテクチャを形成しています

## x-algorithm-main（2026年版 / 上位レイヤー）
{x_algo_content}

---

## the-algorithm-main（2025年版 / 基盤レイヤー）
{algo_content}

---

このコードを「{topic}」の観点で解析してください。以下の点を踏まえること：
- 2026年版と2025年版がどのように連携・継承しているか
- 2025年版から2026年版で何が変わり、何が引き継がれているか
- アフィリエイト運用者にとって実践的な意味は何か

## 出力形式（必ずこのJSONのみを出力）
{{
  "topic": "{topic}",
  "summary": "200文字以内の要約（両バージョンの統合的な解析結果）",
  "marketing_insights": ["アフィリエイト運用者向けの具体的アドバイス（5〜8個）"]
}}
"""


def _read_key_files(repo_path: str, max_chars: int = MAX_CHARS) -> str:
    """リポジトリの主要ファイルを読み込み、結合した文字列を返す。"""
    path = Path(repo_path)
    if not path.exists():
        raise FileNotFoundError(f"リポジトリが見つかりません: {repo_path}")

    collected = []
    total_chars = 0

    # README.md を優先して読む
    readme = path / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8", errors="ignore")
        collected.append(f"=== README.md ===\n{text}")
        total_chars += len(text)

    # 再帰的にターゲット拡張子のファイルを収集
    for file in sorted(path.rglob("*")):
        if file.suffix not in TARGET_EXTENSIONS:
            continue
        if file.name == "README.md":
            continue
        if total_chars >= max_chars:
            break
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
            snippet = text[:max_chars - total_chars]
            collected.append(f"=== {file.relative_to(path)} ===\n{snippet}")
            total_chars += len(snippet)
        except Exception:
            continue

    return "\n\n".join(collected)


def analyze_repositories_combined(x_algo_path: str, algo_path: str, api_key: str, topic: str) -> dict:
    """
    両リポジトリを統合的に読み込み、レイヤード・アーキテクチャとして Claude で解析する。

    x-algorithm-main（2026年版）が the-algorithm-main（2025年版）の上位レイヤーであるという
    継承関係を踏まえた統合解析を行う。

    Returns:
        {"topic": str, "summary": str, "marketing_insights": list[str]}
    """
    # 各リポジトリ30,000文字に制限（合計60,000文字でトークン上限内に収める）
    x_algo_content = _read_key_files(x_algo_path, max_chars=30_000)
    algo_content = _read_key_files(algo_path, max_chars=30_000)

    prompt = COMBINED_ANALYSIS_PROMPT_TEMPLATE.format(
        topic=topic,
        x_algo_content=x_algo_content,
        algo_content=algo_content,
    )

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()

    # JSON部分を抽出（コードブロックで囲まれている場合も対応）
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # フォールバック: パース失敗時は最小構造を返す
    return {
        "topic": topic,
        "summary": raw[:200] if raw else "解析失敗",
        "marketing_insights": []
    }
