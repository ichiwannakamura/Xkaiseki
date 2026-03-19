# tests/test_retriever.py
import pytest
import sqlite3
from pathlib import Path
from src.retriever import search, _build_fts_db

@pytest.fixture
def fts_db(tmp_path):
    db_path = tmp_path / "index.db"
    _build_fts_db(db_path, [
        ("repo/scoring.py", "def like_score(): return engagement * weight"),
        ("repo/README.md", "# X Algorithm\nThis is the recommendation system"),
        ("repo/filter.scala", "object VisibilityFilter extends Filter"),
    ])
    return db_path

def test_search_fts_returns_matching_chunks(fts_db):
    results = search("like score", mode="fts", db_path=fts_db)
    assert len(results) > 0
    assert any("like_score" in r["chunk"] or "like score" in r["chunk"].lower() for r in results)

def test_search_fts_returns_list_of_dicts(fts_db):
    results = search("algorithm", mode="fts", db_path=fts_db)
    assert isinstance(results, list)
    for r in results:
        assert "file" in r
        assert "chunk" in r

def test_search_fts_empty_query_returns_empty(fts_db):
    results = search("", mode="fts", db_path=fts_db)
    assert results == []

def test_search_raises_if_db_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        search("test", db_path=tmp_path / "nonexistent.db")

def test_search_mode_mismatch_uses_stored_mode(fts_db):
    # DBがftsモードで作られているのにvectorを指定 → ftsで動作する
    results = search("algorithm", mode="vector", db_path=fts_db)
    assert isinstance(results, list)
