---
name: streamlit-poc-builder
description: 生成AI/RAG/エージェントのPoCツールをStreamlitで作る時の手順。社内デモ・ポートフォリオ向けのStreamlitマルチページアプリを新規作成または拡張する際、Anthropic APIのモデルID選定・文字化け回避・APIキー管理・コスト表示の定番構成を適用する。「PoCを作りたい」「Streamlitでデモを」「RAGデモ」「セルフチェックツール」等で使う。
---

# Streamlit製PoCツールの作り方

DX推進・情シス向けに、生成AI/RAGのPoCツールをStreamlitで作るときの定番手順。
社内デモやポートフォリオとして見せることを前提に、再現性・正確さ・コスト可視化を重視する。

## 1. 構成の基本：マルチページ

単機能でも、拡張前提でマルチページ構成にする。

```
project-name/
├── app.py                 # トップページ（ツール選択の入口）
├── pages/
│   ├── 1_機能A.py
│   └── 2_機能B.py
├── *.json                 # データは外出し（コードに埋めない）
├── requirements.txt
└── README.md
```

- ページファイルは `pages/` 配下に置くと、Streamlitが自動でサイドバーに並べる。
- ファイル名の先頭の数字（`1_`）が表示順を決める。
- データ（質問項目・デモ文書等）は `.json` に外出しし、コードと分離する。

## 2. モデルIDは現行のものを使う（重要）

Anthropic APIのモデルIDは、必ず現行IDを使う。旧ID（`claude-sonnet-4`, `claude-opus-4` 等の無印）は
APIリタイア後にエラーになる。

- 安価・高速デモ用: `claude-haiku-4-5`
- 高品質が要る時: `claude-sonnet-5`

モデル選択はUIで「AIなし / Haiku / Sonnet」と切り替えられるようにし、
「AIなし」時は定型ロジックで動く設計にすると、API不要でも全体の流れをデモできる。

## 3. APIキーは環境変数から読む（ハードコード禁止）

```python
import os
import anthropic
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
```

- コードにキーを直書きしない。GitHub公開時の事故を防ぐ。
- PowerShellでの設定例: `$env:ANTHROPIC_API_KEY = "sk-ant-..."`

## 4. 日本語ファイルの文字化け回避（Windows）

- PowerShellの `Set-Content` / `Out-File` は日本語UTF-8を壊すことがある。
  ファイル中身の書き込みにこれらを使わない。
- ファイル作成・編集はVSCodeで行うか、`Out-File -Encoding utf8` を明示する。
- 既存ファイルの一括置換はVSCodeの Ctrl+H を使う。

## 5. コストを必ず可視化する

PoCの説得力はコストで決まる。画面に必ず出す。

- 1クエリあたりの概算コスト（入力/出力トークンで単価が違う、日本語は係数が乗る点に注意）
- ライセンス型 vs 従量型の比較
- 稼働率による変動の注意喚起

## 6. RAGデモを作る場合の観点

精度を上げる技術はON/OFF切替で「効果が見える」形にする。

- ハイブリッド検索（ベクトル＋キーワード）= 型番・固有名詞に強い
- 親子チャンク = 文脈保持
- HyDE = 仮回答で検索精度向上（API必要）
- メタデータフィルタ = 部署・文書種別で絞り込み
- 「理想データ（整備済み）/ 現実データ（未整備）」を切り替えて、データ品質の影響を見せる

## 7. 判断軸：そもそもRAGが要るか

作る前に必ず確認する。
- 質問に唯一の確定的な答えがあるか？ → Yes なら SQL/構造化で済む。ベクトル化しない。
- 意味的な類似が要るか？ → RAG。
- 全部をベクトル化するのは無駄（正確な検索の精度低下＋コスト増）。

## 8. 環境のつまずき対策（既知）

- 64bit Python必須。Visual C++ランタイムが要る場合がある。
- `sentence-transformers` + PyTorch の初回インストールは数分かかる。
- リポジトリはOneDrive配下を避ける（.gitのロック問題が起きる）。
