# src/persona/draft_store.py
"""生成した下書きの永続化（JSON ファイル）。"""
import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "drafts"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATUSES = ("draft", "approved", "posted")


def _path(draft_id: str) -> Path:
    return DATA_DIR / f"{draft_id}.json"


def list_drafts(persona_id: str | None = None, task_id: str | None = None) -> list[dict]:
    items = []
    for p in sorted(DATA_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if persona_id and d.get("persona_id") != persona_id:
                continue
            if task_id and d.get("task_id") != task_id:
                continue
            items.append(d)
        except Exception:
            pass
    return items


def get_draft(draft_id: str) -> dict | None:
    p = _path(draft_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_draft(data: dict) -> dict:
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    data["updated_at"] = datetime.now().isoformat()
    if "created_at" not in data:
        data["created_at"] = data["updated_at"]
    if "status" not in data:
        data["status"] = "draft"
    _path(data["id"]).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def update_draft(draft_id: str, **kwargs) -> dict | None:
    draft = get_draft(draft_id)
    if draft is None:
        return None
    draft.update(kwargs)
    return save_draft(draft)


def delete_draft(draft_id: str) -> bool:
    p = _path(draft_id)
    if p.exists():
        p.unlink()
        return True
    return False
