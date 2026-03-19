# tests/test_config.py
import pytest
from pathlib import Path
from unittest.mock import patch
from src.config import load_config, save_config, is_setup_complete

def test_load_config_returns_dict(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=sk-test\nENABLED_MODELS=claude\nSEARCH_MODE=fts\n")
    with patch("src.config.ENV_PATH", env_file):
        config = load_config()
    assert config["claude_api_key"] == "sk-test"
    assert config["enabled_models"] == ["claude"]
    assert config["search_mode"] == "fts"

def test_save_config_writes_env(tmp_path):
    env_file = tmp_path / ".env"
    env_file.touch()
    with patch("src.config.ENV_PATH", env_file):
        save_config({"claude_api_key": "sk-new", "enabled_models": ["claude", "gpt"], "search_mode": "fts", "gpt_api_key": "", "gemini_api_key": "", "grok_api_key": ""})
    content = env_file.read_text()
    assert "sk-new" in content
    assert "claude,gpt" in content

def test_is_setup_complete_true(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=sk-test\nENABLED_MODELS=claude\nSEARCH_MODE=fts\n")
    with patch("src.config.ENV_PATH", env_file):
        assert is_setup_complete() is True

def test_is_setup_complete_false_no_key(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=\nENABLED_MODELS=claude\nSEARCH_MODE=fts\n")
    with patch("src.config.ENV_PATH", env_file):
        assert is_setup_complete() is False
