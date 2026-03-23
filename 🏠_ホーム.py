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
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
  flex: 1; color: white !important; font-size: 1.25rem !important;
  font-weight: 800 !important; border-radius: 8px 8px 0 0 !important;
  justify-content: center; padding: 12px 8px !important; transition: opacity 0.2s; }
.stTabs [aria-selected="false"] { opacity: 0.4 !important; }
.stTabs [aria-selected="true"]  { opacity: 1   !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"]    { display: none !important; }
.ai-card-header { font-size: 1.25rem; font-weight: 800; padding: 10px 16px;
  border-radius: 4px; margin-bottom: 8px; }
/* 分割表示: コードブロックが列幅をはみ出ないよう制御 */
[data-testid='stColumn'] pre { overflow-x: auto !important; }
[data-testid='stColumn'] .stMarkdown { min-width: 0; }
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
if "is_answering" not in st.session_state:
    st.session_state.is_answering = False
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ===== APIキー形式チェック =====
_KEY_PREFIXES = {
    "claude": "sk-ant-",
    "gpt": "sk-",
    "gemini": "AIza",
    "grok": "xai-",
}

def _key_status(key: str, model: str) -> tuple[str, str]:
    """入力値の形式を即時チェック。(icon, message) を返す。"""
    if not key:
        return "", ""
    prefix = _KEY_PREFIXES[model]
    if key.startswith(prefix):
        return "✅", f"形式OK（{prefix}...）"
    return "❌", f"形式エラー — {prefix}... で始まるはずです"


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
    entries = [
        ("claude", "Claude (Anthropic)", "claude_api_key"),
        ("gpt",    "GPT (OpenAI)",       "gpt_api_key"),
        ("gemini", "Gemini (Google)",    "gemini_api_key"),
        ("grok",   "Grok (xAI)",         "grok_api_key"),
    ]
    keys = {}
    for model, label, cfg_key in entries:
        val = st.text_input(label, value=config.get(cfg_key, ""), type="password", key=f"inp_{model}")
        icon, msg = _key_status(val, model)
        if icon == "✅":
            st.success(f"{icon} {msg}", icon=None)
        elif icon == "❌":
            st.error(f"{icon} {msg}", icon=None)
        keys[model] = val

    claude_key = keys["claude"]
    gpt_key    = keys["gpt"]
    gemini_key = keys["gemini"]
    grok_key   = keys["grok"]

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
    is_answering = st.session_state.is_answering

    # ヘッダー（タイトル → ボタン行の順）
    st.title("🔍 Xソース解析チャット")
    c1, c2, c3, _ = st.columns([1, 1, 1, 5])
    with c1:
        if st.button("タブ", disabled=is_answering):
            st.session_state.view_mode = "tab"
    with c2:
        if st.button("分割表示", disabled=is_answering):
            st.session_state.view_mode = "grid"
    with c3:
        if st.button("⚙ 設定", disabled=is_answering):
            st.session_state.show_setup = True
            st.rerun()

    _render_interactive_area(enabled_models, is_answering)

    # 回答中: pending_question を処理
    if is_answering and st.session_state.pending_question:
        question = st.session_state.pending_question
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
        st.session_state.history.append({"question": question, "answers": answers})
        if len(st.session_state.history) > 10:
            st.session_state.history = st.session_state.history[-10:]
        st.session_state.is_answering = False
        st.session_state.pending_question = None
        st.rerun()

    # 入力（回答中は無効）
    question = st.chat_input("質問を入力...", disabled=is_answering)
    if question:
        st.session_state.pending_question = question
        st.session_state.is_answering = True
        st.rerun()


def _render_answers(answers: dict, display_models: list[str], key_prefix: str):
    """タブ または 横並びで回答を表示する。"""
    models_to_show = [m for m in display_models if m in answers]
    if not models_to_show:
        st.info("表示するモデルを選択してください。")
        return

    if st.session_state.view_mode == "tab":
        # タブを各モデルカラーで塗る動的CSS（選択=不透明、非選択=半透明）
        tab_css = "".join(
            f"[data-baseweb='tab-list'] [data-baseweb='tab']:nth-child({i})"
            f"{{ background: {MODEL_COLORS[name]} !important; color: white !important; }}"
            for i, name in enumerate(models_to_show, 1)
        )
        st.markdown(f"<style>{tab_css}</style>", unsafe_allow_html=True)
        tabs = st.tabs([MODEL_LABELS[m] for m in models_to_show])
        for tab, name in zip(tabs, models_to_show):
            with tab:
                st.markdown(answers[name])
    else:
        # 分割表示: :has() で ai-card-header の data-model 属性を持つ列だけにスタイルを当てる
        # （ヘッダーボタン行・チェックボックス行は data-model がないので影響ゼロ）
        col_css = "".join(
            f"[data-testid='stColumn']:has([data-model='{name}']) > div:first-child"
            f"{{ border: 2px solid {MODEL_COLORS[name]} !important;"
            f"border-radius: 10px !important;"
            f"background: {MODEL_COLORS[name]}1A !important; }}"
            for name in models_to_show
        )
        st.markdown(f"<style>{col_css}</style>", unsafe_allow_html=True)
        cols = st.columns(len(models_to_show))
        for col, name in zip(cols, models_to_show):
            with col:
                color = MODEL_COLORS[name]
                st.markdown(
                    f'<div class="ai-card-header" data-model="{name}" style="background:{color}; color:#fff;">{MODEL_LABELS[name]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(answers[name])


@st.fragment
def _render_interactive_area(enabled_models: list[str], is_answering: bool) -> None:
    """モデル選択 + チャット履歴を fragment に包み、モデル切替時のページスクロールを防ぐ。"""
    # モデル選択チップ
    st.write("**表示モデル:**")
    display_models = list(st.session_state.get("display_models", enabled_models))
    cols = st.columns(len(MODEL_NAMES))
    new_display = []
    for i, name in enumerate(MODEL_NAMES):
        if name not in enabled_models:
            continue
        with cols[i]:
            checked = st.checkbox(
                MODEL_LABELS[name],
                value=name in display_models,
                key=f"disp_{name}",
                disabled=is_answering,
            )
            if checked:
                new_display.append(name)
    if new_display:
        st.session_state.display_models = new_display
    else:
        st.session_state.display_models = list(enabled_models)

    st.divider()

    # チャット履歴
    current_display = list(st.session_state.get("display_models", enabled_models))
    for i, turn in enumerate(st.session_state.history):
        with st.chat_message("user"):
            st.write(turn["question"])
        with st.chat_message("assistant"):
            _render_answers(turn["answers"], current_display, f"hist_{i}")


# ===== メイン =====
if st.session_state.show_setup:
    render_setup()
else:
    render_chat()
