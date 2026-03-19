# src/dispatcher.py
import concurrent.futures
import logging

from .models.claude import ClaudeAdapter
from .models.openai_gpt import OpenAIGPTAdapter
from .models.gemini import GeminiAdapter
from .models.grok import GrokAdapter

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 20

ADAPTERS = {
    "claude": ClaudeAdapter(),
    "gpt": OpenAIGPTAdapter(),
    "gemini": GeminiAdapter(),
    "grok": GrokAdapter(),
}


def dispatch(
    question: str,
    context_chunks: list[dict],
    model_names: list[str],
    api_keys: dict[str, str],
    history: list[dict],
) -> dict[str, str]:
    """選択モデル全てに並列でプロンプトを送信し回答を集約する。"""
    recent = history[-MAX_HISTORY_MESSAGES:]

    context_text = "\n\n".join(
        f"=== {c['file']} ===\n{c['chunk']}" for c in context_chunks
    )
    user_content = (
        f"## 参照コード\n{context_text}\n\n## 質問\n{question}"
        if context_text
        else question
    )
    messages = [*recent, {"role": "user", "content": user_content}]

    results: dict[str, str] = {}

    # APIキー未設定のモデルは即座にエラー返却
    runnable = []
    for name in model_names:
        if name not in ADAPTERS:
            continue
        if not api_keys.get(name):
            results[name] = "❌ APIキーが未設定です"
        else:
            runnable.append(name)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(ADAPTERS[name].chat, messages, api_keys[name]): name
            for name in runnable
        }
        for future, name in futures.items():
            try:
                results[name] = future.result(timeout=60)
            except concurrent.futures.TimeoutError:
                results[name] = "⏱️ タイムアウト"
            except Exception as e:
                logger.error("Dispatch error for %s: %s", name, e)
                results[name] = "❌ エラー"

    return results
