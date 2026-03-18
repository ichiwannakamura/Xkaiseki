"""
Xkaiseki — X推薦アルゴリズム解析チャット
Streamlit メインUI
"""
import streamlit as st
from pathlib import Path
from src.knowledge_base import load_knowledge_base
from src.chat_engine import chat

# ─── ページ設定 ───────────────────────────────────────────────
st.set_page_config(
    page_title="Xkaiseki",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ─── ダークテーマ CSS ─────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@600;700&display=swap');

  :root {
    --bg-main:    #0F172A;
    --bg-card:    #1E293B;
    --border:     #334155;
    --text-main:  #F1F5F9;
    --text-sub:   #94A3B8;
    --accent:     #1D9BF0;
    --success:    #22C55E;
    --warning:    #F59E0B;
    --error:      #EF4444;
  }

  .stApp { background-color: var(--bg-main); color: var(--text-main); }
  h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: var(--text-main); }
  p, li, label { font-family: 'Inter', sans-serif; font-size: 1rem; color: var(--text-main); }

  /* チャットメッセージ */
  .chat-user {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 8px 0;
    text-align: right;
  }
  .chat-assistant {
    background: var(--bg-card);
    border: 1px solid var(--accent);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 8px 0;
  }

  /* クイック質問ボタン */
  .stButton > button {
    background: var(--bg-card);
    color: var(--text-main);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.875rem;
    transition: all 0.2s;
    min-height: 44px;
    cursor: pointer;
  }
  .stButton > button:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
</style>
""", unsafe_allow_html=True)

# ─── Session State 初期化 ────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "kb" not in st.session_state:
    st.session_state.kb = {}
if "kb_loaded" not in st.session_state:
    st.session_state.kb_loaded = False

# ─── KB ロード ────────────────────────────────────────────────
KB_PATH = Path(__file__).parent / "data" / "knowledge_base.json"

if not st.session_state.kb_loaded:
    if KB_PATH.exists():
        try:
            st.session_state.kb = load_knowledge_base(str(KB_PATH))
            st.session_state.kb_loaded = True
        except Exception as e:
            st.session_state.kb = {}
    else:
        st.session_state.kb = {}

# ─── サイドバー ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Xkaiseki")
    st.markdown("X推薦アルゴリズム解析チャット")
    st.divider()

    if not st.session_state.kb_loaded:
        st.warning("⚠️ knowledge_base.json が見つかりません。\n`generate_kb.py` を実行してください。")
    else:
        st.success("✅ ナレッジベース読み込み済み")

    st.divider()
    st.markdown("### 使い方ガイド")
    st.markdown("""
1. Anthropic API キーを入力
2. 質問を入力または下のボタンをクリック
3. マーケター向け + 技術的解説が届きます

**API キーの取得:**
[Anthropic Console](https://console.anthropic.com)
""")

    st.divider()
    if st.button("会話をリセット", use_container_width=True):
        st.session_state.history = []
        st.rerun()

# ─── メインコンテンツ ─────────────────────────────────────────
st.markdown("# 🔍 Xkaiseki")
st.markdown("X推薦アルゴリズムに基づく、アフィリエイトアカウント運用アドバイザー")

# API キー入力
api_key_input = st.text_input(
    "🔑 Anthropic API Key",
    type="password",
    placeholder="sk-ant-...",
    value=st.session_state.api_key,
    help="あなた自身のAPIキーを使用します。サーバーには保存されません。"
)
if api_key_input:
    st.session_state.api_key = api_key_input

# ─── クイック質問ボタン ───────────────────────────────────────
QUICK_QUESTIONS = [
    "1万インプレッションへのロードマップを教えて",
    "絶対にやってはいけないNG行動を教えて",
    "いいねの正しい使い方と影響を教えて",
    "For Youに出やすくなる投稿の条件は？",
    "アフィリエイトリンクはどう扱えばいい？"
]

st.markdown("**よくある質問:**")
cols = st.columns(len(QUICK_QUESTIONS))
quick_question = None
for col, q in zip(cols, QUICK_QUESTIONS):
    with col:
        label = q[:10] + "…" if len(q) > 10 else q
        if st.button(label, key=f"quick_{q}", help=q):
            quick_question = q

st.divider()

# ─── チャット表示 ─────────────────────────────────────────────
st.markdown("### 💬 チャット")

# ウェルカムメッセージ
if not st.session_state.history:
    st.markdown("""
<div class="chat-assistant">
🤖 <strong>Xkaisekiへようこそ。</strong><br>
X（旧Twitter）の推薦アルゴリズムについて何でも聞いてください。<br>
アフィリエイトアカウントで成果を出すための具体的なアドバイスをお伝えします。
</div>
""", unsafe_allow_html=True)

# 会話履歴を表示
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-assistant">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

# ─── 入力エリア ───────────────────────────────────────────────
chat_disabled = not bool(st.session_state.api_key)

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "質問を入力",
        placeholder="例：いいねはスコアにどう影響しますか？" if not chat_disabled else "APIキーを入力してください",
        disabled=chat_disabled,
        height=80,
        label_visibility="collapsed"
    )
    submit = st.form_submit_button(
        "送信 →",
        disabled=chat_disabled,
        use_container_width=True
    )

# ─── 送信処理 ─────────────────────────────────────────────────
question = quick_question or (user_input.strip() if submit and user_input.strip() else None)

if question:
    if not st.session_state.api_key:
        st.error("APIキーを入力してください。")
    else:
        st.session_state.history.append({"role": "user", "content": question})

        with st.spinner("解析中..."):
            answer = chat(
                question=question,
                api_key=st.session_state.api_key,
                kb=st.session_state.kb,
                history=st.session_state.history[:-1]
            )

        st.session_state.history.append({"role": "assistant", "content": answer})
        st.rerun()
