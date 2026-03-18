import anthropic
from src.knowledge_base import search

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096
MAX_HISTORY_MESSAGES = 20  # 10往復 × 2

SYSTEM_PROMPT = """あなたは「Xkaiseki」です。
Xの推薦アルゴリズム（2023年版 the-algorithm-main + 2026年版 x-algorithm-main）の解析専門家として、
アフィリエイトアカウント運用者に実践的なアドバイスを提供します。

## 回答フォーマット
必ず以下の2段構成で回答してください：

### マーケター向け解説
- 「何をすればよいか」を箇条書きで具体的に
- 数値・タイミング・頻度を含める

### 技術的補足
- アルゴリズム上の仕組みを簡潔に
- エンジニアでなくても理解できる言葉で

## 制約
- アルゴリズム情報に基づかない推測はしない
- 知識ベースにない場合は「データなし」と明記してから一般的な知識で補完
"""


def build_prompt(
    question: str,
    kb_sections: list[dict],
    history: list[dict]
) -> list[dict]:
    """会話履歴 + KBコンテキスト + 質問 → messages リストを構築する。

    Why: Claudeのcontext windowを効率的に使うため、履歴は直近10往復（20メッセージ）に
    スライディングウィンドウで切り詰める。KBセクションは質問メッセージに埋め込み、
    システムプロンプトとの分離を維持する。
    """
    # 直近10往復（20メッセージ）のスライディングウィンドウ
    recent_history = history[-MAX_HISTORY_MESSAGES:]

    # KBコンテキストを質問に付加
    context_parts = []
    for item in kb_sections:
        context_parts.append(f"[{item['section']}]\n{item['data']}")

    context = "\n\n".join(context_parts)
    if context:
        user_content = f"## 参照情報\n{context}\n\n## 質問\n{question}"
    else:
        user_content = question

    messages = list(recent_history) + [{"role": "user", "content": user_content}]
    return messages


def chat(
    question: str,
    api_key: str,
    kb: dict,
    history: list[dict]
) -> str:
    """KB検索 → プロンプト構築 → Claude API呼び出し → 回答文字列を返す。

    Why: エラーハンドリングをここに集約し、UI層（app.py）には文字列のみを返す。
    これによりUI層がAPIの詳細を知らなくて済む（関心の分離）。
    """
    try:
        kb_sections = search(question, kb) if kb else []
        messages = build_prompt(question, kb_sections, history)

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        return response.content[0].text

    except anthropic.AuthenticationError:
        return "❌ APIキーが正しくありません。Anthropicコンソールで確認してください。"
    except anthropic.RateLimitError:
        return "⏳ レート制限に達しました。しばらく待ってから再試行してください。"
    except anthropic.APITimeoutError:
        return "⏱️ タイムアウトしました。再試行してください。"
    except Exception as e:
        return f"❌ エラーが発生しました: {str(e)}"
