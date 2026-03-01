try:
    import streamlit as st
except ImportError:
    raise SystemExit(1)

import logic
from database import Database, Request


def _seed_requests() -> list[Request]:
    return [
        Request(
            date="2026/01/14",
            title="競合動向の調査",
            requester="山田",
            email="yamada@example.com",
            deadline="2026/01/20",
            topic="国内の主要プレイヤーと直近の動き",
            prompt="主要プレイヤーを3社程度挙げ、直近1年の動きを整理してください。",
            report="結果待ち",
            correction="",
        ),
        Request(
            date="2026/01/12",
            title="技術トレンドの整理",
            requester="佐藤",
            email="sato@example.com",
            deadline="2026/01/18",
            topic="Python研修向けの最新トピック",
            prompt="初学者向けに重要な技術トレンドを3点に絞ってください。",
            report="結果待ち",
            correction="調査範囲を国内事例に絞ってください。",
        ),
    ]


def _init_state() -> None:
    if "page" not in st.session_state:
        st.session_state.page = "list"
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = None
    if "db" not in st.session_state:
        st.session_state.db = Database(_seed_requests())
    if "form_title" not in st.session_state:
        st.session_state.form_title = ""
    if "form_requester" not in st.session_state:
        st.session_state.form_requester = ""
    if "form_deadline" not in st.session_state:
        st.session_state.form_deadline = ""
    if "form_topic" not in st.session_state:
        st.session_state.form_topic = ""
    if "form_email" not in st.session_state:
        st.session_state.form_email = ""
    if "form_prompt" not in st.session_state:
        st.session_state.form_prompt = ""
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""


def _inject_styles() -> None:
    st.markdown("""
        <style>
        html, body, [class*="css"] {
            font-family: "Meiryo", "Yu Gothic UI", "Hiragino Kaku Gothic ProN", sans-serif;
        }
        .app-header {
            border: 1px solid #c9c9c9;
            padding: 16px 12px;
            font-size: 22px;
            font-weight: 700;
            text-align: center;
            margin-bottom: 16px;
        }
        </style>
    """, unsafe_allow_html=True)


def _render_header(title: str) -> None:
    st.markdown(f'<div class="app-header">{title}</div>', unsafe_allow_html=True)


def _render_list(db: Database) -> None:
    _render_header("📋 過去の依頼リスト")
    st.write("完了した依頼一覧です。")
    st.markdown("---")

    requests = logic.list_requests(db)
    if not requests:
        st.info("依頼がありません。")
        return

    header = st.columns([2, 5, 3, 2])
    header[0].markdown("**日付**")
    header[1].markdown("**タイトル**")
    header[2].markdown("**依頼者**")
    header[3].markdown("**詳細**")

    for idx, req in enumerate(requests):
        row = st.columns([2, 5, 3, 2])
        row[0].write(req.date)
        row[1].write(req.title)
        row[2].write(req.requester)
        if row[3].button("開く", key=f"detail_{idx}"):
            st.session_state.selected_index = idx
            st.session_state.page = "detail"
            st.rerun()
        st.divider()


def _render_detail(db: Database) -> None:
    _render_header("📄 依頼詳細")
    requests = logic.list_requests(db)
    index = st.session_state.selected_index

    if index is None or index >= len(requests):
        st.warning("詳細を表示する依頼がありません。")
        if st.button("一覧へ戻る"):
            st.session_state.page = "list"
            st.rerun()
        return

    req = requests[index]
    st.text_input("タイトル", value=req.title, disabled=True)
    st.text_input("依頼者", value=req.requester, disabled=True)
    st.text_area("調査したい内容", value=req.topic, height=90, disabled=True)
    st.text_area("プロンプト", value=req.prompt, height=90, disabled=True)
    st.text_area("📊 レポート", value=req.report, height=180, disabled=True)

    if st.button("◄ 一覧へ戻る"):
        st.session_state.page = "list"
        st.rerun()


