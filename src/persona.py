# src/persona.py
import csv
import io
import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

PERSONA_PATH = Path("data/persona.json")
MODEL = "claude-sonnet-4-6"
MAX_SAMPLE_ITEMS = 60
MAX_SAMPLES_CHARS = 8000


@dataclass
class PersonaProfile:
    tone: str
    sentence_length: str
    vocabulary: list[str]
    expressions: list[str]
    emoji_usage: str
    formality: str
    writing_quirks: list[str]
    raw_analysis: str


class PersonaManager:
    """ユーザーの文体プロフィールを管理し、テキスト書き直しを行う。"""

    def __init__(self, profile_path: Path = PERSONA_PATH):
        self._path = profile_path
        # 自動読み込みなし: セッション間でプロフィールが混在するのを防ぐ。
        # 保存済みデータを使いたい場合は load_profile_from_disk() を明示的に呼ぶ。
        self.profile: Optional[PersonaProfile] = None

    # ── サンプル読み込み ──────────────────────────────────────────

    @staticmethod
    def parse_tweets_csv(csv_content: str) -> list[str]:
        """X公式エクスポートCSVからツイートテキストを抽出する。"""
        reader = csv.DictReader(io.StringIO(csv_content))
        tweets: list[str] = []
        for row in reader:
            text = (row.get("full_text") or row.get("text") or "").strip()
            if text and not text.startswith("RT "):
                tweets.append(text)
        return tweets

    @staticmethod
    def parse_tweets_js(js_content: str) -> list[str]:
        """X公式エクスポートの tweets.js からツイートテキストを抽出する。

        tweets.js の形式: window.YTD.tweets.part0 = [{"tweet": {...}}, ...]
        """
        json_str = re.sub(r"^window\.\w+(?:\.\w+)*\s*=\s*", "", js_content.strip())
        data: list[dict] = json.loads(json_str)
        tweets: list[str] = []
        for item in data:
            tweet = item.get("tweet", item)
            text = (tweet.get("full_text") or tweet.get("text") or "").strip()
            if text and not text.startswith("RT "):
                tweets.append(text)
        return tweets

    @staticmethod
    def combine_samples(texts: list[str]) -> str:
        """サンプルテキストを分析用に結合する（件数・文字数ともに上限あり）。"""
        selected = texts[:MAX_SAMPLE_ITEMS]
        combined = "\n\n---\n\n".join(selected)
        return combined[:MAX_SAMPLES_CHARS]

    # ── スタイル分析 ──────────────────────────────────────────────

    def analyze_style(self, samples: str, api_key: str) -> PersonaProfile:
        """Claude を使って文体を分析し、PersonaProfile を生成・保存する。"""
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""以下はあるユーザーの日記・ツイート・文章のサンプルです。
このユーザーの文体・言葉遣いを詳細に分析し、JSONのみを返してください（説明不要）。

# 文章サンプル:
{samples}

# 返すJSONの構造:
{{
  "tone": "文体トーン（例: カジュアル・フレンドリー）",
  "sentence_length": "文の長さの傾向（例: 短め 10〜20字）",
  "vocabulary": ["特徴的な語彙1", "語彙2"（最大20個）],
  "expressions": ["口癖・決まり文句1", "表現2"（最大10個）],
  "emoji_usage": "絵文字の使い方（例: ほぼ使わない、よく使う: 😊🔥）",
  "formality": "語尾・敬語パターン（例: タメ口、〜だよね、〜じゃん）",
  "writing_quirks": ["独特のクセ1", "クセ2"（最大10個）],
  "raw_analysis": "このユーザーの文体の総合分析（200字程度）"
}}"""
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        result_text = response.content[0].text
        json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if not json_match:
            raise ValueError("スタイル分析レスポンスからJSONを抽出できませんでした")
        data = json.loads(json_match.group())
        self.profile = PersonaProfile(**data)
        self._save_profile()
        return self.profile

    # ── テキスト書き直し ──────────────────────────────────────────

    def build_system_prompt(self) -> str:
        """保存済みプロフィールからペルソナ用システムプロンプトを組み立てる。"""
        if not self.profile:
            raise ValueError(
                "ペルソナプロフィールが未作成です。先にスタイル分析を実行してください。"
            )
        p = self.profile
        vocab = "、".join(p.vocabulary[:10])
        exprs = "、".join(p.expressions[:5])
        quirks = "\n- ".join(p.writing_quirks[:5])
        return f"""あなたは以下の文体プロフィールを持つユーザーの「分身ペルソナ」として、テキストを書き直す専門家です。

# このユーザーの文体プロフィール
- **トーン**: {p.tone}
- **文の長さ**: {p.sentence_length}
- **特徴的な語彙**: {vocab}
- **口癖・決まり文句**: {exprs}
- **絵文字**: {p.emoji_usage}
- **語尾・敬語**: {p.formality}
- **独特のクセ**:
- {quirks}

# 総合分析
{p.raw_analysis}

# タスク
ユーザーが入力したテキストを上記プロフィールに従って書き直してください。
内容・意味は変えず、言葉遣い・表現・トーンだけをこのユーザーらしく変換します。
書き直したテキストのみを返してください（説明・コメント不要）。"""

    def rewrite_text(self, text: str, api_key: str) -> str:
        """ペルソナを使ってテキストを書き直す。"""
        system_prompt = self.build_system_prompt()
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"次のテキストを私の文体で書き直してください:\n\n{text}",
                }
            ],
        )
        return response.content[0].text

    # ── 保存 / 読み込み / 削除 ─────────────────────────────────────

    def _save_profile(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(asdict(self.profile), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_profile_from_disk(self) -> Optional[PersonaProfile]:
        """ディスクから保存済みプロフィールを明示的に読み込む。

        Returns:
            読み込んだ PersonaProfile。ファイルがない・壊れている場合は None。
        """
        self.profile = self._load_profile()
        return self.profile

    def has_saved_profile(self) -> bool:
        """ディスクに保存済みプロフィールが存在するか確認する。"""
        return self._path.exists()

    def delete_profile(self) -> None:
        """プロフィールをメモリとディスクの両方から完全に削除する。"""
        self.profile = None
        if self._path.exists():
            self._path.unlink()

    def _load_profile(self) -> Optional[PersonaProfile]:
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return PersonaProfile(**data)
        except Exception as e:
            logger.warning("ペルソナプロフィールの読み込みに失敗: %s", e)
            return None
