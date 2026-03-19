# src/models/grok.py
import logging
import openai
from .base import ModelAdapter
from .claude import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

MODEL = "grok-3-mini"
MAX_TOKENS = 2048
XAI_BASE_URL = "https://api.x.ai/v1"


class GrokAdapter(ModelAdapter):

    @property
    def model_name(self) -> str:
        return "grok"

    def chat(self, messages: list[dict], api_key: str) -> str:
        try:
            client = openai.OpenAI(api_key=api_key, base_url=XAI_BASE_URL)
            all_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=all_messages,
            )
            return response.choices[0].message.content or "❌ 空の応答"
        except openai.AuthenticationError:
            return "❌ APIキーが正しくありません（Grok）"
        except openai.RateLimitError:
            return "⏳ レート制限（Grok）"
        except openai.APITimeoutError:
            return "⏱️ タイムアウト（Grok）"
        except openai.APIError as e:
            logger.error("Grok API error: %s", e)
            return "❌ APIエラー（Grok）"
