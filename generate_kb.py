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

    print("=== DRY RUN MODE ===")
    for repo_name, repo_path in [("x-algorithm-main", x_algo_path), ("the-algorithm-main", algo_path)]:
        try:
            content = _read_key_files(repo_path)
            tokens = estimate_tokens(content)
            print(f"\n[{repo_name}]")
            print(f"  読み込み文字数: {len(content):,}")
            print(f"  推定トークン数: {tokens:,}")
            print(f"  解析トピック数: {len(ANALYSIS_TOPICS)}")
            print(f"  推定コスト: ~{tokens * len(ANALYSIS_TOPICS) // 1000 * 3}円（sonnet-4-6換算）")
        except FileNotFoundError as e:
            print(f"  [ERROR] {e}")
    print("\n実際に生成する場合は --dry-run を外してください。")


def generate(x_algo_path: str, algo_path: str, api_key: str) -> None:
    """両リポジトリを解析して knowledge_base.json を生成する。"""
    from src.analyzer import analyze_repository, ANALYSIS_TOPICS

    kb = {}
    repos = [
        ("x-algorithm-main", x_algo_path),
        ("the-algorithm-main", algo_path)
    ]

    for topic in ANALYSIS_TOPICS:
        print(f"\n[解析中] トピック: {topic}")
        merged_insights = []
        merged_summary = ""

        for repo_name, repo_path in repos:
            print(f"  - {repo_name} を解析中...")
            try:
                result = analyze_repository(repo_path, api_key, topic)
                merged_insights.extend(result.get("marketing_insights", []))
                if result.get("summary"):
                    merged_summary += f"[{repo_name}] {result['summary']} "
            except Exception as e:
                print(f"    [WARNING] {repo_name} の解析失敗: {e}")

        kb[topic] = {
            "summary": merged_summary.strip(),
            "marketing_insights": list(dict.fromkeys(merged_insights))  # 重複除去
        }
        print(f"  完了: {len(merged_insights)} インサイト取得")

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
