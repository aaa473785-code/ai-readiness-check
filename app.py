"""
AI活用度セルフチェック＆RAG技術デモ
トップページ
"""
import streamlit as st

st.set_page_config(page_title="AI活用ツール", page_icon="🔍", layout="wide")

st.title("🔍 AI活用ツール")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 AI活用度セルフチェック")
    st.markdown(
        "自社のAI活用レベルを20問で診断。\n\n"
        "レーダーチャート＋改善提案＋コスト概算を出します。\n\n"
        "**対象：** DX推進担当・情シス"
    )
    st.page_link("pages/1_セルフチェック.py", label="→ セルフチェックを開く", icon="📋")

with col2:
    st.markdown("### 🔬 RAG技術デモ")
    st.markdown(
        "4つの検索技術をON/OFFして精度の違いを実演。\n\n"
        "理想データ vs 現実データの切替つき。\n\n"
        "**機能：** ハイブリッド検索 / 親子チャンク / HyDE / メタデータフィルタ"
    )
    st.page_link("pages/2_RAGデモ.py", label="→ RAGデモを開く", icon="🔬")

st.markdown("---")
st.caption("※ PoCデモです。左のサイドバーからもページを切り替えられます。")
