# AI活用度セルフチェック＆RAG技術デモ

DX推進担当・情シス向けのPoCツール2本セット。

## ファイル構成

```
ai-readiness-check/
├── ai_readiness_check.py    # セルフチェックツール
├── check_questions.json     # チェック項目データ（外出し）
├── rag_demo.py              # RAG技術デモツール
├── demo_data_ideal.json     # 理想データ（整備済み）
├── demo_data_real.json      # 現実データ（未整備）
├── requirements.txt         # パッケージ一覧
└── README.md
```

## セットアップ

```powershell
mkdir C:\dev\ai-readiness-check
cd C:\dev\ai-readiness-check
# 全ファイルを配置

python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

※ sentence-transformers + PyTorch の初回インストールは時間がかかる（数分）。
※ 64bit Python 必須。Visual C++ ランタイムも必要（前回インストール済みなら不要）。

## 起動

```powershell
# セルフチェック
streamlit run ai_readiness_check.py

# RAGデモ
streamlit run rag_demo.py
```

## セルフチェックツール

- 20問（5カテゴリ×4問）に回答 → レーダーチャート＋レベル判定
- 各回答にコメント入力欄あり
- モデル選択: AIなし / Haiku / Sonnet
- AIなし → 定型の改善提案
- AI ON → Claude が回答内容を読んで個別の改善提案を生成
- コスト概算（ライセンス型 vs 従量型、稼働率の注意喚起）

## RAG技術デモ

4つの検索技術をON/OFFして精度の違いを実演：
- 🔀 ハイブリッド検索（ベクトル＋キーワード）→ 型番・固有名詞に強い
- 🔗 親子チャンク → 文脈を保持したまま精度向上
- 💡 HyDE → 仮回答で検索精度UP（API必要）
- 🏷️ メタデータフィルタ → 部署・文書種別で絞り込み

追加機能:
- 理想データ / 現実データの切替
- 速度・コストの見える化
- モデル選択: AIなし / Haiku / Sonnet
- 検索ごとのコメント記録

## APIキー

環境変数に設定済みなら自動で読み込む:
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```
