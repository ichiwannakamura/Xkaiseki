# src/models/claude.py
import logging
import anthropic
from .base import ModelAdapter

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2048
SYSTEM_PROMPT = (
    "あなたはXの推薦アルゴリズムの専門家です。"
    "提供されたソースコードの断片を参考に、アフィリエイト運用者向けに"
    "マーケター視点（先に）と技術視点（後に）で簡潔に回答してください。"
)


class ClaudeAdapter(ModelAdapter):

    @property
    def model_name(self) -> str:
        return "claude"

    def chat(self, messages: list[dict], api_key: str) -> str:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
            if response.content and hasattr(response.content[0], "text"):
                return response.content[0].text
            return "❌ 予期しないAPI応答形式"
        except anthropic.AuthenticationError:
            return "❌ APIキーが正しくありません（Claude）"
        except anthropic.RateLimitError:
            return "⏳ レート制限。しばらく待ってから再試行してください（Claude）"
        except anthropic.APITimeoutError:
            return "⏱️ タイムアウト（Claude）"
        except anthropic.APIError as e:
            logger.error("Claude API error: %s", e)
            return "❌ APIエラー（Claude）"
