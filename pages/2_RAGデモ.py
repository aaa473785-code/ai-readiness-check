"""
RAG技術デモツール
4大トグル（ハイブリッド/親子チャンク/HyDE/メタデータフィルタ）のON/OFF切替で
検索精度の違いを実演する。理想データ/現実データの切替つき。
"""
import streamlit as st
import numpy as np
import json, os, time, re
from collections import Counter

# ============================================
# Embedding（ローカル / sentence-transformers）
# ============================================
@st.cache_resource
def load_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def embed(texts, embedder):
    return embedder.encode(texts, normalize_embeddings=True)

def cosine_sim(a, b):
    return np.dot(a, b.T)

# ============================================
# キーワード検索（ハイブリッド用・簡易BM25風）
# ============================================
def keyword_score(query, text):
    q_tokens = set(re.findall(r'\w+', query.lower()))
    t_tokens = re.findall(r'\w+', text.lower())
    t_counter = Counter(t_tokens)
    total = len(t_tokens) if t_tokens else 1
    score = sum(t_counter.get(qt, 0) / total for qt in q_tokens)
    # 型番の完全一致ボーナス
    for qt in q_tokens:
        if qt.upper() in text.upper() and any(c.isdigit() for c in qt):
            score += 0.5
    return score

# ============================================
# データ読み込み・チャンク化
# ============================================
@st.cache_data
def load_data(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def make_chunks(documents, use_parent_child=False):
    """通常チャンク or 親子チャンク"""
    chunks = []
    for doc in documents:
        if use_parent_child:
            # 親 = 文書全体、子 = 文単位で分割
            sentences = re.split(r'(?<=[。．.！？])', doc["content"])
            sentences = [s.strip() for s in sentences if s.strip()]
            for i, sent in enumerate(sentences):
                chunks.append({
                    "text": sent,
                    "parent_text": doc["content"],  # 親を保持
                    "title": doc["title"],
                    "doc_id": doc["id"],
                    "metadata": doc.get("metadata", {}),
                    "is_child": True,
                })
        else:
            chunks.append({
                "text": doc["content"],
                "parent_text": doc["content"],
                "title": doc["title"],
                "doc_id": doc["id"],
                "metadata": doc.get("metadata", {}),
                "is_child": False,
            })
    return chunks

# ============================================
# メタデータフィルタ
# ============================================
def apply_metadata_filter(chunks, filters):
    if not filters:
        return chunks
    filtered = []
    for c in chunks:
        meta = c.get("metadata", {})
        match = True
        for key, val in filters.items():
            if val and meta.get(key) and val.lower() not in str(meta.get(key, "")).lower():
                match = False
                break
        if match:
            filtered.append(c)
    return filtered if filtered else chunks  # フィルタで0件なら全件返す

# ============================================
# HyDE（仮回答生成 → それで検索）
# ============================================
def generate_hyde(query, api_key, model_id):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    t0 = time.time()
    msg = client.messages.create(
        model=model_id, max_tokens=200,
        system="社内文書に書かれていそうな回答を1段落で書いてください。事実でなくて構いません。",
        messages=[{"role": "user", "content": f"質問: {query}"}],
    )
    elapsed = time.time() - t0
    text = msg.content[0].text
    inp, out = msg.usage.input_tokens, msg.usage.output_tokens
    return text, inp, out, elapsed

# ============================================
# 回答生成
# ============================================
def generate_answer(query, context, api_key, model_id):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    t0 = time.time()
    msg = client.messages.create(
        model=model_id, max_tokens=500,
        system="あなたは社内文書に基づいて回答するアシスタントです。提供された文書の情報のみで回答してください。情報がない場合は「この文書には該当する情報がありません」と答えてください。回答の末尾に、参照した文書のタイトルを【出典】として必ず明記してください。",
        messages=[{"role": "user", "content": f"【参考文書】\n{context}\n\n【質問】\n{query}"}],
    )
    elapsed = time.time() - t0
    text = msg.content[0].text
    inp, out = msg.usage.input_tokens, msg.usage.output_tokens
    return text, inp, out, elapsed

# ============================================
# コスト計算
# ============================================
def calc_cost(inp, out, model):
    rates = {"haiku": {"i": 1.0, "o": 5.0}, "sonnet": {"i": 3.0, "o": 15.0}}
    r = rates.get(model, rates["haiku"])
    usd = (inp / 1e6) * r["i"] + (out / 1e6) * r["o"]
    return round(usd * 150, 4)

# ============================================
# メイン
# ============================================
def main():
    st.set_page_config(page_title="RAG技術デモ", page_icon="🔬", layout="wide")
    st.title("🔬 RAG技術デモツール")
    st.caption("4つの検索技術をON/OFFして精度の違いを実演｜理想データ vs 現実データの切替つき")

    # ---- サイドバー ----
    with st.sidebar:
        st.header("⚙️ 設定")

        # モデル選択
        model_choice = st.radio("回答生成モデル", ["AIなし（検索のみ）", "Haiku（低コスト）", "Sonnet（高精度）"], index=0)
        model_map = {"AIなし（検索のみ）": None, "Haiku（低コスト）": "claude-haiku-4-5-20251001", "Sonnet（高精度）": "claude-sonnet-4-6"}
        model_id = model_map[model_choice]
        model_short = "haiku" if model_id and "haiku" in model_id else "sonnet"

        api_key = ""
        if model_id:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                api_key = st.text_input("Anthropic APIキー", type="password")
            if api_key:
                st.success(f"API設定済み ✓")

        st.divider()

        # データ切替
        st.header("📂 データ選択")
        data_mode = st.radio("データセット", ["理想データ（整備済み）", "現実データ（未整備）"], index=0)
        data_path = "demo_data_ideal.json" if "理想" in data_mode else "demo_data_real.json"

        st.divider()

        # 4大トグル
        st.header("🔧 検索技術トグル")
        use_hybrid = st.toggle("🔀 ハイブリッド検索", value=False, help="ベクトル検索＋キーワード検索。型番・固有名詞に強い")
        use_parent_child = st.toggle("🔗 親子チャンク", value=False, help="文単位で検索→文書単位で回答。文脈が切れない")
        use_hyde = st.toggle("💡 HyDE（仮回答検索）", value=False, help="質問→仮回答を生成→仮回答で検索。API必要")
        use_metadata = st.toggle("🏷️ メタデータフィルタ", value=False, help="部署・文書種別で絞り込み")

        if use_hyde and not (model_id and api_key):
            st.warning("HyDEにはAPIが必要です")

        # メタデータフィルタ条件
        meta_filters = {}
        if use_metadata:
            st.markdown("##### フィルタ条件")
            meta_filters["department"] = st.text_input("部署名（部分一致）", placeholder="例: 品質管理")
            meta_filters["doc_type"] = st.selectbox("文書種別", ["（指定なし）", "手順書", "マニュアル", "FAQ", "規程"])
            if meta_filters["doc_type"] == "（指定なし）":
                meta_filters["doc_type"] = ""
            meta_filters = {k: v for k, v in meta_filters.items() if v}

        st.divider()
        st.header("📊 検索パラメータ")
        top_k = st.slider("検索件数（top_k）", 1, 10, 3)
        threshold = st.slider("スコア閾値", 0.0, 1.0, 0.2, 0.05)
        if use_hybrid:
            hybrid_alpha = st.slider("ハイブリッド比率（ベクトル:キーワード）", 0.0, 1.0, 0.7, 0.05, help="1.0=ベクトルのみ / 0.0=キーワードのみ")

    # ---- データ読み込み ----
    try:
        data = load_data(data_path)
    except FileNotFoundError:
        st.error(f"データファイルが見つかりません: {data_path}")
        return

    documents = data["documents"]
    st.info(f"📂 **{data['title']}** — {data['description']}（{len(documents)}件）")

    # ---- チャンク化 ----
    chunks = make_chunks(documents, use_parent_child)

    # ---- Embedding ----
    embedder = load_embedder()
    chunk_texts = [c["text"] for c in chunks]

    with st.spinner("Embedding生成中..."):
        t0 = time.time()
        chunk_vecs = embed(chunk_texts, embedder)
        embed_time = time.time() - t0

    # ---- 検索入力 ----
    st.markdown("---")
    st.subheader("🔍 検索")

    sample_queries = [
        "ABC-1234の外観検査の基準は？",
        "プレス機の油圧の正常値は？",
        "CNCでE-07エラーが出たらどうする？",
        "VPNに接続できない",
        "有機溶剤を使うときの保護具は？",
        "50万円の発注に必要な承認は？",
    ]
    selected_q = st.selectbox("サンプル質問", ["（自由入力）"] + sample_queries)
    query = st.text_input("質問を入力", value="" if selected_q == "（自由入力）" else selected_q)

    if not query:
        st.caption("質問を入力するか、サンプルを選んでください。")
        return

    # 入力長チェック（プロンプトインジェクション対策）
    if len(query) > 500:
        st.error("質問は500文字以内にしてください。")
        return

    if st.button("🔍 検索実行", type="primary", use_container_width=True):

        total_cost_inp, total_cost_out = 0, 0
        timings = {}

        # ---- メタデータフィルタ ----
        search_chunks = chunks
        search_vecs = chunk_vecs
        if use_metadata and meta_filters:
            filtered_idx = []
            for i, c in enumerate(chunks):
                meta = c.get("metadata", {})
                match = True
                for key, val in meta_filters.items():
                    if val and (not meta.get(key) or val.lower() not in str(meta[key]).lower()):
                        match = False; break
                if match:
                    filtered_idx.append(i)
            if filtered_idx:
                search_chunks = [chunks[i] for i in filtered_idx]
                search_vecs = chunk_vecs[filtered_idx]
                st.caption(f"🏷️ メタデータフィルタ: {len(chunks)}件 → {len(search_chunks)}件に絞り込み")
            else:
                st.warning("フィルタ条件に一致する文書がないため、全件で検索します")

        # ---- HyDE ----
        hyde_text = None
        if use_hyde and model_id and api_key:
            with st.spinner("HyDE: 仮回答を生成中..."):
                hyde_text, h_inp, h_out, h_time = generate_hyde(query, api_key, model_id)
                total_cost_inp += h_inp; total_cost_out += h_out
                timings["HyDE生成"] = h_time

        # ---- ベクトル検索 ----
        t0 = time.time()
        search_query = hyde_text if hyde_text else query
        query_vec = embed([search_query], embedder)[0]
        vec_scores = cosine_sim(query_vec, search_vecs).flatten()
        timings["ベクトル検索"] = time.time() - t0

        # ---- ハイブリッド検索 ----
        if use_hybrid:
            t0 = time.time()
            kw_scores = np.array([keyword_score(query, c["text"]) for c in search_chunks])
            # 正規化
            if kw_scores.max() > 0:
                kw_scores = kw_scores / kw_scores.max()
            alpha = hybrid_alpha if 'hybrid_alpha' in dir() else 0.7
            try:
                alpha = hybrid_alpha
            except:
                alpha = 0.7
            combined = alpha * vec_scores + (1 - alpha) * kw_scores
            timings["キーワード検索"] = time.time() - t0
        else:
            combined = vec_scores

        # ---- 結果取得 ----
        top_indices = np.argsort(combined)[::-1][:top_k]
        results = []
        for idx in top_indices:
            sc = float(combined[idx])
            if sc >= threshold:
                c = search_chunks[idx]
                results.append({
                    "score": sc,
                    "vec_score": float(vec_scores[idx]),
                    "kw_score": float(kw_scores[idx]) if use_hybrid else 0,
                    "text": c["parent_text"] if use_parent_child else c["text"],
                    "search_text": c["text"],
                    "title": c["title"],
                    "doc_id": c["doc_id"],
                    "metadata": c["metadata"],
                    "is_child": c.get("is_child", False),
                })

        # ---- 検索結果表示 ----
        st.markdown("---")
        st.subheader("📄 検索結果")

        if not results:
            st.warning(f"スコア閾値（{threshold}）を超える結果がありません。閾値を下げるか、質問を変えてみてください。")
        else:
            for i, r in enumerate(results):
                with st.expander(f"**{i+1}. {r['title']}**（スコア: {r['score']:.3f}）", expanded=(i == 0)):
                    # スコア詳細
                    score_cols = st.columns(3 if use_hybrid else 2)
                    score_cols[0].metric("総合スコア", f"{r['score']:.3f}")
                    score_cols[1].metric("ベクトル類似度", f"{r['vec_score']:.3f}")
                    if use_hybrid:
                        score_cols[2].metric("キーワードスコア", f"{r['kw_score']:.3f}")

                    # 親子チャンクの場合、検索にヒットした文を強調
                    if use_parent_child and r["is_child"]:
                        st.caption("🔗 親子チャンク: 文単位で検索 → 文書全体を表示")
                        highlighted = r["text"].replace(r["search_text"], f"**🔍 {r['search_text']}**")
                        st.markdown(highlighted)
                    else:
                        st.markdown(r["text"])

                    # メタデータ
                    meta = r["metadata"]
                    meta_str = " / ".join(f"{k}: {v}" for k, v in meta.items() if v)
                    if meta_str:
                        st.caption(f"🏷️ {meta_str}")
                    else:
                        st.caption("🏷️ メタデータなし")

        # ---- HyDE表示 ----
        if hyde_text:
            with st.expander("💡 HyDE: 生成された仮回答（これで検索した）"):
                st.markdown(hyde_text)

        # ---- AI回答生成 ----
        if model_id and api_key and results:
            st.markdown("---")
            st.subheader("🤖 AI回答")
            context = "\n\n".join(f"【{r['title']}】\n{r['text']}" for r in results[:3])
            with st.spinner(f"{model_choice}で回答生成中..."):
                answer, a_inp, a_out, a_time = generate_answer(query, context, api_key, model_id)
                total_cost_inp += a_inp; total_cost_out += a_out
                timings["回答生成"] = a_time
            st.markdown(answer)

            # 参照文書一覧（出典明示）
            st.markdown("##### 📎 参照文書")
            for j, r in enumerate(results[:3]):
                meta = r["metadata"]
                ver = f"v{meta.get('version','?')}" if meta.get("version") else "版不明"
                dept = meta.get("department","部署不明")
                st.caption(f"{j+1}. {r['title']}（{dept} / {ver} / スコア: {r['score']:.3f}）")

        # ---- 速度・コスト表示 ----
        st.markdown("---")
        st.subheader("⏱️ 速度とコスト")

        t_cols = st.columns(2)
        with t_cols[0]:
            st.markdown("#### 処理時間")
            timings["Embedding（初回キャッシュ後0）"] = embed_time
            for label, t in timings.items():
                st.markdown(f"- {label}: **{t:.3f}秒**")
            total_time = sum(timings.values())
            st.markdown(f"- **合計: {total_time:.3f}秒**")

        with t_cols[1]:
            st.markdown("#### APIコスト（この1回の検索）")
            if total_cost_inp > 0 or total_cost_out > 0:
                cost = calc_cost(total_cost_inp, total_cost_out, model_short)
                st.markdown(f"- 入力: {total_cost_inp} トークン")
                st.markdown(f"- 出力: {total_cost_out} トークン")
                st.markdown(f"- **費用: 約 {cost} 円**（{model_choice}）")

                # 月間試算
                st.markdown("##### 月間試算")
                for vol in [100, 1000, 3000]:
                    monthly = round(cost * vol, 1)
                    st.markdown(f"- 月{vol}回: **約 ¥{monthly:,.1f}**")
            else:
                st.markdown("APIなし（ローカル処理のみ）→ **¥0**")
                st.caption("Embedding・ベクトル検索・キーワード検索はすべてローカル実行。API費用ゼロ。")

        # ---- 有効なトグルのまとめ ----
        st.markdown("---")
        st.subheader("🔧 現在の設定")
        toggles = {
            "ハイブリッド検索": use_hybrid,
            "親子チャンク": use_parent_child,
            "HyDE": use_hyde,
            "メタデータフィルタ": use_metadata,
        }
        tc = st.columns(4)
        for i, (name, on) in enumerate(toggles.items()):
            tc[i].markdown(f"**{name}**")
            tc[i].markdown(f"{'🟢 ON' if on else '⚪ OFF'}")

        st.markdown(f"**データ:** {data_mode}　**モデル:** {model_choice}　**top_k:** {top_k}　**閾値:** {threshold}")

        # コメント入力欄
        st.markdown("---")
        st.subheader("📝 コメント")
        comment = st.text_area("この検索結果についてのメモ・気づき", placeholder="例: ハイブリッドONで型番がヒットするようになった")
        if comment:
            st.success("コメントを記録しました（セッション内）")
            if "comments" not in st.session_state:
                st.session_state["comments"] = []
            st.session_state["comments"].append({
                "query": query,
                "toggles": {k: v for k, v in toggles.items()},
                "data": data_mode,
                "model": model_choice,
                "comment": comment,
            })

        # 過去のコメント
        if st.session_state.get("comments"):
            with st.expander(f"📋 過去のコメント（{len(st.session_state['comments'])}件）"):
                for c in reversed(st.session_state["comments"]):
                    on_list = [k for k, v in c["toggles"].items() if v]
                    st.markdown(f"**Q:** {c['query']}　[{', '.join(on_list) if on_list else '全OFF'}]　{c['data']}　{c['model']}")
                    st.markdown(f"→ {c['comment']}")
                    st.markdown("---")

    # ---- フッター ----
    st.markdown("---")
    st.caption("※ PoCデモです。Embeddingはローカル実行（MiniLM）。データはダミーです。")

if __name__ == "__main__":
    main()
