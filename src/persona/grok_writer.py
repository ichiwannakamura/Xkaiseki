# src/persona/grok_writer.py
"""Grok API を使ってペルソナ人格でSNS投稿下書きを生成する。"""
import logging
import openai

from .persona_store import persona_to_system_prompt

logger = logging.getLogger(__name__)

XAI_BASE_URL = "https://api.x.ai/v1"
RESEARCH_MODEL = "grok-3"        # Web検索対応モデル
WRITE_MODEL = "grok-3-mini"      # 文章生成モデル
MAX_TOKENS = 4096


POST_TYPE_GUIDE = {
    "tweet": (
        "Xのポスト（旧ツイート）として140文字以内で書いてください。"
        "改行は最小限。ハッシュタグを末尾に付けてください。"
    ),
    "thread": (
        "Xのスレッドとして3〜5件の連続ポストを作成してください。"
        "各ポストを「1/」「2/」のように番号で区切ってください。"
        "各ポストは140文字以内。"
    ),
    "article": (
        "note等のブログ記事として800〜1200文字程度で書いてください。"
        "見出しと本文を含む構造的な文章にしてください。"
    ),
}


def research_topic(topic: str, api_key: str) -> str:
    """Grok に最新情報を調査させ、サマリーを返す。"""
    client = openai.OpenAI(api_key=api_key, base_url=XAI_BASE_URL)
    system = (
        "あなたは優秀なリサーチアシスタントです。"
        "与えられたトピックについて最新かつ重要な情報を調査し、"
        "日本語で800文字以内のサマリーを返してください。"
        "事実のみを記述し、情報源があれば簡潔に付記してください。"
    )
    try:
        resp = client.chat.completions.create(
            model=RESEARCH_MODEL,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"次のトピックを調査してください:\n\n{topic}"},
            ],
        )
        return resp.choices[0].message.content or ""
    except openai.AuthenticationError:
        raise ValueError("Grok APIキーが正しくありません")
    except openai.RateLimitError:
        raise ValueError("Grok APIのレート制限に達しました。しばらく待ってから再試行してください")
    except Exception as e:
        logger.error("Grok research error: %s", e)
        raise ValueError(f"調査中にエラーが発生しました: {e}")


def generate_draft(
    persona: dict,
    topic: str,
    post_type: str,
    research_summary: str,
    extra_notes: str,
    api_key: str,
) -> str:
    """ペルソナ人格でSNS投稿下書きを生成する。"""
    client = openai.OpenAI(api_key=api_key, base_url=XAI_BASE_URL)
    system_prompt = persona_to_system_prompt(persona)

    type_guide = POST_TYPE_GUIDE.get(post_type, POST_TYPE_GUIDE["tweet"])

    user_content_parts = [
        f"## 投稿テーマ\n{topic}",
        f"\n## 調査情報\n{research_summary}" if research_summary else "",
        f"\n## 追加指示\n{extra_notes}" if extra_notes else "",
        f"\n## 投稿形式\n{type_guide}",
        "\n上記の情報とあなたの人格設定に基づき、投稿文を生成してください。",
    ]

    try:
        resp = client.chat.completions.create(
            model=WRITE_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "".join(p for p in user_content_parts if p)},
            ],
        )
        return resp.choices[0].message.content or ""
    except openai.AuthenticationError:
        raise ValueError("Grok APIキーが正しくありません")
    except openai.RateLimitError:
        raise ValueError("Grok APIのレート制限に達しました。しばらく待ってから再試行してください")
    except Exception as e:
        logger.error("Grok write error: %s", e)
        raise ValueError(f"下書き生成中にエラーが発生しました: {e}")
