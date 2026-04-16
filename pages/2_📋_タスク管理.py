# pages/2_📋_タスク管理.py
"""投稿タスク（テーマ・ペルソナ・投稿形式）を登録・管理するページ。"""
import streamlit as st
from src.persona.persona_store import list_personas
from src.persona.task_store import list_tasks, save_task, delete_task, update_status, POST_TYPES

st.set_page_config(page_title="タスク管理", page_icon="📋", layout="wide")

st.markdown("""
<style>
body { background: #0F172A; color: #F1F5F9; }
</style>
""", unsafe_allow_html=True)

st.title("📋 タスク管理")
st.caption("どのペルソナで・何を・どの形式で投稿するか、タスクとして登録します。")

personas = list_personas()
if not personas:
    st.warning("先に「ペルソナ管理」ページでペルソナを作成してください。")
    st.stop()

persona_map = {p["id"]: p for p in personas}
persona_options = {p["id"]: f"{p['name']} ({p.get('display_name', '')})" for p in personas}

tab_list, tab_new = st.tabs(["📋 タスク一覧", "➕ タスク登録"])

STATUS_LABELS = {"pending": "⏳ 待機中", "processing": "🔄 処理中", "done": "✅ 完了"}
POST_TYPE_LABELS = {"tweet": "🐦 ツイート", "thread": "🧵 スレッド", "article": "📝 記事"}
PRIORITY_LABELS = {1: "🔵 低", 2: "🟡 中", 3: "🟠 高", 4: "🔴 最優先", 5: "🚨 緊急"}

# ===== 一覧タブ =====
with tab_list:
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        filter_persona = st.selectbox(
            "ペルソナで絞り込み",
            options=["all"] + list(persona_options.keys()),
            format_func=lambda x: "すべて" if x == "all" else persona_options.get(x, x),
        )
    with col_filter2:
        filter_status = st.selectbox(
            "ステータスで絞り込み",
            options=["all", "pending", "processing", "done"],
            format_func=lambda x: "すべて" if x == "all" else STATUS_LABELS.get(x, x),
        )

    tasks = list_tasks(
        persona_id=None if filter_persona == "all" else filter_persona,
        status=None if filter_status == "all" else filter_status,
    )

    if not tasks:
        st.info("タスクがありません。「タスク登録」タブから追加しましょう。")
    else:
        for t in tasks:
            persona_name = persona_options.get(t.get("persona_id", ""), "不明なペルソナ")
            with st.container():
                c1, c2, c3 = st.columns([5, 2, 1])
                with c1:
                    st.markdown(f"**{t.get('topic', '（テーマなし）')}**")
                    st.caption(f"{persona_name}  ·  {POST_TYPE_LABELS.get(t.get('post_type', ''), '？')}  ·  優先度: {PRIORITY_LABELS.get(t.get('priority', 2), '？')}")
                    if t.get("notes"):
                        st.markdown(f"_{t['notes']}_")
                with c2:
                    new_status = st.selectbox(
                        "ステータス",
                        options=["pending", "processing", "done"],
                        index=["pending", "processing", "done"].index(t.get("status", "pending")),
                        format_func=lambda x: STATUS_LABELS.get(x, x),
                        key=f"st_{t['id']}",
                        label_visibility="collapsed",
                    )
                    if new_status != t.get("status"):
                        update_status(t["id"], new_status)
                        st.rerun()
                with c3:
                    if st.button("🗑️", key=f"del_{t['id']}", help="削除"):
                        delete_task(t["id"])
                        st.rerun()
                st.divider()

# ===== タスク登録タブ =====
with tab_new:
    st.subheader("新しいタスクを登録")

    col_p, col_pt = st.columns(2)
    with col_p:
        selected_persona_id = st.selectbox(
            "ペルソナ *",
            options=list(persona_options.keys()),
            format_func=lambda x: persona_options[x],
        )
    with col_pt:
        post_type = st.selectbox(
            "投稿形式 *",
            options=list(POST_TYPE_LABELS.keys()),
            format_func=lambda x: POST_TYPE_LABELS[x],
        )

    topic = st.text_area(
        "投稿テーマ / リサーチキーワード *",
        placeholder="例: 最近のAI規制の動向について、欧州 AI Act の影響を日本の開発者視点で解説する",
        height=100,
    )
    notes = st.text_area(
        "追加指示・メモ（任意）",
        placeholder="例: 批判的な論調で。競合製品と比較する。特定のデータを引用する。",
        height=80,
    )
    priority = st.slider("優先度", min_value=1, max_value=5, value=2, format="%d")
    st.caption(PRIORITY_LABELS.get(priority, ""))

    if st.button("📌 タスクを登録", type="primary", disabled=not topic.strip()):
        task = save_task({
            "persona_id": selected_persona_id,
            "topic": topic.strip(),
            "post_type": post_type,
            "notes": notes.strip(),
            "priority": priority,
            "status": "pending",
        })
        st.success(f"✅ タスクを登録しました！「下書き生成」ページで実行できます。")
        st.balloons()
