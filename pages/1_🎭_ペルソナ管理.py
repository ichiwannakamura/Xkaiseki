# pages/1_🎭_ペルソナ管理.py
"""SNS アカウントのペルソナ（人格）を作成・編集・削除するページ。"""
import json
import streamlit as st
from src.persona.persona_store import list_personas, save_persona, delete_persona, persona_to_system_prompt

st.set_page_config(page_title="ペルソナ管理", page_icon="🎭", layout="wide")

st.markdown("""
<style>
body { background: #0F172A; color: #F1F5F9; }
.persona-card {
    background: #1E293B; border: 1px solid #334155;
    border-radius: 12px; padding: 16px; margin-bottom: 12px;
}
.badge {
    display: inline-block; padding: 2px 10px; border-radius: 99px;
    font-size: 0.75rem; font-weight: 600; margin: 2px;
}
</style>
""", unsafe_allow_html=True)

st.title("🎭 ペルソナ管理")
st.caption("SNS アカウントに与える「人格コンテキスト」を定義・管理します。")

tab_list, tab_new = st.tabs(["📋 一覧", "➕ 新規作成 / 編集"])

# ===== 一覧タブ =====
with tab_list:
    personas = list_personas()
    if not personas:
        st.info("ペルソナがまだありません。「新規作成」タブから作りましょう。")
    else:
        for p in personas:
            ps = p.get("personality", {})
            ss = p.get("sns_style", {})
            with st.container():
                col_info, col_actions = st.columns([5, 1])
                with col_info:
                    st.markdown(f"### {p.get('name', '無名')} `{p.get('display_name', '')}`")
                    st.markdown(f"_{p.get('bio', '（自己紹介なし）')}_")
                    traits_html = "".join(
                        f'<span class="badge" style="background:#7c3aed22;color:#a78bfa;">#{t}</span>'
                        for t in ps.get("traits", [])
                    )
                    exp_html = "".join(
                        f'<span class="badge" style="background:#0369a122;color:#38bdf8;">🔬{e}</span>'
                        for e in p.get("expertise", [])
                    )
                    st.markdown(traits_html + exp_html, unsafe_allow_html=True)
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("口調", {"casual": "カジュアル", "formal": "フォーマル", "neutral": "ニュートラル"}.get(ps.get("tone", "neutral"), "−"))
                    col_b.metric("絵文字", ss.get("emoji_usage", "−"))
                    col_c.metric("文字数傾向", ss.get("avg_length", "−"))

                with col_actions:
                    if st.button("編集", key=f"edit_{p['id']}"):
                        st.session_state["edit_persona"] = p
                        st.rerun()
                    if st.button("削除", key=f"del_{p['id']}", type="secondary"):
                        delete_persona(p["id"])
                        st.success(f"「{p['name']}」を削除しました")
                        st.rerun()

                with st.expander("JSON / システムプロンプトを確認"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.code(json.dumps(p, ensure_ascii=False, indent=2), language="json")
                    with c2:
                        st.text_area("システムプロンプト（AI に渡す文）", value=persona_to_system_prompt(p), height=300, key=f"sp_{p['id']}")

                st.divider()

# ===== 新規作成 / 編集タブ =====
with tab_new:
    editing = st.session_state.get("edit_persona", {})

    st.subheader("基本情報")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("アカウント名（ID）*", value=editing.get("name", ""), placeholder="例: tech_observer_jp")
    with col2:
        display_name = st.text_input("表示名", value=editing.get("display_name", ""), placeholder="例: テック観察者")
    bio = st.text_area("自己紹介 / bio", value=editing.get("bio", ""), placeholder="例: AI・テック・ビジネスを中心に情報発信。")

    st.subheader("人格 / 口調")
    ps = editing.get("personality", {})
    col3, col4 = st.columns(2)
    with col3:
        tone = st.selectbox(
            "口調スタイル",
            options=["casual", "formal", "neutral"],
            index=["casual", "formal", "neutral"].index(ps.get("tone", "neutral")),
            format_func=lambda x: {"casual": "カジュアル（タメ口）", "formal": "フォーマル（敬語）", "neutral": "ニュートラル（中性）"}[x],
        )
    with col4:
        traits_input = st.text_input(
            "性格特性（カンマ区切り）",
            value=", ".join(ps.get("traits", [])),
            placeholder="例: 分析的, 皮肉的, 好奇心旺盛",
        )

    values = st.text_area("価値観・信念", value=ps.get("values", ""), placeholder="例: テクノロジーで社会課題を解決することを重視する。")
    speaking_style = st.text_area(
        "話し方の詳細",
        value=ps.get("speaking_style", ""),
        placeholder="例: 短文でキレよく。専門用語を自然に混ぜる。文末は「〜だな」「〜と思う」など断定を避ける。",
        height=100,
    )

    st.subheader("専門・興味分野 / 避けるトピック")
    col5, col6 = st.columns(2)
    with col5:
        expertise_input = st.text_input(
            "専門・興味分野（カンマ区切り）",
            value=", ".join(editing.get("expertise", [])),
            placeholder="例: AI, スタートアップ, 量子コンピューター",
        )
    with col6:
        avoid_input = st.text_input(
            "避けるトピック（カンマ区切り）",
            value=", ".join(editing.get("avoid_topics", [])),
            placeholder="例: 政治, 宗教, 特定人物への批判",
        )

    st.subheader("SNS 投稿スタイル")
    ss = editing.get("sns_style", {})
    col7, col8, col9, col10 = st.columns(4)
    with col7:
        emoji_usage = st.selectbox(
            "絵文字使用",
            options=["none", "rare", "moderate", "heavy"],
            index=["none", "rare", "moderate", "heavy"].index(ss.get("emoji_usage", "rare")),
            format_func=lambda x: {"none": "なし", "rare": "たまに", "moderate": "普通", "heavy": "多め"}[x],
        )
    with col8:
        avg_length = st.selectbox(
            "文字数傾向",
            options=["short", "medium", "long"],
            index=["short", "medium", "long"].index(ss.get("avg_length", "medium")),
            format_func=lambda x: {"short": "短文（〜80字）", "medium": "中文（〜140字）", "long": "長文（140字超）"}[x],
        )
    with col9:
        hashtag_count = st.number_input("ハッシュタグ数", min_value=0, max_value=10, value=ss.get("hashtag_count", 2))
    with col10:
        hashtags_input = st.text_input(
            "よく使うハッシュタグ",
            value=" ".join(ss.get("hashtags", [])),
            placeholder="#AI #テック",
        )

    st.divider()
    col_save, col_clear = st.columns([1, 4])
    with col_save:
        save_btn = st.button("💾 保存", type="primary", disabled=not name.strip())
    with col_clear:
        if editing and st.button("新規作成モードに戻る"):
            st.session_state.pop("edit_persona", None)
            st.rerun()

    if save_btn:
        persona = {
            "id": editing.get("id"),
            "name": name.strip(),
            "display_name": display_name.strip(),
            "bio": bio.strip(),
            "personality": {
                "tone": tone,
                "traits": [t.strip() for t in traits_input.split(",") if t.strip()],
                "values": values.strip(),
                "speaking_style": speaking_style.strip(),
            },
            "expertise": [e.strip() for e in expertise_input.split(",") if e.strip()],
            "avoid_topics": [a.strip() for a in avoid_input.split(",") if a.strip()],
            "sns_style": {
                "emoji_usage": emoji_usage,
                "avg_length": avg_length,
                "hashtag_count": int(hashtag_count),
                "hashtags": hashtags_input.split(),
            },
        }
        saved = save_persona(persona)
        st.session_state.pop("edit_persona", None)
        st.success(f"✅ 「{saved['name']}」を保存しました！")
        st.rerun()
