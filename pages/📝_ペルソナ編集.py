# pages/📝_ペルソナ編集.py
import html
import streamlit as st
from src.config import load_config
from src.persona import PersonaManager

st.set_page_config(page_title="ペルソナ編集", page_icon="📝", layout="wide")

st.markdown("""
<style>
body { background: #0F172A; color: #F1F5F9; }
.profile-card {
    background: #1E293B;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border: 1px solid #334155;
}
.profile-label {
    font-size: 0.75rem;
    color: #94A3B8;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
}
.profile-value {
    font-size: 0.95rem;
    color: #F1F5F9;
}
.diff-box {
    background: #1E293B;
    border-radius: 8px;
    padding: 14px 18px;
    border-left: 4px solid;
    font-size: 0.93rem;
    line-height: 1.75;
    white-space: pre-wrap;
    word-break: break-word;
    min-height: 100px;
}
</style>
""", unsafe_allow_html=True)

# ===== セッション初期化 =====
if "persona_manager" not in st.session_state:
    st.session_state.persona_manager = PersonaManager()
if "rewrite_result" not in st.session_state:
    st.session_state.rewrite_result = None

manager: PersonaManager = st.session_state.persona_manager

st.title("📝 分身ペルソナ 文章編集ツール")
st.caption(
    "日記やツイートを読み込んでAIに「あなたらしさ」を学習させ、"
    "文章をあなたの言葉で書き直します。"
)

tab_create, tab_edit = st.tabs(["🧬 ペルソナ作成", "✏️ 文章を書き直す"])


# ===== Tab 1: ペルソナ作成 =====
with tab_create:
    config = load_config()

    st.subheader("① 学習用サンプルをアップロード")

    col_diary, col_tweets = st.columns(2)

    with col_diary:
        st.markdown("**日記・メモ・過去の文章 (.txt / .md)**")
        diary_files = st.file_uploader(
            "日記ファイル",
            type=["txt", "md"],
            accept_multiple_files=True,
            key="diary_upload",
            label_visibility="collapsed",
        )

    with col_tweets:
        st.markdown("**X ツイートエクスポート (tweets.js / .csv)**")
        st.caption("X設定 → アーカイブリクエスト → data/tweets.js を使用")
        tweet_file = st.file_uploader(
            "ツイートファイル",
            type=["js", "csv"],
            accept_multiple_files=False,
            key="tweet_upload",
            label_visibility="collapsed",
        )

    # ── サンプルテキスト収集 ──
    sample_texts: list[str] = []

    if diary_files:
        for f in diary_files:
            content = f.read().decode("utf-8", errors="ignore")
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            sample_texts.extend(paragraphs)
        st.success(f"✅ 日記/メモ: {len(diary_files)} ファイル読み込み済み")

    if tweet_file:
        content = tweet_file.read().decode("utf-8", errors="ignore")
        try:
            if tweet_file.name.endswith(".js"):
                tweets = manager.parse_tweets_js(content)
            else:
                tweets = manager.parse_tweets_csv(content)
            sample_texts.extend(tweets)
            st.success(f"✅ ツイート: {len(tweets)} 件読み込み済み")
        except Exception as e:
            st.error(f"❌ ツイートファイルの解析に失敗しました: {e}")

    if sample_texts:
        used = min(len(sample_texts), 60)
        st.info(
            f"📊 合計 **{len(sample_texts)} 件** のサンプルを収集しました"
            f"（上位 **{used} 件** を分析に使用）"
        )

    st.subheader("② Claude API キーの確認")
    api_key_input = st.text_input(
        "Claude API キー (sk-ant-...)",
        value=config.get("claude_api_key", ""),
        type="password",
        help="ホーム画面で設定したキーが自動入力されます",
    )

    st.subheader("③ 文体を分析してペルソナを作成")

    if not sample_texts:
        st.caption("⬆️ まずサンプルファイルをアップロードしてください")

    if st.button(
        "🧬 ペルソナを分析・作成",
        type="primary",
        disabled=not sample_texts or not api_key_input,
    ):
        combined = manager.combine_samples(sample_texts)
        with st.spinner("Claude があなたの文体を分析中... (10〜20 秒)"):
            try:
                manager.analyze_style(combined, api_key_input)
                st.session_state.persona_manager = manager
                st.success(
                    "✅ ペルソナの作成が完了しました！"
                    "「文章を書き直す」タブで使えます。"
                )
            except Exception as e:
                st.error(f"❌ 分析に失敗しました: {e}")

    # ── プロフィール表示 ──
    if manager.profile:
        st.divider()
        st.subheader("📋 現在のペルソナプロフィール")
        p = manager.profile

        col_left, col_right = st.columns(2)

        with col_left:
            for label, value in [
                ("トーン", p.tone),
                ("文の長さ", p.sentence_length),
                ("絵文字の使い方", p.emoji_usage),
                ("語尾・敬語スタイル", p.formality),
            ]:
                st.markdown(
                    f'<div class="profile-card">'
                    f'<div class="profile-label">{html.escape(label)}</div>'
                    f'<div class="profile-value">{html.escape(value)}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

        with col_right:
            st.markdown("**特徴的な語彙**")
            st.markdown(" ".join(f"`{v}`" for v in p.vocabulary[:15]))

            st.markdown("**口癖・決まり文句**")
            for expr in p.expressions:
                st.markdown(f"- {expr}")

            st.markdown("**独特のクセ**")
            for quirk in p.writing_quirks:
                st.markdown(f"- {quirk}")

        st.markdown("**総合分析**")
        st.markdown(f"> {p.raw_analysis}")

        if st.button("🗑️ ペルソナをリセット", type="secondary"):
            manager.profile = None
            st.session_state.persona_manager = manager
            st.session_state.rewrite_result = None
            st.rerun()


# ===== Tab 2: 文章編集 =====
with tab_edit:
    if not manager.profile:
        st.warning("⚠️ まず「ペルソナ作成」タブでプロフィールを作成してください。")
    else:
        p = manager.profile
        st.caption(f"使用中のペルソナ: **{p.tone}** / {p.formality}")

        config = load_config()

        input_text = st.text_area(
            "書き直したいテキストを入力",
            height=200,
            placeholder=(
                "ここに文章を貼り付けてください...\n\n"
                "SNS 投稿、メール、ブログ記事など何でも OK です。"
            ),
            key="rewrite_input",
        )

        api_key_edit = st.text_input(
            "Claude API キー",
            value=config.get("claude_api_key", ""),
            type="password",
            key="edit_api_key",
            label_visibility="collapsed",
        )

        if st.button(
            "✏️ ペルソナで書き直す",
            type="primary",
            disabled=not input_text or not api_key_edit,
        ):
            with st.spinner("ペルソナが書き直し中..."):
                try:
                    result = manager.rewrite_text(input_text, api_key_edit)
                    st.session_state.rewrite_result = result
                except Exception as e:
                    st.error(f"❌ 書き直しに失敗しました: {e}")

        if st.session_state.rewrite_result and input_text:
            st.divider()
            col_before, col_after = st.columns(2)

            with col_before:
                st.markdown("**修正前**")
                st.markdown(
                    f'<div class="diff-box" style="border-color:#64748B;">'
                    f"{html.escape(input_text)}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col_after:
                st.markdown("**修正後（ペルソナ適用）**")
                st.markdown(
                    f'<div class="diff-box" style="border-color:#7c3aed;">'
                    f"{html.escape(st.session_state.rewrite_result)}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            st.download_button(
                "💾 修正後テキストをダウンロード (.txt)",
                data=st.session_state.rewrite_result,
                file_name="rewritten.txt",
                mime="text/plain",
            )
