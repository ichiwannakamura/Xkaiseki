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

ANALYSIS_PROMPT_TEMPLATE = """
以下はXの推薦アルゴリズムのソースコードです。
このコードを「{topic}」の観点で深く解析し、以下のJSON形式で回答してください。

## ソースコード
{content}

## 出力形式（必ずこのJSONのみを出力）
{{
  "topic": "{topic}",
  "summary": "200文字以内の要約",
  "marketing_insights": ["アフィリエイト運用者向けの具体的アドバイス（3〜5個）"]
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


def analyze_repository(repo_path: str, api_key: str, topic: str) -> dict:
    """
    リポジトリを読み込み、指定トピックについて Claude で解析し dict を返す。

    Returns:
        {"topic": str, "summary": str, "marketing_insights": list[str]}
    """
    content = _read_key_files(repo_path)
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(topic=topic, content=content)

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
