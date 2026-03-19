"""
KB生成スクリプト

Usage:
    python generate_kb.py \
        --x-algo-path ../x-algorithm-main \
        --algo-path ../the-algorithm-main

    # ドライラン（対象ファイルとトークン見積もりを表示）
    python generate_kb.py --dry-run \
        --x-algo-path ../x-algorithm-main \
        --algo-path ../the-algorithm-main
"""
import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OUTPUT_PATH = Path(__file__).parent / "data" / "knowledge_base.json"


def estimate_tokens(text: str) -> int:
    """1トークン ≈ 4文字として概算する。"""
    return len(text) // 4


def dry_run(x_algo_path: str, algo_path: str) -> None:
    """解析対象ファイルの一覧とトークン見積もりを表示する（実際の解析はしない）。"""
    from src.analyzer import _read_key_files, ANALYSIS_TOPICS

    print("=== DRY RUN MODE（統合解析モード）===")
    total_chars = 0
    for repo_name, repo_path in [("x-algorithm-main", x_algo_path), ("the-algorithm-main", algo_path)]:
        try:
            content = _read_key_files(repo_path, max_chars=30_000)
            print(f"\n[{repo_name}]")
            print(f"  読み込み文字数: {len(content):,}")
            print(f"  推定トークン数: {estimate_tokens(content):,}")
            total_chars += len(content)
        except FileNotFoundError as e:
            print(f"  [ERROR] {e}")

    combined_tokens = estimate_tokens(total_chars * "x")  # chars → token estimate
    combined_tokens = total_chars // 4
    print(f"\n【統合解析（1回のAPI呼び出し / トピック）】")
    print(f"  合計入力文字数: {total_chars:,}")
    print(f"  推定入力トークン数: {combined_tokens:,}")
    print(f"  解析トピック数: {len(ANALYSIS_TOPICS)}")
    print(f"  推定コスト: ~{combined_tokens * len(ANALYSIS_TOPICS) // 1000 * 3}円（sonnet-4-6換算）")
    print("\n実際に生成する場合は --dry-run を外してください。")


def generate(x_algo_path: str, algo_path: str, api_key: str) -> None:
    """両リポジトリを統合解析して knowledge_base.json を生成する。"""
    from src.analyzer import analyze_repositories_combined, ANALYSIS_TOPICS

    kb = {}

    for topic in ANALYSIS_TOPICS:
        print(f"\n[解析中] トピック: {topic}")
        print(f"  - 両リポジトリを統合解析中（継承関係を考慮）...")
        try:
            result = analyze_repositories_combined(x_algo_path, algo_path, api_key, topic)
            kb[topic] = {
                "summary": result.get("summary", ""),
                "marketing_insights": result.get("marketing_insights", [])
            }
            print(f"  完了: {len(kb[topic]['marketing_insights'])} インサイト取得")
        except Exception as e:
            print(f"    [WARNING] 統合解析失敗: {e}")
            kb[topic] = {"summary": "", "marketing_insights": []}

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

    print(f"\n✅ knowledge_base.json を生成しました: {OUTPUT_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Xkaiseki KB生成スクリプト")
    parser.add_argument("--x-algo-path", required=True, help="x-algorithm-main のパス")
    parser.add_argument("--algo-path", required=True, help="the-algorithm-main のパス")
    parser.add_argument("--dry-run", action="store_true", help="解析せず対象ファイル一覧とトークン見積もりを表示")
    args = parser.parse_args()

    if args.dry_run:
        dry_run(args.x_algo_path, args.algo_path)
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY 環境変数が設定されていません。")
        print("  export ANTHROPIC_API_KEY=sk-ant-... または .env ファイルに設定してください。")
        raise SystemExit(1)

    generate(args.x_algo_path, args.algo_path, api_key)


if __name__ == "__main__":
    main()
