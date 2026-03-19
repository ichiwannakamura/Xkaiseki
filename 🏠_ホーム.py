# 🏠_ホーム.py
import streamlit as st
from pathlib import Path
from src.config import load_config, save_config, is_setup_complete, MODEL_NAMES
from src.retriever import search, DEFAULT_DB_PATH
from src.dispatcher import dispatch

st.set_page_config(page_title="Xkaiseki", page_icon="🔍", layout="wide")

# ===== CSS =====
st.markdown("""
<style>
body { background: #0F172A; color: #F1F5F9; }
.model-chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px;
  border-radius: 8px; border: 2px solid #334155; cursor: pointer;
  font-size: 0.82rem; font-weight: 500; margin-right: 6px; }
</style>
""", unsafe_allow_html=True)

MODEL_COLORS = {
    "claude": "#7c3aed", "gpt": "#10a37f", "gemini": "#4285f4", "grok": "#e7482e"
}
MODEL_LABELS = {
    "claude": "Claude", "gpt": "GPT", "gemini": "Gemini", "grok": "Grok"
}

# ===== セッション初期化 =====
if "history" not in st.session_state:
    st.session_state.history = []
if "show_setup" not in st.session_state:
    st.session_state.show_setup = not is_setup_complete()
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "tab"
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "claude"
if "last_answers" not in st.session_state:
    st.session_state.last_answers = {}


# ===== セットアップ画面 =====
def render_setup():
    st.title("⚙️ セットアップ")
    st.caption("初回のみ設定します。次回から自動で読み込まれます。")

    config = load_config()

    st.subheader("使用するモデルを選択（複数可）")
    enabled = set(config.get("enabled_models", []))
    new_enabled = []
    cols = st.columns(4)
    for i, name in enumerate(MODEL_NAMES):
        with cols[i]:
            if st.checkbox(MODEL_LABELS[name], value=name in enabled, key=f"chk_{name}"):
                new_enabled.append(name)

    st.subheader("APIキー")
    claude_key = st.text_input("Claude (Anthropic)", value=config.get("claude_api_key", ""), type="password")
    gpt_key    = st.text_input("GPT (OpenAI)",       value=config.get("gpt_api_key", ""),    type="password")
    gemini_key = st.text_input("Gemini (Google)",    value=config.get("gemini_api_key", ""), type="password")
    grok_key   = st.text_input("Grok (xAI)",         value=config.get("grok_api_key", ""),   type="password")

    st.subheader("検索方式")
    search_mode = st.radio(
        "ソースコード検索方式",
        options=["fts", "vector"],
        format_func=lambda x: "キーワード検索（追加不要）" if x == "fts" else "意味検索（初回~100MBダウンロード）",
        index=0 if config.get("search_mode", "fts") == "fts" else 1,
        horizontal=True,
    )

    if not DEFAULT_DB_PATH.exists():
        st.warning("⚠️ ソースコードインデックスが見つかりません。index_source.py を実行してください。")

    if st.button("チャットを開始 →", type="primary", disabled=not new_enabled):
        save_config({
            "claude_api_key": claude_key,
            "gpt_api_key": gpt_key,
            "gemini_api_key": gemini_key,
            "grok_api_key": grok_key,
            "enabled_models": new_enabled,
            "search_mode": search_mode,
        })
        st.session_state.show_setup = False
        st.rerun()


# ===== チャット画面 =====
def render_chat():
    config = load_config()
    enabled_models = config.get("enabled_models", ["claude"])
    search_mode = config.get("search_mode", "fts")
    api_keys = {
        "claude": config["claude_api_key"],
        "gpt":    config["gpt_api_key"],
        "gemini": config["gemini_api_key"],
        "grok":   config["grok_api_key"],
    }

    # ヘッダー
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🔍 Xkaiseki")
    with col2:
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("タブ"):
                st.session_state.view_mode = "tab"
        with c2:
            if st.button("並べて"):
                st.session_state.view_mode = "grid"
        with c3:
            if st.button("⚙ 設定"):
                st.session_state.show_setup = True
                st.rerun()

    # モデル選択チップ（複数選択）
    st.write("**表示モデル:**")
    display_models = list(st.session_state.get("display_models", enabled_models))
    cols = st.columns(len(MODEL_NAMES))
    new_display = []
    for i, name in enumerate(MODEL_NAMES):
        if name not in enabled_models:
            continue
        with cols[i]:
            checked = st.checkbox(MODEL_LABELS[name], value=name in display_models, key=f"disp_{name}")
            if checked:
                new_display.append(name)
    if new_display:
        st.session_state.display_models = new_display
    else:
        st.session_state.display_models = enabled_models

    st.divider()

    # チャット履歴 + 回答表示
    for i, turn in enumerate(st.session_state.history):
        with st.chat_message("user"):
            st.write(turn["question"])
        with st.chat_message("assistant"):
            _render_answers(turn["answers"], st.session_state.display_models, f"hist_{i}")

    # 入力
    question = st.chat_input("質問を入力...")
    if question:
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("全モデルが回答中..."):
                chunks = []
                if DEFAULT_DB_PATH.exists():
                    try:
                        chunks = search(question, mode=search_mode)
                    except Exception:
                        pass

                answers = dispatch(
                    question=question,
                    context_chunks=chunks,
                    model_names=enabled_models,
                    api_keys=api_keys,
                    history=[
                        msg
                        for turn in st.session_state.history
                        for msg in [
                            {"role": "user", "content": turn["question"]},
                            {"role": "assistant", "content": next(iter(turn["answers"].values()), "")},
                        ]
                    ],
                )
            _render_answers(answers, st.session_state.display_models, f"new_{len(st.session_state.history)}")

        st.session_state.history.append({"question": question, "answers": answers})
        if len(st.session_state.history) > 10:
            st.session_state.history = st.session_state.history[-10:]
        st.rerun()


def _render_answers(answers: dict, display_models: list[str], key_prefix: str):
    """タブ または 横並びで回答を表示する。"""
    models_to_show = [m for m in display_models if m in answers]
    if not models_to_show:
        st.info("表示するモデルを選択してください。")
        return

    if st.session_state.view_mode == "tab":
        tabs = st.tabs([MODEL_LABELS[m] for m in models_to_show])
        for tab, name in zip(tabs, models_to_show):
            with tab:
                st.write(answers[name])
    else:
        cols = st.columns(len(models_to_show))
        for col, name in zip(cols, models_to_show):
            with col:
                st.markdown(f"**{MODEL_LABELS[name]}**")
                st.write(answers[name])


# ===== メイン =====
if st.session_state.show_setup:
    render_setup()
else:
    render_chat()
