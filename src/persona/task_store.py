# src/persona/task_store.py
"""投稿タスクの永続化（JSON ファイル）。"""
import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "tasks"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATUSES = ("pending", "processing", "done")
POST_TYPES = ("tweet", "thread", "article")


def _path(task_id: str) -> Path:
    return DATA_DIR / f"{task_id}.json"


def list_tasks(persona_id: str | None = None, status: str | None = None) -> list[dict]:
    items = []
    for p in sorted(DATA_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            t = json.loads(p.read_text(encoding="utf-8"))
            if persona_id and t.get("persona_id") != persona_id:
                continue
            if status and t.get("status") != status:
                continue
            items.append(t)
        except Exception:
            pass
    return items


def get_task(task_id: str) -> dict | None:
    p = _path(task_id)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_task(data: dict) -> dict:
    if "id" not in data:
        data["id"] = str(uuid.uuid4())
    data["updated_at"] = datetime.now().isoformat()
    if "created_at" not in data:
        data["created_at"] = data["updated_at"]
    if "status" not in data:
        data["status"] = "pending"
    _path(data["id"]).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def update_status(task_id: str, status: str) -> dict | None:
    task = get_task(task_id)
    if task is None:
        return None
    task["status"] = status
    return save_task(task)


def delete_task(task_id: str) -> bool:
    p = _path(task_id)
    if p.exists():
        p.unlink()
        return True
    return False
