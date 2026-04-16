# src/persona/persona_store.py
"""ペルソナ定義の永続化（JSON ファイル）。"""
import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "personas"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _path(persona_id: str) -> Path:
    return DATA_DIR / f"{persona_id}.json"


def list_personas() -> list[dict]:
    items = []
    for p in sorted(DATA_DIR.glob("*.json")):
        try:
            items.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    return items


def get_persona(persona_id: str) -> dict | None:
    p = _path(persona_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_persona(data: dict) -> dict:
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    data["updated_at"] = datetime.now().isoformat()
    if "created_at" not in data:
        data["created_at"] = data["updated_at"]
    _path(data["id"]).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def delete_persona(persona_id: str) -> bool:
    p = _path(persona_id)
    if p.exists():
        p.unlink()
        return True
    return False


def persona_to_system_prompt(persona: dict) -> str:
    """ペルソナ辞書から AI に渡す system prompt 文字列を生成する。"""
    p = persona
    ps = p.get("personality", {})
    ss = p.get("sns_style", {})

    tone_label = {"casual": "フレンドリー・タメ口", "formal": "丁寧語・敬語", "neutral": "中性的"}.get(
        ps.get("tone", "neutral"), "中性的"
    )
    traits = "、".join(ps.get("traits", []))
    expertise = "、".join(p.get("expertise", []))
    avoid = "、".join(p.get("avoid_topics", []))
    hashtags = " ".join(ss.get("hashtags", []))

    lines = [
        f"あなたは「{p.get('name', 'NoName')}」というSNSアカウントの人格として振る舞います。",
        f"表示名: {p.get('display_name', p.get('name', ''))}",
        f"自己紹介: {p.get('bio', '')}",
        "",
        "【人格・口調】",
        f"口調スタイル: {tone_label}",
        f"性格特性: {traits}" if traits else "",
        f"価値観・信念: {ps.get('values', '')}" if ps.get("values") else "",
        f"話し方の詳細: {ps.get('speaking_style', '')}" if ps.get("speaking_style") else "",
        "",
        "【専門・興味分野】",
        f"{expertise}" if expertise else "特になし",
        "",
        "【避けるトピック】",
        f"{avoid}" if avoid else "特になし",
        "",
        "【SNS 投稿スタイル】",
        f"絵文字使用: {ss.get('emoji_usage', 'rare')}",
        f"投稿文字数傾向: {ss.get('avg_length', 'medium')}",
        f"ハッシュタグ数: {ss.get('hashtag_count', 2)}個程度",
        f"よく使うハッシュタグ: {hashtags}" if hashtags else "",
        "",
        "このペルソナの口調・価値観・文体を完全に維持して投稿文を作成してください。",
    ]
    return "\n".join(l for l in lines if l is not None and l != "")
