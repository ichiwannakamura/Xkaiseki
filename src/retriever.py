# src/retriever.py
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "index.db"
TOP_K = 5


def search(query: str, mode: str = "fts", db_path: Path | None = None) -> list[dict]:
    """ソースコードインデックスを検索して関連チャンクを返す。"""
    if not query.strip():
        return []

    path = db_path or DEFAULT_DB_PATH
    if not path.exists():
        raise FileNotFoundError(f"インデックスが見つかりません: {path}")

    with sqlite3.connect(path) as conn:
        stored_mode = _get_stored_mode(conn)
        effective_mode = stored_mode if stored_mode else mode
        if stored_mode and stored_mode != mode:
            # DBのモードと要求モードが異なる場合はDBのモードを優先
            effective_mode = stored_mode

        if effective_mode == "fts":
            return _fts_search(conn, query)
        else:
            return _vector_search(conn, query)


def _get_stored_mode(conn: sqlite3.Connection) -> str | None:
    try:
        row = conn.execute(
            "SELECT value FROM meta WHERE key='search_mode'"
        ).fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None


def _fts_search(conn: sqlite3.Connection, query: str) -> list[dict]:
    try:
        rows = conn.execute(
            "SELECT file_path, chunk FROM chunks_fts WHERE chunks_fts MATCH ? LIMIT ?",
            (query, TOP_K),
        ).fetchall()
        return [{"file": r[0], "chunk": r[1]} for r in rows]
    except sqlite3.OperationalError:
        return []


def _vector_search(conn: sqlite3.Connection, query: str) -> list[dict]:
    """ベクトル検索。sentence-transformersが必要。"""
    import numpy as np
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_vec = model.encode(query).astype("float32")

    rows = conn.execute(
        "SELECT file_path, chunk, embedding FROM chunks_vec"
    ).fetchall()

    scored = []
    for file_path, chunk, emb_blob in rows:
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        norm = np.linalg.norm(query_vec) * np.linalg.norm(emb)
        score = float(np.dot(query_vec, emb) / norm) if norm > 0 else 0.0
        scored.append((score, file_path, chunk))

    scored.sort(reverse=True)
    return [{"file": r[1], "chunk": r[2]} for r in scored[:TOP_K]]


def _build_fts_db(
    db_path: Path, chunks: list[tuple[str, str]]
) -> None:
    """テスト用ヘルパー: FTSインデックスDBを構築する。"""
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(file_path, chunk)")
        conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO meta VALUES ('search_mode', 'fts')")
        conn.executemany(
            "INSERT INTO chunks_fts(file_path, chunk) VALUES (?, ?)", chunks
        )
        conn.commit()
