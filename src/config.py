# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

ENV_PATH = Path(__file__).parent.parent / ".env"

MODEL_NAMES = ("claude", "gpt", "gemini", "grok")


def load_config() -> dict:
    """Read config from .env file."""
    load_dotenv(ENV_PATH, override=True)
    return {
        "claude_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "gpt_api_key": os.getenv("OPENAI_API_KEY", ""),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "grok_api_key": os.getenv("GROK_API_KEY", ""),
        "enabled_models": [
            m.strip()
            for m in os.getenv("ENABLED_MODELS", "").split(",")
            if m.strip()
        ],
        "search_mode": os.getenv("SEARCH_MODE", "fts"),
    }


def save_config(config: dict) -> None:
    """Write config to .env file."""
    ENV_PATH.touch()
    mapping = {
        "ANTHROPIC_API_KEY": config.get("claude_api_key", ""),
        "OPENAI_API_KEY": config.get("gpt_api_key", ""),
        "GEMINI_API_KEY": config.get("gemini_api_key", ""),
        "GROK_API_KEY": config.get("grok_api_key", ""),
        "ENABLED_MODELS": ",".join(config.get("enabled_models", [])),
        "SEARCH_MODE": config.get("search_mode", "fts"),
    }
    for key, value in mapping.items():
        set_key(str(ENV_PATH), key, value)


def is_setup_complete() -> bool:
    """Return True if at least one model is enabled and has an API key."""
    config = load_config()
    if not config["enabled_models"]:
        return False
    key_map = {
        "claude": config["claude_api_key"],
        "gpt": config["gpt_api_key"],
        "gemini": config["gemini_api_key"],
        "grok": config["grok_api_key"],
    }
    return any(key_map.get(m) for m in config["enabled_models"])
