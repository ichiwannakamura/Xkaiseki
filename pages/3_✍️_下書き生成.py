# pages/3_✍️_下書き生成.py
"""Grok でリサーチ→ペルソナ人格で下書きを自動生成・管理するページ。"""
import streamlit as st
from src.config import load_config
from src.persona.persona_store import list_personas, get_persona
from src.persona.task_store import list_tasks, get_task, update_status
from src.persona.draft_store import list_drafts, save_draft, update_draft, delete_draft
from src.persona.grok_writer import research_topic, generate_draft

st.set_page_config(page_title="下書き生成", page_icon="✍️", layout="wide")

st.markdown("""
<style>
body { background: #0F172A; color: #F1F5F9; }
.draft-card {
    background: #1E293B; border: 1px solid #334155;
    border-radius: 12px; padding: 16px; margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

st.title("✍️ 下書き生成")
st.caption("タスクを選択 → Grok が最新情報を調査 → ペルソナ人格で下書きを自動生成します。")

# Grok API キー確認
config = load_config()
grok_api_key = config.get("grok_api_key", "")
if not grok_api_key:
    st.error("❌ Grok APIキーが設定されていません。ホームの「⚙ 設定」から登録してください。")
    st.stop()

personas = list_personas()
if not personas:
    st.warning("先に「ペルソナ管理」ページでペルソナを作成してください。")
    st.stop()

persona_map = {p["id"]: p for p in personas}

tab_gen, tab_drafts = st.tabs(["🤖 下書き生成", "📂 下書き一覧"])

# ===== 生成タブ =====
with tab_gen:
    st.subheader("タスクから生成")

    pending_tasks = list_tasks(status="pending") + list_tasks(status="processing")
    if not pending_tasks:
        st.info("処理待ちのタスクがありません。「タスク管理」ページで登録してください。")
    else:
        POST_TYPE_LABELS = {"tweet": "🐦 ツイート", "thread": "🧵 スレッド", "article": "📝 記事"}

        task_options = {
            t["id"]: f"{t.get('topic', '無題')[:40]} [{POST_TYPE_LABELS.get(t.get('post_type',''), '?')}] — {persona_map.get(t.get('persona_id', ''), {}).get('name', '不明')}"
            for t in pending_tasks
        }
        selected_task_id = st.selectbox(
            "タスクを選択 *",
            options=list(task_options.keys()),
            format_func=lambda x: task_options[x],
        )
        task = get_task(selected_task_id)
        persona = get_persona(task["persona_id"]) if task else None

        if task and persona:
            with st.expander("タスク詳細を確認"):
                st.json(task)

            st.subheader("生成オプション")
            col_opt1, col_opt2 = st.columns(2)
            with col_opt1:
                do_research = st.toggle("🔍 Grok に最新情報を調査させる", value=True)
            with col_opt2:
                extra_notes = st.text_input(
                    "追加指示（任意）",
                    value=task.get("notes", ""),
                    placeholder="例: ポジティブなトーンで。数字・データを含める。",
                )

            st.divider()

            if st.button("⚡ 生成開始", type="primary"):
                research_summary = ""

                # ── Step 1: リサーチ ──
                if do_research:
                    with st.status("🔍 Grok がリサーチ中...", expanded=True) as status_box:
                        st.write(f"テーマ: **{task['topic']}**")
                        try:
                            research_summary = research_topic(task["topic"], grok_api_key)
                            st.write("**リサーチ結果:**")
                            st.markdown(research_summary)
                            status_box.update(label="✅ リサーチ完了", state="complete")
                        except ValueError as e:
                            status_box.update(label=f"❌ リサーチ失敗: {e}", state="error")
                            st.stop()

                # ── Step 2: 下書き生成 ──
                with st.status("✍️ 下書きを生成中...", expanded=True) as status_box:
                    st.write(f"ペルソナ: **{persona['name']}** / 形式: **{task.get('post_type', 'tweet')}**")
                    try:
                        draft_content = generate_draft(
                            persona=persona,
                            topic=task["topic"],
                            post_type=task.get("post_type", "tweet"),
                            research_summary=research_summary,
                            extra_notes=extra_notes,
                            api_key=grok_api_key,
                        )
                        status_box.update(label="✅ 生成完了", state="complete")
                    except ValueError as e:
                        status_box.update(label=f"❌ 生成失敗: {e}", state="error")
                        st.stop()

                # ── Step 3: 保存 ──
                draft = save_draft({
                    "task_id": task["id"],
                    "persona_id": task["persona_id"],
                    "persona_name": persona.get("name", ""),
                    "topic": task["topic"],
                    "post_type": task.get("post_type", "tweet"),
                    "content": draft_content,
                    "research_summary": research_summary,
                    "extra_notes": extra_notes,
                })
                update_status(task["id"], "done")

                st.success("🎉 下書きを保存しました！")
                st.subheader("生成された下書き")
                st.markdown(draft_content)
                char_count = len(draft_content)
                st.caption(f"文字数: {char_count} 字")

# ===== 下書き一覧タブ =====
with tab_drafts:
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_persona_id = st.selectbox(
            "ペルソナで絞り込み",
            options=["all"] + [p["id"] for p in personas],
            format_func=lambda x: "すべて" if x == "all" else persona_map.get(x, {}).get("name", x),
        )
    with col_f2:
        filter_draft_status = st.selectbox(
            "ステータスで絞り込み",
            options=["all", "draft", "approved", "posted"],
            format_func=lambda x: {"all": "すべて", "draft": "📝 下書き", "approved": "✅ 承認済み", "posted": "🚀 投稿済み"}.get(x, x),
        )

    drafts = list_drafts(persona_id=None if filter_persona_id == "all" else filter_persona_id)
    if filter_draft_status != "all":
        drafts = [d for d in drafts if d.get("status") == filter_draft_status]

    if not drafts:
        st.info("下書きがありません。")
    else:
        STATUS_OPTIONS = ["draft", "approved", "posted"]
        STATUS_LABELS_D = {"draft": "📝 下書き", "approved": "✅ 承認済み", "posted": "🚀 投稿済み"}
        POST_TYPE_LABELS = {"tweet": "🐦 ツイート", "thread": "🧵 スレッド", "article": "📝 記事"}

        for d in drafts:
            with st.container():
                st.markdown(f"**{d.get('topic', '無題')[:60]}**  —  {d.get('persona_name', '不明')} / {POST_TYPE_LABELS.get(d.get('post_type', ''), '?')}")

                col_s, col_del = st.columns([2, 1])
                with col_s:
                    new_status = st.selectbox(
                        "ステータス",
                        options=STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(d.get("status", "draft")),
                        format_func=lambda x: STATUS_LABELS_D.get(x, x),
                        key=f"dstatus_{d['id']}",
                        label_visibility="collapsed",
                    )
                    if new_status != d.get("status"):
                        update_draft(d["id"], status=new_status)
                        st.rerun()
                with col_del:
                    if st.button("🗑️ 削除", key=f"ddel_{d['id']}"):
                        delete_draft(d["id"])
                        st.rerun()

                # 編集可能な下書き本文
                edited = st.text_area(
                    "下書き本文（直接編集可）",
                    value=d.get("content", ""),
                    height=200,
                    key=f"dcontent_{d['id']}",
                )
                col_save, col_copy = st.columns([1, 4])
                with col_save:
                    if st.button("💾 保存", key=f"dsave_{d['id']}"):
                        update_draft(d["id"], content=edited)
                        st.success("保存しました")

                if d.get("research_summary"):
                    with st.expander("📊 リサーチサマリーを見る"):
                        st.markdown(d["research_summary"])

                st.caption(f"作成: {d.get('created_at', '')[:16]}  /  更新: {d.get('updated_at', '')[:16]}")
                st.divider()
