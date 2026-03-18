import json
import pytest
from pathlib import Path
from src.knowledge_base import load_knowledge_base, search

SAMPLE_KB = {
    "scoring": {
        "signals": ["like", "reply", "retweet"],
        "weights_summary": "いいねは最も影響力が高い",
        "marketing_insight": "返信を促す投稿でスコアを上げる"
    },
    "forbidden_actions": {
        "hard_filters": ["スパム"],
        "soft_filters": ["低エンゲージメント"],
        "marketing_insight": "連投は避けること"
    },
    "for_you_conditions": {
        "requirements": ["フォロワー比率", "エンゲージメント率"],
        "marketing_insight": "For Youに出るにはエンゲージメントが鍵"
    },
    "affiliate_strategy": {
        "content_types": ["教育コンテンツ"],
        "posting_timing": "朝7時〜9時",
        "engagement_tactics": ["質問投稿"],
        "marketing_insight": "リンクは最初のコメントに"
    },
    "roadmap_10k_impressions": {
        "phases": [
            {"phase": 1, "goal": "100フォロワー", "actions": ["毎日投稿"], "kpi": "100imp/日"}
        ]
    }
}


def test_load_knowledge_base_returns_dict(tmp_path):
    # Arrange
    kb_path = tmp_path / "knowledge_base.json"
    kb_path.write_text(json.dumps(SAMPLE_KB), encoding="utf-8")

    # Act
    kb = load_knowledge_base(str(kb_path))

    # Assert
    assert isinstance(kb, dict)
    assert "scoring" in kb


def test_load_knowledge_base_file_not_found():
    # Arrange / Act / Assert
    with pytest.raises(FileNotFoundError):
        load_knowledge_base("/nonexistent/path.json")


def test_search_returns_matching_sections():
    # Arrange
    kb = SAMPLE_KB

    # Act
    results = search("いいね スコア", kb)

    # Assert
    assert len(results) >= 1
    assert any("scoring" in r.get("section", "") for r in results)


def test_search_returns_max_3_results():
    # Arrange
    kb = SAMPLE_KB

    # Act
    results = search("投稿 エンゲージメント アフィリエイト", kb)

    # Assert
    assert len(results) <= 3


def test_search_empty_query_returns_empty():
    # Arrange
    kb = SAMPLE_KB

    # Act
    results = search("", kb)

    # Assert
    assert results == []


def test_search_no_match_returns_empty():
    # Arrange
    kb = SAMPLE_KB

    # Act
    results = search("xyzzy全く関係ない単語", kb)

    # Assert
    assert results == []


def test_search_case_insensitive():
    # Arrange
    kb = SAMPLE_KB

    # Act
    results_lower = search("like", kb)
    results_upper = search("LIKE", kb)

    # Assert
    assert results_lower == results_upper
