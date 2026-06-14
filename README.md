# AI活用度セルフチェック＆RAG技術デモ

DX推進担当・情シス向けの **PoCツール2本セット** です。  
Streamlit のマルチページ構成で、以下の2つのデモを実行できます。

1. AI活用度セルフチェック
2. RAG技術デモ

---

## 概要

### 1. AI活用度セルフチェック

自社のAI活用状況を20問で診断し、カテゴリ別スコア、総合レベル、改善提案、コスト概算を表示します。

主な機能:

- 20問のチェック項目に回答
- 5カテゴリ別のスコア算出
- レーダーチャート表示
- 総合レベル判定
- 各回答へのコメント入力
- AIなし / Haiku / Sonnet のモデル選択
- AIなしの場合は定型の改善提案を表示
- AI ON の場合は Claude が回答内容を読んで個別の改善提案を生成
- ライセンス型 / 従量型のコスト概算
- 稼働率による未使用コストの注意喚起

### 2. RAG技術デモ

4つの検索技術をON/OFFしながら、検索精度の違いを比較できるデモです。

比較できる技術:

- ハイブリッド検索  
  ベクトル検索とキーワード検索を組み合わせます。型番や固有名詞に強い検索を確認できます。

- 親子チャンク  
  文単位で検索し、回答時には文書全体の文脈を保持します。

- HyDE  
  質問から仮回答を生成し、その仮回答を使って検索します。APIキーが必要です。

- メタデータフィルタ  
  部署や文書種別で検索対象を絞り込みます。

追加機能:

- 理想データ / 現実データの切替
- 速度とコストの見える化
- AIなし / Haiku / Sonnet のモデル選択
- 検索ごとのコメント記録

---

## ファイル構成

```text
ai-readiness-check/
├── app.py                         # トップページ（ツール選択）
├── pages/
│   ├── 1_セルフチェック.py          # AI活用度セルフチェック
│   └── 2_RAGデモ.py                # RAG技術デモ
├── check_questions.json           # チェック項目データ
├── demo_data_ideal.json           # 理想データ（整備済み）
├── demo_data_real.json            # 現実データ（未整備）
├── requirements.txt               # Pythonパッケージ一覧
└── README.md
```

---

## セットアップ

Windows PowerShell で実行する例です。

```powershell
git clone https://github.com/aaa473785-code/ai-readiness-check.git
cd ai-readiness-check

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

`sentence-transformers` と `torch` の初回インストールには数分かかる場合があります。  
64bit Python の利用を推奨します。環境によっては Visual C++ ランタイムが必要になることがあります。

---

## 起動方法

```powershell
streamlit run app.py
```

ブラウザでトップページが開き、2つのツールを選択できます。  
左サイドバーからもページを切り替えられます。

---

## APIキー設定

Claude を使う機能を利用する場合は、Anthropic APIキーを環境変数に設定します。

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

環境変数に設定済みの場合、アプリ側で自動的に読み込みます。  
未設定の場合は、画面上の入力欄からAPIキーを入力できます。

---

## 注意事項

- このリポジトリは PoC デモ用です。
- データはダミーデータです。
- 実際の導入判断には、個別要件、セキュリティ、運用体制、コスト試算の確認が必要です。
- APIを使う機能では、利用量に応じてAPI費用が発生します。
