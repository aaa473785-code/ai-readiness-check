"""
AI活用度セルフチェックツール v2
- チェック項目はJSON外出し（check_questions.json）
- 各回答にコメント入力欄あり
- モデル選択：Haiku / Sonnet / AIなし（3択）
- コスト計算つき
"""
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import json, os, time

matplotlib.rcParams["font.family"] = ["Noto Sans CJK JP","IPAexGothic","Hiragino Sans","Yu Gothic","Meiryo","sans-serif"]

CHOICES = {0:"該当しない", 1:"一部該当する", 2:"概ね該当する", 3:"完全に該当する"}

COST_ITEMS = {
    "copilot":      {"name":"Microsoft 365 Copilot",    "monthly":4497, "desc":"生成AI支援（Word/Excel/Teams等）"},
    "chatgpt_team": {"name":"ChatGPT Team",             "monthly":3750, "desc":"汎用チャットAI（チーム利用）"},
    "claude_pro":   {"name":"Claude Pro",               "monthly":2800, "desc":"汎用チャットAI（個人利用）"},
    "api_haiku":    {"name":"API Haiku 従量",            "monthly":200,  "desc":"RAG等（月3,000回想定）"},
    "api_sonnet":   {"name":"API Sonnet 従量",           "monthly":1500, "desc":"高精度用途（月1,000回想定）"},
}