def _render_request(db: Database) -> None:
    _render_header("➕ 新規依頼")
    st.write("ディープリサーチの依頼を入力してください。")
    st.markdown("---")

    st.subheader("📋 基本情報")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("📌 タイトル", key="form_title")
        st.text_input("👤 依頼者名", key="form_requester")
        st.text_input("📅 納期（YYYY/MM/DD）", key="form_deadline")
    
    with col2:
        st.text_input("📧 メールアドレス", key="form_email")

    st.text_area("🔍 調査したい内容", key="form_topic", height=120)

    st.markdown("---")
    st.subheader("🔐 Google AI API キー")
    st.info("💡 このセッション中はこの API キーを使用します。")
    
    api_key_input = st.text_input(
        "🔑 Google AI API キー",
        type="password",
        value=st.session_state.api_key,
        placeholder="AIzaSy... から始まるキーを入力してください",
        help="プロンプト生成と実行の両方で使用します"
    )
    
    if api_key_input:
        st.session_state.api_key = api_key_input

    st.markdown("---")
    st.subheader("📝 プロンプト生成")

    if st.button("🤖 AI でプロンプトを生成", use_container_width=True):
        if not st.session_state.form_title:
            st.error("❌ タイトルを入力してください。")
        elif not st.session_state.form_topic:
            st.error("❌ 調査したい内容を入力してください。")
        elif not st.session_state.api_key:
            st.error("❌ API キーを入力してください。")
        else:
            with st.spinner("💭 Gemini でプロンプトを生成中..."):
                st.session_state.form_prompt = logic.create_prompt(
                    st.session_state.form_title,
                    st.session_state.form_deadline,
                    st.session_state.form_topic,
                    st.session_state.api_key
                )
                st.success("✅ プロンプトを生成しました")

    st.text_area("💬 ディープリサーチ用プロンプト", key="form_prompt", height=160)

    st.markdown("---")
    
    if st.button("🚀 実行", type="primary", use_container_width=True):
        if not st.session_state.form_title:
            st.error("❌ タイトルを入力してください。")
        elif not st.session_state.form_topic:
            st.error("❌ 調査したい内容を入力してください。")
        elif not st.session_state.form_prompt:
            st.error("❌ プロンプトを生成してください。")
        elif not st.session_state.api_key:
            st.error("❌ API キーを入力してください。")
        else:
            with st.spinner("🔍 Gemini API でディープリサーチを実行中...\n\nしばらくお待ちください..."):
                try:
                    request, success, report = logic.submit_request(
                        db=db,
                        title=st.session_state.form_title,
                        requester=st.session_state.form_requester,
                        deadline=st.session_state.form_deadline,
                        topic=st.session_state.form_topic,
                        email=st.session_state.form_email,
                        prompt=st.session_state.form_prompt,
                        api_key=st.session_state.api_key,
                    )
                    
                    if success:
                        st.session_state.page = "complete"
                        st.rerun()
                    else:
                        st.error(f"❌ エラー: {report}")
                except Exception as e:
                    st.error(f"❌ エラー: {str(e)}")


def _render_complete() -> None:
    _render_header("✅ 完了")
    st.success("送信が完了しました！")
    
    requests = st.session_state.db.list_requests()
    if requests:
        latest = requests[0]
        st.subheader("📋 リサーチ結果")
        st.text_area("レポート", value=latest.report, height=300, disabled=True)
    
    if st.button("✓ 完了"):
        st.session_state.page = "list"
        st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="ディープリサーチ管理システム",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    _init_state()
    _inject_styles()

    with st.sidebar:
        st.markdown("## 🔍 AI Deep Research Desk")
        st.caption("制作チーム：WA・NAO・SA（ワナオサ）")
        st.markdown("---")
        st.markdown("# 📑 メニュー")
        st.markdown("---")
        
        if st.button("📋 過去の依頼リスト", use_container_width=True, key="menu_list"):
            st.session_state.page = "list"
            st.rerun()
        
        if st.button("➕ 新規依頼", use_container_width=True, key="menu_request"):
            st.session_state.page = "request"
            st.rerun()

    page = st.session_state.page
    db = st.session_state.db
    
    if page == "list":
        _render_list(db)
    elif page == "detail":
        _render_detail(db)
    elif page == "request":
        _render_request(db)
    elif page == "complete":
        _render_complete()


if __name__ == "__main__":
    main()