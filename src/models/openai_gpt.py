# src/models/openai_gpt.py
import logging
import openai
from .base import ModelAdapter
from .claude import SYSTEM_PROMPT  # 同じシステムプロンプトを共有

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"
MAX_TOKENS = 2048


class OpenAIGPTAdapter(ModelAdapter):

    @property
    def model_name(self) -> str:
        return "gpt"

    def chat(self, messages: list[dict], api_key: str) -> str:
        try:
            client = openai.OpenAI(api_key=api_key)
            all_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=all_messages,
            )
            return response.choices[0].message.content or "❌ 空の応答"
        except openai.AuthenticationError:
            return "❌ APIキーが正しくありません（GPT）"
        except openai.RateLimitError:
            return "⏳ レート制限（GPT）"
        except openai.APITimeoutError:
            return "⏱️ タイムアウト（GPT）"
        except openai.APIError as e:
            logger.error("GPT API error: %s", e)
            return "❌ APIエラー（GPT）"