# ---------- データ読み込み ----------
@st.cache_data
def load_questions(path="check_questions.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# ---------- スコア計算 ----------
def calc_scores(categories, answers):
    cat_scores = {}
    for cat in categories:
        tw = sum(q["weight"] for q in cat["questions"])
        ws = sum(answers.get(q["id"],0)*q["weight"] for q in cat["questions"])
        cat_scores[cat["name"]] = round((ws/(tw*3))*100) if tw else 0
    return {"categories": cat_scores, "overall": round(sum(cat_scores.values())/len(cat_scores))}

def get_level(score):
    if score>=80: return "A（先進）","AI活用が組織に定着。次は高度化・横展開。","#16A34A"
    if score>=60: return "B（推進中）","取り組みは進行中。定着に課題あり。種火の活用と効果測定がカギ。","#2563EB"
    if score>=40: return "C（着手）","AI着手済みだが基盤・体制に不足。データ整備と小さな成功体験を優先。","#CA8A04"
    return "D（未着手）","AI活用はこれから。方針策定とデータ棚卸しから。焦って大規模導入は不要。","#DC2626"

# ---------- 定型レコメンド ----------
def static_recs(scores, answers):
    cs = scores["categories"]
    worst = min(cs, key=cs.get)
    best  = max(cs, key=cs.get)
    recs = [f"**最も改善余地が大きい領域：{worst}（{cs[worst]}点）**"]
    tips = {
        "データ基盤":  "📌 データ基盤が弱い状態でAIを入れると「使えない」評価に。工数の6〜7割はデータ整備。まず社内文書の棚卸しから。",
        "人材・体制":  "📌 種火がいない or 試せない環境。全社一斉より種火を見つけて小さく始めるほうが定着率が高い。",
        "ツール活用":  "📌 ツールの利用率が不明＝ライセンスコストが無駄の可能性。まず利用実態の可視化から。",
        "運用・定着":  "📌 効果測定なし＝継続・縮小・拡大の判断不能。KPI設定＋月次の利用率確認サイクルを。",
        "戦略・方針":  "📌 経営層の方針なしで現場だけ動くと予算・展開で詰まる。小さなPoCで数字を出し経営層を動かす。",
    }
    for k,v in tips.items():
        if cs.get(k,0)<50: recs.append(v)
    recs.append(f"✅ **強みの領域：{best}（{cs[best]}点）** — ここを起点に横展開が効率的。")
    return recs

# ---------- AI分析 ----------
def ai_recs(scores, answers, categories, api_key, model_id):
    import anthropic
    txt = ""
    for cat in categories:
        txt += f"\n【{cat['name']}】（{scores['categories'][cat['name']]}点）\n"
        for q in cat["questions"]:
            v = answers.get(q["id"],0)
            c = answers.get(f"{q['id']}_comment","")
            txt += f"  - {q['text']}: {CHOICES[v]}"
            if c: txt += f"（補足: {c}）"
            txt += "\n"
    level,_,_ = get_level(scores["overall"])
    prompt = f"""以下は企業のAI活用度チェック結果です。DX推進担当・情シス向けに具体的な改善提案を3〜5個出してください。
【総合】{scores['overall']}点（{level}）
{txt}
ルール: 各提案は「何を」「なぜ」「どう始めるか」の3点。来週から始められる具体策。スコアが低い領域優先。500文字以内。"""
    client = anthropic.Anthropic(api_key=api_key)
    t0 = time.time()
    msg = client.messages.create(
        model=model_id, max_tokens=800,
        system="あなたはAI導入コンサルタントです。実務的で具体的な改善提案を行います。",
        messages=[{"role":"user","content":prompt}],
    )
    elapsed = time.time()-t0
    text = msg.content[0].text
    inp = msg.usage.input_tokens
    out = msg.usage.output_tokens
    return text, inp, out, elapsed

# ---------- レーダーチャート ----------
def draw_radar(cs):
    labels = list(cs.keys())
    vals = list(cs.values()) + [list(cs.values())[0]]
    angles = np.linspace(0,2*np.pi,len(labels),endpoint=False).tolist() + [0]
    fig,ax = plt.subplots(figsize=(5,5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("white"); ax.set_facecolor("white")
    ax.set_ylim(0,100); ax.set_yticks([20,40,60,80,100])
    ax.set_yticklabels(["20","40","60","80","100"], fontsize=8, color="#94A3B8")
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(labels, fontsize=10, color="#334155")
    ax.fill(angles, vals, alpha=0.15, color="#2563EB")
    ax.plot(angles, vals, linewidth=2, color="#2563EB", marker="o", markersize=6)
    for a,v in zip(angles[:-1], vals[:-1]):
        ax.annotate(f"{v}", xy=(a,v), xytext=(0,12), textcoords="offset points", ha="center", fontsize=11, fontweight="bold", color="#1E293B")
    ax.grid(color="#E2E8F0", linewidth=0.5)
    plt.tight_layout()
    return fig

# ---------- コスト計算ヘルパー ----------
def api_cost_jpy(inp, out, model):
    rates = {"haiku":{"i":1.0,"o":5.0}, "sonnet":{"i":3.0,"o":15.0}}
    r = rates.get(model, rates["haiku"])
    usd = (inp/1e6)*r["i"] + (out/1e6)*r["o"]
    return round(usd*150, 2)

# ============================================
# メイン
# ============================================
def main():
    st.set_page_config(page_title="AI活用度セルフチェック", page_icon="🔍", layout="wide")
    st.markdown("""<style>
    .stRadio > div { flex-direction:row; gap:8px; flex-wrap:wrap; }
    .stRadio > div > label { background:#F1F5F9; border-radius:8px; padding:6px 14px; border:1px solid #E2E8F0; }
    </style>""", unsafe_allow_html=True)

    data = load_questions()
    categories = data["categories"]

    st.title("🔍 AI活用度セルフチェックツール")
    st.caption("DX推進担当・情シス向け｜自社のAI活用レベルを診断し、改善提案とコスト概算を出します")

    # ---- サイドバー ----
    with st.sidebar:
        st.header("⚙️ 設定")
        model_choice = st.radio("分析モデル", ["AIなし","Haiku（低コスト）","Sonnet（高精度）"], index=0)
        model_map = {"AIなし":None, "Haiku（低コスト）":"claude-haiku-4-5-20251001", "Sonnet（高精度）":"claude-sonnet-4-6"}
        model_id = model_map[model_choice]

        api_key = ""
        if model_id:
            api_key = os.environ.get("ANTHROPIC_API_KEY","")
            if not api_key:
                api_key = st.text_input("Anthropic APIキー", type="password")
            if api_key: st.success(f"APIキー設定済み ✓（{model_choice}）")
            else: st.warning("APIキーを入力してください")

        st.divider()
        st.header("💰 コスト試算の前提")
        num_users = st.number_input("対象人数", min_value=10, max_value=10000, value=100, step=10)

    # ---- チェック項目 ----
    st.markdown("---")
    st.subheader("📋 チェック項目（20問）")
    st.caption("各項目について自社の状況に最も近いものを選び、必要に応じてコメントを追記してください。")

    answers = {}
    for cat in categories:
        st.markdown(f"### {cat['name']}")
        st.caption(cat["description"])
        for q in cat["questions"]:
            val = st.radio(q["text"], options=[0,1,2,3], format_func=lambda x:CHOICES[x], horizontal=True, key=q["id"])
            answers[q["id"]] = val
            comment = st.text_input("補足コメント（任意）", key=f"{q['id']}_comment", label_visibility="collapsed", placeholder="補足があればここに入力...")
            if comment: answers[f"{q['id']}_comment"] = comment
        st.markdown("")

    # ---- 診断 ----
    st.markdown("---")
    if st.button("🔍 診断する", type="primary", use_container_width=True):
        scores = calc_scores(categories, answers)
        st.session_state["scores"] = scores
        st.session_state["answers"] = answers
        st.session_state["diagnosed"] = True

    # ---- 結果 ----
    if st.session_state.get("diagnosed"):
        scores = st.session_state["scores"]
        answers = st.session_state["answers"]
        level, level_desc, _ = get_level(scores["overall"])

        st.markdown("---")
        st.subheader("📊 診断結果")
        c1,c2,c3 = st.columns(3)
        c1.metric("総合スコア", f"{scores['overall']}点")
        c2.metric("レベル", level)
        c3.metric("分析モード", model_choice)
        st.info(level_desc)

        col_c, col_d = st.columns([1,1])
        with col_c:
            fig = draw_radar(scores["categories"])
            st.pyplot(fig); plt.close()
        with col_d:
            st.markdown("#### カテゴリ別スコア")
            for cn, sc in scores["categories"].items():
                st.markdown(f"**{cn}** — {sc}点")
                st.progress(sc/100)

        # ---- 改善提案 ----
        st.markdown("---")
        st.subheader("💡 改善提案")

        if model_id and api_key:
            with st.spinner(f"{model_choice}で分析中..."):
                try:
                    text, inp, out, elapsed = ai_recs(scores, answers, categories, api_key, model_id)
                    st.markdown(text)
                    m = "haiku" if "haiku" in model_id else "sonnet"
                    cost = api_cost_jpy(inp, out, m)
                    st.caption(f"📎 API費用: 約{cost}円（入力{inp} + 出力{out}トークン, {model_choice}, {elapsed:.1f}秒）")
                except Exception as e:
                    st.error(f"APIエラー: {e}")
                    for r in static_recs(scores, answers): st.markdown(r)
        else:
            for r in static_recs(scores, answers): st.markdown(r)
            st.caption("💡 サイドバーでモデルを選ぶと、回答内容に基づく個別の改善提案が生成されます。")

        # ---- コスト試算 ----
        st.markdown("---")
        st.subheader("💰 AI導入コスト概算")
        st.caption(f"対象人数: {num_users}人")
        ca, cb = st.columns(2)
        with ca:
            st.markdown("#### ライセンス型")
            for k in ["copilot","chatgpt_team","claude_pro"]:
                it = COST_ITEMS[k]; m = it["monthly"]*num_users
                st.markdown(f"**{it['name']}**　¥{it['monthly']:,}/人/月　→　月額 **¥{m:,}**（年 ¥{m*12:,}）  \n{it['desc']}")
                st.markdown("")
        with cb:
            st.markdown("#### 従量課金型")
            for k in ["api_haiku","api_sonnet"]:
                it = COST_ITEMS[k]; m = it["monthly"]*num_users
                st.markdown(f"**{it['name']}**　目安 ¥{it['monthly']:,}/人/月　→　月額 **¥{m:,}**（年 ¥{m*12:,}）  \n{it['desc']}")
                st.markdown("")
        cop = COST_ITEMS["copilot"]["monthly"]*num_users
        st.markdown(f"**💡 稼働率に注意：** 稼働率40%なら月額の60%（最大 ¥{int(cop*0.6):,}/月）が未使用コスト。導入後の利用率モニタリング必須。")
        st.markdown("---")
        st.caption("※ PoCです。実際の導入判断には個別要件分析が必要です。料金は2026年6月時点の概算。")

if __name__=="__main__":
    main()
