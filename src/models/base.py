# src/models/base.py
from abc import ABC, abstractmethod


class ModelAdapter(ABC):
    """Xkaisekiが対応する各LLMモデルの共通インターフェース。"""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """モデルの識別名（config で使う短縮名）。"""
        ...

    @abstractmethod
    def chat(self, messages: list[dict], api_key: str) -> str:
        """messages を送信して回答テキストを返す。エラー時はエラーメッセージ文字列を返す。"""
        ...
