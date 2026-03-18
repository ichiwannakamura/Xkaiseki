import json
from pathlib import Path
from typing import Any

DEFAULT_KB_PATH = Path(__file__).parent.parent / "data" / "knowledge_base.json"
MAX_SEARCH_RESULTS = 3


def load_knowledge_base(path: str | None = None) -> dict[str, Any]:
    """knowledge_base.json を読み込んで dict を返す。"""
    kb_path = Path(path) if path else DEFAULT_KB_PATH
    if not kb_path.exists():
        raise FileNotFoundError(f"knowledge_base.json が見つかりません: {kb_path}")
    with kb_path.open(encoding="utf-8") as f:
        return json.load(f)


def _flatten_section(_section_key: str, section_value: Any) -> str:
    """セクション値を検索用の平坦なテキストに変換する。

    dictの場合はvalue群を結合、それ以外はstr()で変換する。
    """
    if isinstance(section_value, dict):
        return " ".join(str(v) for v in section_value.values() if v)
    return str(section_value)


def search(query: str, kb: dict[str, Any]) -> list[dict[str, Any]]:
    """
    クエリのキーワードでKBを部分一致検索（OR）し、最大3件のセクションを返す。

    Returns:
        [{"section": str, "data": dict}, ...]
    """
    if not query.strip():
        return []

    keywords = query.lower().split()
    results = []

    for section_key, section_value in kb.items():
        text = _flatten_section(section_key, section_value).lower()
        # OR検索: どれか1つのキーワードが含まれればマッチ
        if any(kw in text for kw in keywords):
            results.append({"section": section_key, "data": section_value})
        if len(results) >= MAX_SEARCH_RESULTS:
            break

    return results
