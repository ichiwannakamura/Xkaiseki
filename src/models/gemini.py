# src/models/gemini.py
import logging
from .base import ModelAdapter
from .claude import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

MODEL = "gemini-2.0-flash"


class GeminiAdapter(ModelAdapter):

    @property
    def model_name(self) -> str:
        return "gemini"

    def chat(self, messages: list[dict], api_key: str) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=MODEL,
                system_instruction=SYSTEM_PROMPT,
            )
            # メッセージ履歴を Gemini 形式に変換（最後のメッセージ以外）
            history = [
                {
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [msg["content"]],
                }
                for msg in messages[:-1]
            ]
            chat = model.start_chat(history=history)
            response = chat.send_message(messages[-1]["content"])
            return response.text
        except Exception as e:
            err = str(e)
            if "API_KEY_INVALID" in err or "401" in err:
                return "❌ APIキーが正しくありません（Gemini）"
            if "429" in err or "quota" in err.lower():
                return "⏳ レート制限（Gemini）"
            logger.error("Gemini API error: %s", e)
            return "❌ APIエラー（Gemini）"
