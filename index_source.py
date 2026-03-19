# index_source.py
"""ソースコードインデックス構築スクリプト

Usage:
    python index_source.py \\
        --x-algo-path ../x-algorithm-main \\
        --algo-path ../the-algorithm-main \\
        --mode fts
"""
import argparse
import sqlite3
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent / "data" / "index.db"
TARGET_EXTENSIONS = {".md", ".py", ".scala", ".java", ".ts", ".go"}
CHUNK_SIZE = 1_000
CHUNK_OVERLAP = 200


def _chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _index_repo(conn: sqlite3.Connection, repo_path: str, repo_name: str) -> int:
    count = 0
    for file in sorted(Path(repo_path).rglob("*")):
        if file.suffix not in TARGET_EXTENSIONS:
            continue
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
            relative = f"{repo_name}/{file.relative_to(repo_path)}"
            for chunk in _chunk_text(text):
                conn.execute(
                    "INSERT INTO chunks_fts(file_path, chunk) VALUES (?, ?)",
                    (relative, chunk),
                )
                count += 1
        except Exception:
            continue
    return count


def build_fts(x_algo_path: str, algo_path: str) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(OUTPUT_PATH) as conn:
        conn.execute("DROP TABLE IF EXISTS chunks_fts")
        conn.execute("DROP TABLE IF EXISTS meta")
        conn.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(file_path, chunk)")
        conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO meta VALUES ('search_mode', 'fts')")

        total = 0
        for name, path in [
            ("x-algorithm-main", x_algo_path),
            ("the-algorithm-main", algo_path),
        ]:
            print(f"インデックス中: {name}...")
            n = _index_repo(conn, path, name)
            total += n
            print(f"  {n} チャンク追加")

        conn.commit()

    print(f"\n[完了] index.db 生成完了: {total} チャンク -> {OUTPUT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Xkaiseki ソースコードインデックス構築")
    parser.add_argument("--x-algo-path", required=True, help="x-algorithm-main のパス")
    parser.add_argument("--algo-path", required=True, help="the-algorithm-main のパス")
    parser.add_argument(
        "--mode", choices=["fts", "vector"], default="fts",
        help="検索モード（vector は要 sentence-transformers）"
    )
    args = parser.parse_args()

    if args.mode == "vector":
        print("※ vector モードは現在 fts にフォールバックします")

    build_fts(args.x_algo_path, args.algo_path)


if __name__ == "__main__":
    main()
